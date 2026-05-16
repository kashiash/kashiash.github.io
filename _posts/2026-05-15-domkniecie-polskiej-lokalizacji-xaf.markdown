---
layout: post
title: "Domknięcie polskiej lokalizacji w XAF: klasy, enumy i widoki bez mieszanki PL/EN"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 4
---

![Polska lokalizacja: Gumka i ołówek](/assets/images/polish-localization.png)

> **Część 4 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. [Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})
> 4. **Domknięcie polskiej lokalizacji: klasy, enumy i widoki** — ten wpis

Ten wpis pokazuje dokładnie, co dopisałem do `Model.DesignedDiffs.Localization.pl.xafml`, żeby interfejs po polsku nie mieszał polskich i angielskich nazw.

## Zmienione pliki

```text
CS/MainDemo.Module/Model.DesignedDiffs.Localization.pl.xafml
CS/MainDemo.WebAPI.Tests/LocalizationTests.cs
```

## Klasy frameworkowe widoczne w UI

To jest dokładny fragment z repo:

```xml
<Class Name="DevExpress.Persistent.BaseImpl.EF.ReportDataV2" Caption="Raporty">
  <OwnMembers>
    <Member Name="DataTypeCaption" Caption="Typ danych" />
    <Member Name="DisplayName" Caption="Nazwa wyświetlana" />
    <Member Name="IsInplaceReport" Caption="Raport osadzony" />
    <Member Name="IsPredefined" Caption="Tylko do odczytu" />
    <Member Name="ParametersObjectType" Caption="Typ danych parametrow" />
  </OwnMembers>
</Class>
<Class Name="DevExpress.Persistent.BaseImpl.EFCore.AuditTrail.AuditDataItemPersistent" Caption="Historia zmian">
  <OwnMembers>
    <Member Name="AuditedDefaultString" Caption="Obiekt audytowany" />
    <Member Name="AuditOperationType" Caption="Typ operacji" />
    <Member Name="ModifiedOn" Caption="Zmodyfikowano" />
    <Member Name="NewValue" Caption="Nowa wartość" />
    <Member Name="ObjectType" Caption="Typ obiektu" />
    <Member Name="OldValue" Caption="Stara wartość" />
    <Member Name="PropertyName" Caption="Nazwa pola" />
    <Member Name="UserName" Caption="Uzytkownik" />
  </OwnMembers>
</Class>
```

## Brakujące klasy biznesowe

To jest dokładny fragment z repo:

```xml
<Class Name="MainDemo.Module.BusinessObjects.PortfolioFileData" Caption="Portfolio">
  <OwnMembers>
    <Member Name="DocumentType" Caption="Typ dokumentu" />
    <Member Name="File" Caption="Plik" />
  </OwnMembers>
</Class>
<Class Name="MainDemo.Module.BusinessObjects.Position" Caption="Stanowisko">
  <OwnMembers>
    <Member Name="Departments" Caption="Działy" />
    <Member Name="Employees" Caption="Pracownicy" />
    <Member Name="Title" Caption="Nazwa" />
  </OwnMembers>
</Class>
<Class Name="MainDemo.Module.BusinessObjects.Resume" Caption="CV">
  <OwnMembers>
    <Member Name="Employee" Caption="Pracownik" />
    <Member Name="File" Caption="Plik" />
    <Member Name="Portfolio" Caption="Portfolio" />
  </OwnMembers>
</Class>
```

## Enumy i komunikaty

To jest dokładny fragment z repo:

```xml
<LocalizationGroup Name="Enums">
  <LocalizationGroup Name="DevExpress.Persistent.Base.SecurityPermissionPolicy" Value="Polityka uprawnień">
    <LocalizationItem Name="AllowAllByDefault" Value="Domyślnie zezwalaj na wszystko" />
    <LocalizationItem Name="DenyAllByDefault" Value="Domyślnie odmawiaj wszystkiego" />
    <LocalizationItem Name="ReadOnlyAllByDefault" Value="Domyślnie tylko odczyt" />
  </LocalizationGroup>
  <LocalizationGroup Name="DevExpress.Persistent.Base.SecurityPermissionState" Value="Nawigacja">
    <LocalizationItem Name="Allow" Value="Zezwól" />
    <LocalizationItem Name="Deny" Value="Odmów" />
  </LocalizationGroup>
  <LocalizationGroup Name="DevExpress.Persistent.BaseImpl.EFCore.AuditTrail.AuditOperationType">
    <LocalizationItem Name="AddedToCollection" Value="Dodano do kolekcji" />
    <LocalizationItem Name="CustomData" Value="Dane niestandardowe" />
    <LocalizationItem Name="InitialValueAssigned" Value="Przypisano wartość początkową" />
    <LocalizationItem Name="ObjectChanged" Value="Zmieniono obiekt" />
    <LocalizationItem Name="ObjectCreated" Value="Utworzono obiekt" />
    <LocalizationItem Name="ObjectDeleted" Value="Usunięto obiekt" />
    <LocalizationItem Name="RemovedFromCollection" Value="Usunięto z kolekcji" />
  </LocalizationGroup>
  <LocalizationGroup Name="MainDemo.Module.BusinessObjects.DocumentType">
    <LocalizationItem Name="Diagrams" Value="Diagramy" />
    <LocalizationItem Name="Documentation" Value="Dokumentacja" />
    <LocalizationItem Name="Screenshots" Value="Zrzuty ekranu" />
    <LocalizationItem Name="SourceCode" Value="Kod źródłowy" />
    <LocalizationItem Name="Tests" Value="Testy" />
    <LocalizationItem Name="Unknown" Value="Nieznany" />
  </LocalizationGroup>
  <LocalizationGroup Name="MainDemo.Module.BusinessObjects.Priority">
    <LocalizationItem Name="High" Value="Wysoki" />
    <LocalizationItem Name="Low" Value="Niski" />
    <LocalizationItem Name="Normal" Value="Normalny" />
  </LocalizationGroup>
  <LocalizationGroup Name="MainDemo.Module.BusinessObjects.TaskStatus">
    <LocalizationItem Name="NotStarted" Value="Nie rozpoczęto" />
    <LocalizationItem Name="InProgress" Value="W toku" />
    <LocalizationItem Name="WaitingForSomeoneElse" Value="Oczekuje na inną osobę" />
    <LocalizationItem Name="Deferred" Value="Odroczone" />
    <LocalizationItem Name="Completed" Value="Zakończone" />
  </LocalizationGroup>
</LocalizationGroup>
<LocalizationGroup Name="Messages">
  <LocalizationItem Name="CannotUploadFile" Value="Nie można przesłać pliku {0}, gdy trwa przesyłanie innego pliku." />
</LocalizationGroup>
```

