---
layout: post
title: "Obsługa skanów i podglądu PDF w XAF Blazor: dokumenty, upload i preview inline"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 6
---

Ten wpis pokazuje, jak dodać dokumenty, upload wielu plików i podgląd PDF do aplikacji XAF Blazor + EF Core.

Cel:

1. właściciel, na przykład `Employee`, ma zakładkę `Załączniki`,
2. użytkownik klika `Dodaj pliki`,
3. przeciąga wiele PDF-ów naraz,
4. każdy plik zapisuje się jako osobny rekord `DocumentFile`,
5. po otwarciu dokumentu PDF jest widoczny inline.

Opisuję wariant wdrożony w `MainDemo.NET.EFCore`.

## Co trzeba dodać

Trzeba dodać cztery grupy elementów:

1. w modelu danych,
2. w `DbContext`,
3. w warstwie XAF i Blazor,
4. w modelu widoków.

Najpierw model danych. Potem baza. Na końcu UI i widoki.

### 1. Klasy danych

- `DocumentFileType`
  To słownik typów dokumentów, na przykład `Faktura`, `Umowa`, `Korespondencja`.

- `DocumentFile`
  To encja dokumentu. Przechowuje plik, typ, opis i datę dodania.

- `IHasDocumentFiles`
  To interfejs dla obiektów, które mają mieć zakładkę `Załączniki`.

- `DocumentFiles` na właścicielu
  To kolekcja dokumentów na klasie takiej jak `Employee` albo `DemoTask`.

- `DocumentFileUploadParameters`
  To obiekt pomocniczy do popupu `Dodaj pliki`.

### 2. Rejestracja w bazie i `DbContext`

- `DbSet<DocumentFile>`
  To tabela dokumentów.

- `DbSet<DocumentFileType>`
  To tabela typów dokumentów.

- relacje `DocumentFile -> Employee` i `DocumentFile -> DemoTask`
  Te relacje wskazują właściciela dokumentu.

### 3. Warstwa XAF i Blazor

- `DocumentFileNestedListViewController`
  Dodaje akcję `Dodaj pliki`, otwiera popup i odświeża listę po uploadzie.

- `DocumentUploadAreaRenderer`
  To komponent z `DxUpload`. Obsługuje przeciągnięcie wielu plików.

- `DocumentFileUploadController`
  To endpoint HTTP, który zapisuje każdy plik jako osobny rekord `DocumentFile`.

- `DocumentPreviewRenderer`
  To komponent podglądu PDF i obrazów.

### 4. Model widoków

- wpis `DocumentFiles` do detail view właściciela
  Dzięki temu użytkownik widzi zakładkę `Załączniki`.

- `DocumentFile_DetailView` z `PreviewFile`
  Dzięki temu po otwarciu dokumentu widać podgląd pliku.

## Krok 1. Słownik typów dokumentów

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

## Krok 2. Encja dokumentu

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

    public virtual Employee Employee { get; set; }
    public virtual DemoTask DemoTask { get; set; }

    [NotMapped]
    [EditorAlias(EditorAliases.DocumentPreviewPropertyEditor)]
    public virtual DocumentFilePreview PreviewFile => new(File);
}
```

W tej aplikacji `DocumentFile` ma dwa pola właściciela:

1. `Employee`
2. `DemoTask`

To wystarcza do osiągnięcia celu.

## Krok 3. Interfejs i kolekcja dokumentów na właścicielu

```csharp
public interface IHasDocumentFiles {
    IList<DocumentFile> DocumentFiles { get; set; }
}
```

Przykład:

```csharp
[Aggregated]
public virtual IList<DocumentFile> DocumentFiles { get; set; } = new ObservableCollection<DocumentFile>();
```

Tak działa to na `Employee` i `DemoTask`.

## Krok 4. `DbContext`

```csharp
public DbSet<DocumentFile> DocumentFiles { get; set; }
public DbSet<DocumentFileType> DocumentFileTypes { get; set; }
```

Relacje:

```csharp
modelBuilder.Entity<DocumentFile>()
    .HasOne(documentFile => documentFile.Employee)
    .WithMany(employee => employee.DocumentFiles)
    .OnDelete(DeleteBehavior.Cascade);

