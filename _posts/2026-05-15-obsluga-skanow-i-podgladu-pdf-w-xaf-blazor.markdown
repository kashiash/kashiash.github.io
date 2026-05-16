---
layout: post
title: "Obsługa skanów i podglądu PDF w XAF Blazor: dokumenty, upload i preview inline"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 6
---

W aplikacji referencyjnej XAF bardzo szybko dochodzi się do ściany: pojedynczy `FileData` gdzieś w encji albo prosty załącznik w jednym module nie wystarcza, gdy trzeba obsłużyć prawdziwe dokumenty. Pojawia się potrzeba słownika typów dokumentów, wielu plików przypinanych do różnych obiektów, drag-drop uploadu i podglądu PDF bez pobierania pliku na dysk.

Taki właśnie wzorzec dołożyłem do `MainDemo.NET.EFCore`. Nie jako nowy subsystem z osobną magią, tylko jako czytelny zestaw elementów XAF Blazor:

1. encja `DocumentFileType` jako słownik typów dokumentów,
2. encja `DocumentFile` jako sam dokument,
3. interfejs `IHasDocumentFiles`, żeby jeden kontroler obsługiwał wiele typów,
4. popup z `DxUpload` i multi-file uploadem,
5. endpoint API zapisujący `FileData`,
6. custom preview dla PDF i obrazów inline w Blazorze.

Żeby dało się to wdrożyć także w innym projekcie, sam opis wzorca nie wystarcza. Potrzebne są jeszcze minimalne klasy i fragmenty kodu, które można skopiować jako punkt startowy.

Najpierw słownik typów dokumentów:

```csharp
[DefaultClassOptions]
[ImageName("BO_Category")]
[XafDefaultProperty(nameof(Name))]
public class DocumentFileType : BaseObject {
    [RuleRequiredField]
    [RuleUniqueValue]
    [MaxLength(20)]
    public virtual string Code { get; set; }

    [RuleRequiredField]
    [MaxLength(100)]
    public virtual string Name { get; set; }

    [MaxLength(255)]
    public virtual string Description { get; set; }

    public virtual bool IsActive { get; set; } = true;
}
```

Potem sama encja dokumentu:

```csharp
[ImageName("BO_FileAttachment")]
[XafDefaultProperty(nameof(DisplayName))]
public class DocumentFile : BaseObject {
    [RuleRequiredField]
    [EditorAlias(DevExpress.ExpressApp.Editors.EditorAliases.FileDataPropertyEditor)]
    public virtual FileData File { get; set; }

    public virtual DocumentFileType Type { get; set; }
    public virtual string Description { get; set; }
    public virtual DateTime UploadedAtUtc { get; set; }

    [NotMapped]
    [EditorAlias(EditorAliases.DocumentPreviewPropertyEditor)]
    public virtual DocumentFilePreview PreviewFile => new(File);
}
```

Sam dokument nie musi jeszcze mówić, kto jest jego właścicielem. Tu są dwa warianty.

Wariant A, użyty w tym repo, prowadzi powiązanie od właściciela:

```csharp
public interface IHasDocumentFiles {
    IList<DocumentFile> DocumentFiles { get; set; }
}

public class Employee : BaseObject, IHasDocumentFiles {
    [Aggregated]
    public virtual IList<DocumentFile> DocumentFiles { get; set; } = new ObservableCollection<DocumentFile>();
}
```

To jest dobre rozwiązanie, gdy właścicieli jest mało.

Wariant B, lepszy przy dużej liczbie właścicieli, używa osobnej klasy powiązania:

```csharp
public class DocumentBinding : BaseObject {
    public virtual DocumentFile Document { get; set; }

    [MaxLength(500)]
    public virtual string OwnerType { get; set; }

    public virtual Guid OwnerId { get; set; }
}
```

W `DbContext` potrzebujesz co najmniej:

```csharp
public DbSet<DocumentFile> DocumentFiles { get; set; }
public DbSet<DocumentFileType> DocumentFileTypes { get; set; }
```

oraz relacji do właścicieli:

```csharp
modelBuilder.Entity<DocumentFile>()
    .HasOne(file => file.Employee)
    .WithMany(employee => employee.DocumentFiles);

modelBuilder.Entity<DocumentFile>()
    .HasOne(file => file.DemoTask)
    .WithMany(task => task.DocumentFiles);
```

