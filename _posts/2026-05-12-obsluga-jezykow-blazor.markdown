---
layout: post
title: "Obsługa języków w Blazorze: polski, angielski i niemiecki"
---

Włączenie wielu języków w aplikacji Blazor bardzo rzadko kończy się na dopisaniu jednej listy kultur. Jeśli zrobisz tylko tyle, użytkownik może zobaczyć język w menu, ale raporty dalej zostaną po angielsku, a aplikacja i tak nie wybierze poprawnie języka z przeglądarki.

Dlatego warto patrzeć na lokalizację jak na kilka warstw, a nie jedną opcję w konfiguracji.

## 1. Zacznij od listy języków, które aplikacja ma pokazywać

Najczęściej pierwszym miejscem jest `appsettings.json`.

Przykład:

```json
"DevExpress": {
  "ExpressApp": {
    "Languages": "pl-PL;en-US;de-DE",
    "ShowLanguageSwitcher": true
  }
}
```

To steruje tym, co użytkownik widzi w przełączniku języków.

Jeśli `ShowLanguageSwitcher` jest wyłączone, to nawet dobrze skonfigurowane kultury nie będą łatwo dostępne z UI.

## 2. Oddziel listę języków od logiki ich wyboru

To, że język jest na liście, nie znaczy jeszcze, że aplikacja go sama wybierze.

Za automatyczny wybór odpowiada zwykle `RequestLocalizationOptions`.

Przykład:

```csharp
services.Configure<RequestLocalizationOptions>(options =>
{
    var supportedCultures = new[]
    {
        new CultureInfo("pl-PL"),
        new CultureInfo("en-US"),
        new CultureInfo("de-DE")
    };

    options.DefaultRequestCulture = new RequestCulture("pl-PL");
    options.SupportedCultures = supportedCultures;
    options.SupportedUICultures = supportedCultures;
    options.RequestCultureProviders = new List<IRequestCultureProvider>
    {
        new QueryStringRequestCultureProvider(),
        new CookieRequestCultureProvider(),
        new AcceptLanguageHeaderRequestCultureProvider()
    };
});
```

To jest sensowny układ, bo:

1. użytkownik może nadpisać język query stringiem,
2. potem działa wybór zapisany w cookie,
3. jeśli nie ma wyboru ręcznego, aplikacja bierze język z przeglądarki,
4. fallback pozostaje przewidywalny.

## 3. Fallback powinien być świadomą decyzją

W przykładzie fallback to `pl-PL`. To ma sens, jeśli aplikacja jest przede wszystkim używana po polsku.

Najgorsze, co można zrobić, to zostawić przypadkową kulturę tylko dlatego, że "tak było wcześniej". Fallback to decyzja produktowa, a nie przypadek.

## 4. Dodanie nowego języka to zwykle co najmniej dwa miejsca

Jeśli chcesz dodać np. `fr-FR`, to sama zmiana w `appsettings.json` nie wystarcza.

Trzeba:

1. dopisać język do `Languages`,
2. dopisać kulturę do `SupportedCultures`,
3. dopisać kulturę do `SupportedUICultures`.

Przykład:

```json
"Languages": "pl-PL;en-US;de-DE;fr-FR"
```

i równolegle:

```csharp
var supportedCultures = new[]
{
    new CultureInfo("pl-PL"),
    new CultureInfo("en-US"),
    new CultureInfo("de-DE"),
    new CultureInfo("fr-FR")
};
```

Jeśli zrobisz tylko jeden z tych kroków, lokalizacja będzie częściowa albo myląca.

## 5. Raporty i designer raportów to osobny temat

Tu bardzo często wychodzi różnica między "aplikacja ma języki" a "cały system ma języki".

Jeśli używasz raportów DevExpress, zwykle trzeba dodatkowo przekazać aktywną kulturę do JavaScriptu.

Przykład:

```csharp
propertyEditor.CallbacksModel.CustomizeLocalization = "ReportingLocalization.onCustomizeLocalization";
await jSRuntime.InvokeVoidAsync("ReportingLocalization.setCurrentCulture", cultureInfoService?.CurrentCulture.Name);
```

Podobnie dla viewera:

```csharp
propertyEditor.DocumentViewerCallbacksModel.CustomizeLocalization = "ReportingLocalization.onCustomizeLocalization";
await jSRuntime.InvokeVoidAsync("ReportingLocalization.setCurrentCulture", cultureInfoService?.CurrentCulture.Name);
```

Jeśli tego nie dopilnujesz, główne UI może działać poprawnie, a raporty dalej będą wracały do angielskiego.

## 6. Polski często wymaga dodatkowych plików lokalizacyjnych

W praktyce bardzo często dochodzą pliki typu:

- `dx-analytics-core.pl.json`
- `dx-dashboard.pl.json`
- `dx-reporting.pl.json`
- `dx-rich.pl.json`
- `dx-spreadsheet.pl.json`

Samo ich wrzucenie do katalogu nie wystarcza. Trzeba jeszcze:

1. upewnić się, że są kopiowane do outputu,
2. załadować je w `_Host.cshtml`.

Przykład ładowania:

```html
if (currentCulture == "pl") {
    e.LoadMessages($.get("/js/localization/dx-analytics-core." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-dashboard." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-reporting." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-rich." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-spreadsheet." + currentCulture + ".json"));
}
```

To jest moment, o którym najłatwiej zapomnieć.

## 7. Pliki lokalizacyjne muszą trafić do outputu

Jeśli projekt ma `.csproj`, który jawnie kontroluje content, to trzeba dopisać odpowiednie wpisy.

Przykład:

```xml
<Content Update="wwwroot\js\localization\dx-analytics-core.pl.json">
  <CopyToOutputDirectory>Always</CopyToOutputDirectory>
</Content>
```

Bez tego lokalizacja może działać w repo, ale nie w zbudowanej aplikacji.

## 8. Sensowny workflow dodania języka

Najmniej boleśnie robi się to tak:

1. dodaj kulturę do `appsettings.json`,
2. dodaj kulturę do `Startup.cs`,
3. sprawdź wybór z `Accept-Language`,
4. sprawdź raporty i designer,
5. dodaj pliki `dx-*`, jeśli są potrzebne,
6. upewnij się, że trafiają do outputu,
7. przebuduj aplikację,
8. sprawdź realne UI, nie tylko kompilację.

## 9. Prompt dla agenta AI

Jeżeli chcesz zlecić to agentowi, minimalny prompt może wyglądać tak:

```text
Dodaj lub popraw obsługę języków w aplikacji Blazor.

Zakres:
1. Włącz przełącznik języka.
2. Ustaw listę języków w appsettings.json.
3. Skonfiguruj RequestLocalizationOptions w Startup.cs.
4. Domyślnie wybieraj język z przeglądarki/systemu, ale z fallbackiem na pl-PL.
5. Sprawdź raporty i pliki lokalizacyjne DevExpress.
6. Przebuduj aplikację i podaj listę zmienionych plików.
```

To jest krótki prompt, ale nadal mówi agentowi, żeby nie zatrzymał się na samym `Languages`.

## 10. Najczęstsze błędy

Najczęściej powtarza się:

1. zmiana `Languages` bez zmiany `RequestLocalizationOptions`,
2. brak `AcceptLanguageHeaderRequestCultureProvider`,
3. brak lokalizacji raportów,
4. brak kopiowania plików `dx-*.json`,
5. test tylko na poziomie kompilacji,
6. brak decyzji, jaki ma być fallback.

Jeśli chcesz, żeby aplikacja naprawdę była wielojęzyczna, to trzeba patrzeć na języki tak samo poważnie jak na każdą inną część konfiguracji runtime.