modelBuilder.Entity<DocumentFile>()
    .HasOne(documentFile => documentFile.DemoTask)
    .WithMany(task => task.DocumentFiles)
    .OnDelete(DeleteBehavior.Cascade);
```

## Krok 5. Popup parametrów uploadu

```csharp
[DomainComponent]
public class DocumentFileUploadParameters {
    public virtual DocumentFileType Type { get; set; }
    public virtual string Description { get; set; }
    public virtual DocumentUploadArea UploadArea { get; set; } = new();

    [Browsable(false)]
    public virtual string OwnerObjectType { get; set; }

    [Browsable(false)]
    public virtual Guid OwnerObjectId { get; set; }
}
```

## Krok 6. Kontroler XAF z akcją `Dodaj pliki`

Ta klasa dodaje akcję `Dodaj pliki` i otwiera popup uploadu.

```csharp
public class DocumentFileNestedListViewController : ObjectViewController<ListView, DocumentFile> {
    private readonly PopupWindowShowAction addFilesAction;

    public DocumentFileNestedListViewController() {
        TargetViewNesting = Nesting.Nested;

        addFilesAction = new PopupWindowShowAction(this, "AddDocumentFiles", PredefinedCategory.RecordEdit) {
            Caption = "Dodaj pliki",
            ImageName = "BO_FileAttachment",
            AcceptButtonCaption = "Zamknij"
        };

        addFilesAction.CustomizePopupWindowParams += AddFilesAction_CustomizePopupWindowParams;
        addFilesAction.Execute += AddFilesAction_Execute;
    }

    protected override void OnActivated() {
        base.OnActivated();
        addFilesAction.Active["HasOwner"] = GetOwner() is IHasDocumentFiles;
    }

    private void AddFilesAction_CustomizePopupWindowParams(object sender, CustomizePopupWindowParamsEventArgs e) {
        if(GetOwner() is not BaseObject owner) {
            throw new UserFriendlyException("Brak obiektu nadrzędnego dla załączników.");
        }

        var popupObjectSpace = Application.CreateObjectSpace(typeof(DocumentFileUploadParameters));
        var parameters = popupObjectSpace.CreateObject<DocumentFileUploadParameters>();
        parameters.OwnerObjectType = owner.GetType().Name;
        parameters.OwnerObjectId = owner.ID;
        parameters.Type = popupObjectSpace.FirstOrDefault<DocumentFileType>(item => item.Code == "OTHER");

        e.View = Application.CreateDetailView(popupObjectSpace, "DocumentFileUploadParameters_DetailView", true, parameters);
        e.DialogController.SaveOnAccept = false;
        e.Maximized = true;
    }

    private void AddFilesAction_Execute(object sender, PopupWindowShowActionExecuteEventArgs e) {
        View.ObjectSpace.Refresh();
        View.Refresh();
    }

    private object GetOwner() {
        if(View?.CollectionSource is PropertyCollectionSource propertyCollectionSource) {
            return propertyCollectionSource.MasterObject;
        }
        return null;
    }
}
```

Ten kontroler:

1. dodaje akcję `Dodaj pliki`,
2. otwiera popup,
3. przekazuje do popupu właściciela,
4. po zamknięciu odświeża listę.

## Krok 7. `DxUpload` z przeciąganiem wielu plików

To jest element, który pozwala użytkownikowi wrzucić 20 PDF-ów jednym przeciągnięciem.

```razor
<DxUpload Name="files"
          UploadUrl="@uploadUrl"
          AllowMultiFileUpload="true"
          UploadMode="UploadMode.Instant"
          AllowedFileExtensions="@AllowedExtensions"
          MaxFileSize="100_000_000"
          ExternalDropZoneCssSelector=".upload-drop-zone"
          ExternalSelectButtonCssSelector=".upload-select-button"
          AdditionalParameters="@additionalParams"
          FileUploaded="OnFileUploaded" />
```

Najważniejsze są:

1. `AllowMultiFileUpload="true"`
2. `UploadMode="Instant"`

## Krok 8. Endpoint API zapisujący pliki

```csharp
[ApiController]
[Authorize]
[Route("api/document-files")]
public class DocumentFileUploadController : ControllerBase {
    private readonly INonSecuredObjectSpaceFactory objectSpaceFactory;