## Nawigacja i widoki

To jest dokładny fragment z repo:

```xml
<NavigationItems>
  <Items>
    <Item Id="Default" Caption="Domyślne">
      <Items>
        <Item Id="Employee_ListView" Caption="Pracownicy" />
        <Item Id="ApplicationUser_ListView" Caption="Użytkownicy" />
        <Item Id="DemoTask_ListView" Caption="Zadania" />
        <Item Id="Department_ListView" Caption="Działy" />
        <Item Id="DocumentFileType_ListView" Caption="Typy dokumentów" />
        <Item Id="Event_ListView" Caption="Kalendarz" />
        <Item Id="Note" Caption="Notatka" />
        <Item Id="Paycheck_ListView" Caption="Wypłaty" />
        <Item Id="PermissionPolicyRole_ListView" Caption="Role" />
        <Item Id="Position_ListView" Caption="Stanowiska" />
        <Item Id="Resume_ListView" Caption="CV" />
      </Items>
    </Item>
    <Item Id="Reports" Caption="Raporty">
      <Items>
        <Item Id="ReportsV2" Caption="Raporty" />
      </Items>
    </Item>
  </Items>
</NavigationItems>
<Views>
  <ListView Id="ApplicationUser_ListView" Caption="Użytkownicy" />
  <ListView Id="AuditDataItemPersistent_ListView" Caption="Historia zmian" />
  <DetailView Id="AuthenticationStandardLogonParameters_DetailView_Demo" Caption="Logowanie">
    <Items>
      <StaticText Id="LogonText" Text="Wpisz nazwę użytkownika i hasło, aby kontynuować." />
      <StaticText Id="PasswordHint" Text="Ta aplikacja demonstracyjna nie wymaga hasła do logowania." />
    </Items>
  </DetailView>
```

I końcówka widoków list:

```xml
  <ListView Id="ReportDataV2_ListView" Caption="Raporty" />
  <ListView Id="Resume_ListView" Caption="CV" />
  <ListView Id="Resume_Portfolio_ListView">
    <Columns>
      <ColumnInfo Id="File" Caption="Plik" />
    </Columns>
  </ListView>
</Views>
```

## Test lokalizacji

To jest pełny test z repo:

```csharp
public class LocalizationTests : BaseWebApiTest {
    const string ApiUrl = "/api/Localization/";

    [Fact]
    public async System.Threading.Tasks.Task GetClassCaption() {
        string url = "ClassCaption?classFullName=DevExpress.Persistent.BaseImpl.EF.PermissionPolicy.PermissionPolicyUser";

        string result = await SendRequestAsync("de-DE", url);
        Assert.Equal("Benutzer", result);

        result = await SendRequestAsync("pl-PL", url);
        Assert.Equal("Użytkownik", result);

        result = await SendRequestAsync("en-US", url);
        Assert.Equal("Base User", result);
    }

    [Fact]
    public async System.Threading.Tasks.Task GetAdditionalPolishClassCaptions() {
        var result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Position");
        Assert.Equal("Stanowisko", result);

        result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Resume");
        Assert.Equal("CV", result);

        result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=DevExpress.Persistent.BaseImpl.EF.ReportDataV2");
        Assert.Equal("Raporty", result);
    }
}
```

## Co ta zmiana domyka

Po tej zmianie po polsku są już:

1. klasy biznesowe `Position`, `Resume`, `PortfolioFileData`,
2. typy frameworkowe `ReportDataV2` i `AuditDataItemPersistent`,
3. enumy `DocumentType`, `Priority`, `TaskStatus`,
4. nawigacja, logowanie i listy widoczne w UI.
