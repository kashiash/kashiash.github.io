---
layout: post
title: "Obsługa języków w Blazorze: polski, angielski i niemiecki"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 1
---

![Języki w Blazorze: Wieża Babel](/assets/images/languages-blazor.png)

> **Część 1 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> 1. **Obsługa języków: polski, angielski, niemiecki** — ten wpis
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. [Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

Ten wpis pokazuje dokładnie, co zmieniłem w repo `MainDemo.NET.EFCore`, żeby dodać `pl-PL`.

## Zakres zmiany

Zmiana objęła:

1. listę języków w `appsettings.json`,
2. wybór kultury w `Startup.cs`,
3. ładowanie plików lokalizacyjnych DevExpress w `scripts.js`,
4. osadzenie `Model.DesignedDiffs.Localization.pl.xafml`,
5. testy HTTP dla lokalizacji,
6. ustabilizowanie testów raportów po dodaniu obsługi kultur.

## `appsettings.json`

To jest dokładny fragment z repo:

```json
"DevExpress": {
  "ExpressApp": {
    "Languages": "pl-PL;en-US;de-DE",
    "ShowLanguageSwitcher": true,
    "Security": {
      "UrlSigningKey": "669BC10469B34252A2EF1BA1BAFEDEAF"
    },
    "ThemeSwitcher": {
      "DefaultItemName": "Office White",
      "ShowSizeModeSwitcher": true
    }
  }
}
```

Najważniejsza zmiana to:

```json
"Languages": "pl-PL;en-US;de-DE"
```

W tym repo fallback został na `en-US`. Nie zmieniałem go na `pl-PL`, bo testy raportów CSV zakładają angielski separator i format daty.

## `Startup.cs`

To jest dokładna konfiguracja z repo:

```csharp
using System.Globalization;
using Microsoft.AspNetCore.Localization;

// ...

services.Configure<RequestLocalizationOptions>(options => {
    var supportedCultures = new[] {
        new CultureInfo("pl-PL"),
        new CultureInfo("en-US"),
        new CultureInfo("de-DE")
    };

    options.DefaultRequestCulture = new RequestCulture("en-US");
    options.SupportedCultures = supportedCultures;
    options.SupportedUICultures = supportedCultures;
    options.RequestCultureProviders = new List<IRequestCultureProvider> {
        new QueryStringRequestCultureProvider(),
        new CookieRequestCultureProvider(),
        new AcceptLanguageHeaderRequestCultureProvider()
    };
});
```

To ustawienie:

1. rejestruje `pl-PL`,
2. bierze kulturę z query stringa, cookie i `Accept-Language`,
3. zostawia `en-US` jako domyślne zachowanie.

## `scripts.js`

Tu siedzi dokładna obsługa lokalizacji reportingu i widgetów DevExpress:

```javascript
window.ReportingLocalization = {
    currentCulture: null,
    loadMergedMessages: function (baseUrl, overrideUrl) {
        return $.get(baseUrl).then(baseMessages => {
            return $.get(overrideUrl)
                .then(overrideMessages => $.extend(true, {}, baseMessages, overrideMessages))
                .catch(() => baseMessages);
        });
    },
    resolveLocalizationCulture: function (culture) {
        if (!culture) {
            return null;
        }

        const normalizedCulture = culture.toLowerCase();
        if (normalizedCulture.startsWith("de")) {
            return "de-DE";
        }
        if (normalizedCulture.startsWith("pl")) {
            return "pl-PL";
        }

        return null;
    },
    setCurrentCulture: function (culture) {
        window.ReportingLocalization.currentCulture = culture;
    },
    onCustomizeLocalization: function (_, e) {
        const currentCulture = window.ReportingLocalization.resolveLocalizationCulture(window.ReportingLocalization.currentCulture);
        if (currentCulture) {
            const analyticsMessages = window.ReportingLocalization.loadMergedMessages(
                "js/localization/dx-analytics-core." + currentCulture + ".json",
                "js/localization/overrides/dx-analytics-core." + currentCulture + ".json"
            );
            const reportingMessages = window.ReportingLocalization.loadMergedMessages(
                "js/localization/dx-reporting." + currentCulture + ".json",
                "js/localization/overrides/dx-reporting." + currentCulture + ".json"
            );
            const widgetMessages = window.ReportingLocalization.loadMergedMessages(
                "js/localization/" + currentCulture + ".json",
                "js/localization/overrides/" + currentCulture + ".json"
            );

            e.LoadMessages(analyticsMessages);
            e.LoadMessages(reportingMessages);
            widgetMessages.done(result => {
                e.WidgetLocalization.loadMessages(result);
            }).always(() => {
                e.WidgetLocalization.locale(currentCulture);
            });
        }
    }
};
```

## `MainDemo.Module.csproj`

Polski model lokalizacji został osadzony jako zasób:

```xml
<EmbeddedResource Include="Model.DesignedDiffs.Localization.de.xafml">
  <DependentUpon>Model.DesignedDiffs.xafml</DependentUpon>
</EmbeddedResource>
<EmbeddedResource Include="Model.DesignedDiffs.Localization.pl.xafml">
  <DependentUpon>Model.DesignedDiffs.xafml</DependentUpon>
</EmbeddedResource>
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

    [Fact]
    public async System.Threading.Tasks.Task GetMemberCaption() {
        string url = "MemberCaption?classFullName=MainDemo.Module.BusinessObjects.Employee&memberName=Birthday";

        string result = await SendRequestAsync("de-DE", url);
        Assert.Equal("Geburtstag", result);

        result = await SendRequestAsync("pl-PL", url);
        Assert.Equal("Data urodzenia", result);

        result = await SendRequestAsync("en-US", url);
        Assert.Equal("Birth Date", result);
    }

    [Fact]
    public async System.Threading.Tasks.Task GetActionCaption() {
        string url = "ActionCaption?actionName=SetTaskAction";

        string result = await SendRequestAsync("de-DE", url);
        Assert.Equal("Setze für Aufgabe...", result);

        result = await SendRequestAsync("pl-PL", url);
        Assert.Equal("Ustaw zadanie...", result);

        result = await SendRequestAsync("en-US", url);
        Assert.Equal("Set Task", result);
    }
}
```

To jest realny test HTTP pod:

```text
/api/Localization/
```

## Test raportów

Po dodaniu kultur trzeba było ustabilizować testy raportów:

```csharp
using System.Globalization;

string currentData = DateTime.Now.ToString("d", CultureInfo.GetCultureInfo("en-US"));

private async System.Threading.Tasks.Task LoadReportAndCompare(string userName, string url, string expectedResult) {
    var request = new HttpRequestMessage(HttpMethod.Get, url);
    request.Headers.Add("Accept-Language", "en-US");
    var response = await WebApiClient.SendAsync(request);
    Assert.True(response.IsSuccessStatusCode, $"Request failed for {userName} @ {url} ");

    string loadedReport = await response.Content.ReadAsStringAsync();
    Assert.Equal(expectedResult, loadedReport);
}
```

## Pliki z tłumaczeniami JavaScript

Do repo doszły:

```text
CS/MainDemo.Blazor.Server/wwwroot/js/localization/pl-PL.json
CS/MainDemo.Blazor.Server/wwwroot/js/localization/dx-analytics-core.pl-PL.json
CS/MainDemo.Blazor.Server/wwwroot/js/localization/dx-reporting.pl-PL.json
```

## Wynik

Po tej zmianie aplikacja:

1. pokazuje `pl-PL` na liście języków,
2. wybiera polski z `Accept-Language`,
3. ładuje polskie komunikaty DevExpress dla reportingu,
4. ma polskie captiony w modelu XAF,
5. przechodzi testy HTTP dla lokalizacji.