    public DocumentFileUploadController(INonSecuredObjectSpaceFactory objectSpaceFactory) {
        this.objectSpaceFactory = objectSpaceFactory;
    }

    [HttpPost("upload")]
    [RequestSizeLimit(100_000_000)]
    public async Task<IActionResult> Upload(
        [FromForm] List<IFormFile> files,
        [FromForm] string ownerObjectType,
        [FromForm] Guid ownerObjectId,
        [FromForm] Guid? typeId,
        [FromForm] string description) {

        using IObjectSpace objectSpace = objectSpaceFactory.CreateNonSecuredObjectSpace(typeof(DocumentFile));
        DocumentFileType documentType = ResolveDocumentType(objectSpace, typeId);

        foreach(var formFile in files.Where(item => item.Length > 0)) {
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

Ten endpoint:

1. odbiera wiele plików,
2. tworzy dla każdego osobny `DocumentFile`,
3. przypina go do właściciela,
4. zapisuje całość do bazy.

## Krok 9. Podgląd PDF

PDF nie wymaga własnego silnika renderującego.

Najprostszy działający wariant:

```razor
@if (Extension == "pdf") {
    <object data="@ContentUrl" type="application/pdf" width="100%" height="800"></object>
}
```

To znaczy:

1. komponent przygotowuje URL,
2. `<object>` osadza PDF,
3. renderowanie wykonuje standardowa przeglądarka PDF w browserze użytkownika.

## Krok 10. Zakładka `Załączniki`

Na detail view właściciela trzeba dodać `DocumentFiles`.

Bez tego:

1. użytkownik nie zobaczy listy dokumentów,
2. nie uruchomi akcji `Dodaj pliki`.

## Krok 11. Detail view dokumentu

`DocumentFile_DetailView` powinien mieć:

1. `File`
2. `Type`
3. `Description`
4. `PreviewFile`

To wystarcza do:

1. zapisania dokumentu,
2. wyświetlenia PDF,
3. pobrania pliku.

## Jak działa cały przepływ

1. użytkownik otwiera `Employee`,
2. przechodzi do `Załączniki`,
3. klika `Dodaj pliki`,
4. otwiera się popup,
5. popup pokazuje `DxUpload`,
6. użytkownik przeciąga 20 PDF-ów,
7. `DxUpload` wysyła je do `/api/document-files/upload`,
8. endpoint tworzy 20 rekordów `DocumentFile`,
9. każdy rekord trafia do właściciela,
10. lista dokumentów odświeża się po zamknięciu popupu,
11. po otwarciu dokumentu PDF jest widoczny inline.

## Jak to zostało dołożone do `Resume` pracownika

W tym repo `Resume` już istniało jako klasa CV pracownika.

Najważniejszy fragment:

```csharp
public class Resume : BaseObject {
    [RuleRequiredField]
    public virtual Employee Employee { get; set; }

    [FileTypeFilter("pdf-only", "PDF file", "*.pdf")]
    public virtual FileData File { get; set; }

    [EditorAlias(EditorAliases.PdfViewerPropertyEditor)]
    public FileData ResumeView => File;
}
```

To dawało:

1. jeden rekord `Resume`,
2. jeden plik PDF,
3. podgląd PDF w detail view.

Brakowało dodawania wielu PDF-ów przez drag and drop na `Employee.Resumes`.

Dodałem to przez:

1. `ResumeUploadParameters`
2. `ResumeNestedListViewController`
3. `ResumeUploadAreaPropertyEditor`
4. `ResumeUploadAreaRenderer`
5. `ResumeUploadController`

Popup trzyma tylko `EmployeeId`.

Kontroler:

1. działa na nested liście `Resume`,
2. dodaje akcję `Dodaj CV`,
3. otwiera popup,
4. odświeża listę po zamknięciu.

Najważniejszy fragment:

```csharp
addResumesAction = new PopupWindowShowAction(this, "AddEmployeeResumes", PredefinedCategory.RecordEdit) {
    Caption = "Dodaj CV",
    ImageName = "BO_Resume",
    AcceptButtonCaption = "Zamknij"
};
```

Renderer używa:

```razor
<DxUpload Name="files"
          UploadUrl="@UploadUrl"
          AllowMultiFileUpload="true"
          UploadMode="UploadMode.Instant"
          AllowedFileExtensions="@AllowedExtensions"
          AdditionalParameters="@AdditionalParameters" />
```

I ustawień:

```csharp
private const string UploadUrl = "/api/resumes/upload";
private static readonly List<string> AllowedExtensions = [".pdf"];
```

Endpoint:

1. przyjmuje listę plików,
2. przyjmuje `employeeId`,
3. odrzuca rozszerzenia inne niż `.pdf`,
4. dla każdego pliku tworzy osobny `Resume`,
5. ustawia `Resume.Employee`,
6. ustawia `Resume.File`.

Efekt w UI:

1. na `Employee_DetailView` jest zakładka `CV`,
2. w zakładce jest lista `Resumes`,
3. użytkownik klika `Dodaj CV`,
4. przeciąga wiele PDF-ów,
5. każdy PDF zapisuje się jako osobny rekord `Resume`,
6. po otwarciu rekordu działa standardowy podgląd PDF z `ResumeView`.

## Komendy

Build:

```powershell
dotnet build CS\MainDemo.NET.EFCore.sln -c Debug
```

Testy:

```powershell
dotnet test CS\MainDemo.WebAPI.Tests\MainDemo.WebAPI.Tests.csproj -c Debug --filter "DocumentFileUploadTests|DynamicAppearanceRuleTests|LocalizationTests"
```

Start aplikacji:

```powershell
dotnet run --no-launch-profile --project CS/MainDemo.Blazor.Server/MainDemo.Blazor.Server.csproj -c Debug --urls http://127.0.0.1:5115
```

## Co sprawdzić ręcznie

1. czy właściciel ma zakładkę `Załączniki`,
2. czy jest przycisk `Dodaj pliki`,
3. czy popup otwiera się poprawnie,
4. czy można przeciągnąć wiele PDF-ów naraz,
5. czy lista się odświeża,
6. czy każdy plik utworzył osobny rekord,
7. czy PDF jest widoczny inline.

Pełny opis repozytoryjny tej zmiany jest tutaj:

[Obsługa skanów i podglądu PDF w MainDemo Blazor](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/obsluga-skanow-i-podgladu-pdf-w-main-demo-blazor.md)

## Instrukcja dla agenta AI

Wdróż pełną obsługę dokumentów w aplikacji XAF Blazor + EF Core zgodnie z tym wpisem.

Zakres:

1. dodaj `DocumentFileType`,
2. dodaj `DocumentFile`,
3. dodaj `IHasDocumentFiles`,
4. dodaj kolekcję `DocumentFiles` na klasach właścicieli,
5. zarejestruj `DbSet` i relacje w `DbContext`,
6. dodaj `DocumentFileUploadParameters`,
7. dodaj `DocumentFileNestedListViewController`,
8. dodaj `DocumentUploadAreaRenderer` z `DxUpload`,
9. dodaj `DocumentFileUploadController`,
10. dodaj `DocumentPreviewRenderer`,
11. dodaj zakładkę `Załączniki` do detail view właściciela,
12. dodaj `PreviewFile` do `DocumentFile_DetailView`,
13. dodaj seed typów dokumentów,
14. dodaj migrację EF Core,
15. dodaj test integracyjny uploadu wielu plików,
16. skompiluj rozwiązanie,
17. uruchom testy,
18. uruchom aplikację i popraw błędy kompilacji, błędy uruchomieniowe oraz brakujące rejestracje.

Zasady:

1. użyj powiązania od właściciela przez `DocumentFiles`,
2. nie dodawaj wielu pól właściciela do `DocumentFile`,
3. dla PDF użyj standardowej przeglądarki PDF w przeglądarce przez `<object>`,
4. nie dodawaj wariantów pobocznych,
5. zostaw jedną działającą ścieżkę od uploadu do podglądu.

Warunek zakończenia:

1. użytkownik może wejść na detail view właściciela,
2. może otworzyć zakładkę `Załączniki`,
3. może kliknąć `Dodaj pliki`,
4. może przeciągnąć wiele PDF-ów naraz,
5. każdy plik zapisuje się jako osobny `DocumentFile`,
6. lista odświeża się po zamknięciu popupu,
7. detail view dokumentu pokazuje PDF inline,
8. build przechodzi,
9. testy przechodzą,
10. rozwiązanie uruchamia się bez błędów.