W tej iteracji właścicielami dokumentów są `Employee` i `DemoTask`, więc użyłem wariantu A, czyli powiązania od właściciela. To wystarczy, żeby wzorzec był realny, a jednocześnie nie rozlewa zmian po całej demówce. Użytkownik wchodzi w zakładkę `Załączniki`, klika `Dodaj pliki`, wybiera typ dokumentu i od razu przeciąga kilka plików do strefy uploadu. Każdy plik zapisuje się jako osobny rekord `DocumentFile`, a po zamknięciu popupu lista się odświeża.

Najważniejsza decyzja techniczna była taka, żeby **nie podmieniać globalnie standardowego edytora `FileData`**. Zamiast tego podgląd siedzi na osobnej właściwości `PreviewFile`, a Blazor-only property editor renderuje:

- `<object>` dla PDF,
- `<img>` dla obrazów,
- czytelny komunikat z przyciskiem pobrania dla pozostałych rozszerzeń.

To pozwala zachować stabilność po stronie WinForms i nie wprowadza zależności platformowych do wspólnego modułu. `DOCX` i `XLSX` są już akceptowane na uploadzie, ale w tym kroku kończą się pobraniem pliku. Konwersję do PDF warto robić dopiero wtedy, gdy naprawdę jest potrzebna i wiadomo, gdzie ten koszt ma siedzieć.

Sam renderer podglądu może być prosty. Najważniejszy fragment wygląda tak:

```razor
@if (Extension == "pdf") {
    <object data="@ContentUrl" type="application/pdf" width="100%" height="800"></object>
}
else if (Extension is "jpg" or "jpeg" or "png" or "gif") {
    <img src="@ContentUrl" style="max-width:100%; max-height:800px;" alt="@FileName" />
}
else {
    <div class="alert alert-info">
        Podgląd inline jest dostępny dla PDF i obrazów. Ten plik można pobrać.
    </div>
}
```

Z kolei endpoint uploadu w najkrótszej potrzebnej wersji wygląda tak:

```csharp
[ApiController]
[Authorize]
[Route("api/document-files")]
public class DocumentFileUploadController : ControllerBase {
    [HttpPost("upload")]
    public async Task<IActionResult> Upload(
        [FromForm] List<IFormFile> files,
        [FromForm] string ownerObjectType,
        [FromForm] Guid ownerObjectId,
        [FromForm] Guid? typeId,
        [FromForm] string description) {

        using IObjectSpace objectSpace = objectSpaceFactory.CreateNonSecuredObjectSpace(typeof(DocumentFile));
        DocumentFileType documentType = ResolveDocumentType(objectSpace, typeId);

        foreach (var formFile in files.Where(item => item.Length > 0)) {
            var documentFile = objectSpace.CreateObject<DocumentFile>();
            var fileData = objectSpace.CreateObject<FileData>();

            await using var stream = formFile.OpenReadStream();
            fileData.LoadFromStream(formFile.FileName, stream);

            documentFile.File = fileData;
            documentFile.Type = documentType;
            documentFile.Description = description;
            AddToOwnerDocuments(objectSpace, documentFile, ownerObjectType, ownerObjectId);
        }

        objectSpace.CommitChanges();
        return Ok();
    }
}
```

Najważniejsza rzecz jest prosta: każdy przesłany plik staje się osobnym rekordem `DocumentFile`, a aplikacja przypina go do właściciela przez jego kolekcję dokumentów.

Przy wdrożeniu wyszły też trzy drobne, ale typowe problemy:

- konflikt nazw `EditorAliases` między własnym modułem a DevExpressem,
- zły typ event args w `DxUpload`,
- odwołanie do właściciela nested listy przez niewłaściwe API (`Owner` zamiast `PropertyCollectionSource.MasterObject`).

To są właśnie rzeczy, które odróżniają działający wzorzec od ładnego snippetu. Kod został doprowadzony do zielonego `dotnet build`, a testy integracyjne przechodzą przez prawdziwy endpoint `multipart/form-data`, więc mechanizm jest sprawdzony end-to-end.

Pełny opis wdrożenia w tym repo, z listą plików i konkretnymi poprawkami kompilacji, jest tutaj:

[Obsługa skanów i podglądu PDF w MainDemo Blazor](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/obsluga-skanow-i-podgladu-pdf-w-main-demo-blazor.md)
