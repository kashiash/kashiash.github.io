---
layout: post
title: "Obsługa skanów i podglądu PDF w XAF Blazor: dokumenty, upload i preview inline"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 6
---

Ten wpis pokazuje najprostszą kompletną ścieżkę dodania dokumentów do aplikacji XAF Blazor + EF Core.

Cel:

1. właściciel, na przykład `Employee`, ma zakładkę `Załączniki`,
2. użytkownik klika `Dodaj pliki`,
3. przeciąga wiele PDF-ów naraz,
4. każdy plik zapisuje się jako osobny rekord `DocumentFile`,
5. po otwarciu dokumentu PDF jest widoczny inline.

To jest dokładnie wariant wdrożony w `MainDemo.NET.EFCore`.

## Co trzeba dodać

1. `DocumentFileType` jako słownik typów dokumentów,
2. `DocumentFile` jako encję dokumentu,
3. `IHasDocumentFiles` jako interfejs właściciela,
4. `DocumentFiles` jako kolekcję na właścicielu,
5. `DbSet` i relacje w `DbContext`,
6. `DocumentFileUploadParameters` do popupu,
7. `DocumentFileNestedListViewController` z akcją `Dodaj pliki`,
8. `DocumentUploadAreaRenderer` z `DxUpload`,
9. `DocumentFileUploadController` jako endpoint API,
10. `DocumentPreviewRenderer` do podglądu PDF,
11. wpis `DocumentFiles` do detail view właściciela,
12. `DocumentFile_DetailView` z `PreviewFile`.

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

To jest klasa, która uruchamia cały proces.

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
