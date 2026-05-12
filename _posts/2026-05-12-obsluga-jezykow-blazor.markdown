---
layout: post
title: "Obsługa języków w Blazorze: polski, angielski i niemiecki"
series: "Dostosowanie demówki XAF Blazor do własnych potrzeb"
series_part: 1
---

> **Część 1 serii: Dostosowanie demówki XAF Blazor do własnych potrzeb**
>
> Bierzemy publiczne `MainDemo.NET.EFCore` od DevExpressa i przerabiamy je krok po kroku tak, żeby wyglądało i działało jak nasza własna aplikacja, nie demówka.
>
> 1. **Obsługa języków: polski, angielski, niemiecki** — ten wpis
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. [Custom DateEditor z parametrem modelowym do blokady kółka myszy]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

Wielojęzyczność w Blazorze ma tę samą przypadłość co branding: wygląda niewinnie, dopóki nie zaczniesz tego robić naprawdę. Na początku człowiek dopisuje dwa kody kultur, włącza przełącznik języka i myśli, że temat zamknięty. A potem okazuje się, że menu przełącza się ładnie, ale raporty dalej są po angielsku, część UI wraca do fallbacku, a nowy użytkownik i tak dostaje zły język na wejściu.

To nie jest wielka tragedia. To po prostu oznacza, że języki trzeba potraktować jako konfigurację runtime, a nie kosmetykę.

## Konkret z ostatniego wdrożenia, nie teoria

Właśnie zrobiłem taką zmianę w publicznym repo:

- [kashiash/MainDemoEFCoreCustomization](https://github.com/kashiash/MainDemoEFCoreCustomization)

I tam dobrze widać jedną rzecz, której w ładnych, czystych tutorialach zwykle nie ma: czasem sam język to połowa roboty, a druga połowa to ratowanie projektu przed zależnościami, które do tej pory działały tylko dlatego, że lokalnie dziedziczyły ustawienia z katalogu nadrzędnego.

W tym repo dodałem:

- `pl-PL` do `appsettings.json`,
- `RequestLocalizationOptions` w `Startup.cs`,
- polskie pliki `dx-analytics-core.pl-PL.json`, `dx-reporting.pl-PL.json` i `pl-PL.json`,
- `Model.DesignedDiffs.Localization.pl.xafml`,
- testy dla polskiej lokalizacji,
- osobny dokument krok po kroku w repo:
  [`docs/obsluga-jezyka-polskiego-w-main-demo-blazor.md`](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/docs/obsluga-jezyka-polskiego-w-main-demo-blazor.md)

I teraz najciekawsze: nie zostawiłem fallbacku na `pl-PL`, mimo że w wielu projektach to ma sens. Tutaj zostawiłem `en-US`, bo inaczej raporty CSV zaczęły zmieniać separator i format daty. Czyli dokładnie ten przypadek, o który zwykle nikt nie pyta na początku, a który potem rozwala testy i „nagle” zmienia zachowanie systemu.

To jest dobry przykład, że artykuł daje kierunek, ale gotową zmianę i tak trzeba dopasować do konkretnego projektu.

## Sama lista języków niczego jeszcze nie załatwia

Na ogół zaczyna się od `appsettings.json`.

Na przykład tak:

```json
"DevExpress": {
  "ExpressApp": {
    "Languages": "pl-PL;en-US;de-DE",
    "ShowLanguageSwitcher": true
  }
}
```

To jest potrzebne. Ale tylko potrzebne.

Ta sekcja mówi aplikacji, jakie języki ma pokazać w UI. Nie mówi jeszcze, jak wybrać domyślny język użytkownika. Nie mówi też nic o raportach.

Czyli: dobry początek, ale tylko początek.

## Prawdziwa robota zaczyna się w `RequestLocalizationOptions`

To jest miejsce, gdzie wychodzi, czy aplikacja faktycznie „rozumie” języki użytkownika, czy tylko je wyświetla.

Typowy układ:

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

I tu już widać całą logikę:

- query string może nadpisać kulturę,
- cookie pamięta wybór użytkownika,
- `Accept-Language` bierze język z przeglądarki,
- `pl-PL` zostaje jako fallback.

To jest moim zdaniem sensowny kompromis. Użytkownik nie musi klikać niczego ręcznie przy pierwszym wejściu, ale też nie tracisz kontroli nad domyślnym zachowaniem.

## Fallback nie może być przypadkowy

W wielu projektach fallback zostaje taki, jaki akurat ktoś kiedyś wpisał.

To jest zły pomysł.

Jeśli aplikacja jest głównie po polsku, `pl-PL` jako fallback ma sens. Jeśli robisz produkt pod rynek międzynarodowy, może mieć sens coś innego. Najgorsze są ustawienia „bo już były”.

Takie rzeczy wychodzą dopiero później, kiedy nagle nowy użytkownik z niemieckim systemem dostaje polski, a zespół się zastanawia, czy to bug, czy feature.

## Dodanie nowego języka prawie nigdy nie kończy się na jednym pliku

Załóżmy, że chcesz dodać `fr-FR`.

Jeśli dopiszesz tylko:

```json
"Languages": "pl-PL;en-US;de-DE;fr-FR"
```

to zrobiłeś tylko pół roboty.

Trzeba jeszcze dopisać kulturę w `Startup.cs`:

```csharp
var supportedCultures = new[]
{
    new CultureInfo("pl-PL"),
    new CultureInfo("en-US"),
    new CultureInfo("de-DE"),
    new CultureInfo("fr-FR")
};
```

I dopiero wtedy zaczyna to być spójne.

Inaczej użytkownik zobaczy język na liście, ale aplikacja nie będzie go poprawnie traktowała jako wspieranego języka runtime.

## Raporty potrafią udawać, że problemu nie ma

Tu bywa najwięcej pułapek.

Główne UI może przełączać się poprawnie, a report viewer czy designer i tak zostaną po angielsku. I człowiek ma wtedy takie złudne poczucie, że „w sumie działa prawie wszystko”.

To „prawie” jest właśnie najdroższe.

Jeżeli używasz DevExpress, to zwykle trzeba przekazać kulturę do JavaScriptu. Na przykład tak:

```csharp
propertyEditor.CallbacksModel.CustomizeLocalization = "ReportingLocalization.onCustomizeLocalization";
await jSRuntime.InvokeVoidAsync("ReportingLocalization.setCurrentCulture", cultureInfoService?.CurrentCulture.Name);
```

albo tak:

```csharp
propertyEditor.DocumentViewerCallbacksModel.CustomizeLocalization = "ReportingLocalization.onCustomizeLocalization";
await jSRuntime.InvokeVoidAsync("ReportingLocalization.setCurrentCulture", cultureInfoService?.CurrentCulture.Name);
```

I właśnie to jest ten moment, o którym łatwo zapomnieć, jeśli człowiek patrzy tylko na główny shell aplikacji.

## Polski zwykle potrzebuje jeszcze jednego kroku

W projektach z DevExpress polski bardzo często nie kończy się na samej kulturze `pl-PL`.

Dochodzą pliki lokalizacyjne, na przykład:

- `dx-analytics-core.pl.json`
- `dx-dashboard.pl.json`
- `dx-reporting.pl.json`
- `dx-rich.pl.json`
- `dx-spreadsheet.pl.json`

Pierwsze miejsce, które warto wtedy otworzyć, to:

- [localization.devexpress.com](https://localization.devexpress.com/)

To jest oficjalny serwis DevExpress z tłumaczeniami. Czasem człowiek odruchowo zaczyna szukać tych plików po starych projektach albo paczkach NuGet, a tu po prostu szybciej jest najpierw sprawdzić, czy gotowa lokalizacja już tam leży.

Drugie miejsce, które naprawdę warto mieć otwarte obok, to główna dokumentacja XAF:

- [Localization | XAF Documentation](https://docs.devexpress.com/eXpressAppFramework/113298/localization)

I to nie jest pusty link „na wszelki wypadek”. DevExpress zbiera tam w jednym miejscu najważniejsze tematy związane z lokalizacją: podstawy, lokalizację standardowych modułów i kontrolek, culture-specific formatting, runtime language switcher oraz osobne instrukcje typu „localize an XAF application”. Jak ktoś robi XAF pierwszy albo drugi raz, to taka strona oszczędza sporo błądzenia między przypadkowymi tematami.

Jest jeszcze trzeci, nowy kierunek: DevExpress MCP Server.

- [Transform Your Development Experience with the DevExpress MCP Server](https://community.devexpress.com/Blogs/news/archive/2025/10/16/transform-your-development-experience-with-the-devexpress-mcp-server.aspx)
- `https://api.devexpress.com/mcp/docs`
- `https://api.devexpress.com/mcp/docs?v=24.2`

To przydaje się wtedy, kiedy nie chcesz tylko czytać dokumentacji ręcznie, ale chcesz dać agentowi AI bezpośredni dostęp do aktualnych materiałów DevExpress. W praktyce to jest bardzo sensowne przy pytaniach o XAF, raporty, dashboardy albo Blazor UI, bo agent może szukać po oficjalnej bazie dokumentacji zamiast zgadywać albo opierać się na starych przykładach.

I ważna rzecz praktyczna: samo znalezienie tych plików jeszcze nic nie daje. Trzeba je normalnie dograć do projektu. W moim przypadku był to katalog w stylu:

- `DevExpressLocalizedResources_2025.2_pl\json resources\`

czyli miejsce, z którego bierzesz pliki typu `dx-analytics-core.pl.json`, `dx-reporting.pl.json`, `dx-dashboard.pl.json` i kopiujesz je do `wwwroot/js/localization/`.

I teraz najważniejsze: samo wrzucenie ich do katalogu niczego nie gwarantuje.

Trzeba jeszcze je załadować, np.:

```html
if (currentCulture == "pl") {
    e.LoadMessages($.get("/js/localization/dx-analytics-core." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-dashboard." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-reporting." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-rich." + currentCulture + ".json"));
    e.LoadMessages($.get("/js/localization/dx-spreadsheet." + currentCulture + ".json"));
}
```

Jak tego nie zrobisz, to polski będzie „tak trochę”.

## A potem jeszcze `.csproj`

Tak, jeszcze to.

Jeśli projekt jawnie kontroluje content, to pliki trzeba skopiować do outputu.

Na przykład:

```xml
<Content Update="wwwroot\js\localization\dx-analytics-core.pl.json">
  <CopyToOutputDirectory>Always</CopyToOutputDirectory>
</Content>
```

Ten etap jest nudny, ale bez niego można stracić godzinę na patrzenie, czemu lokalnie „w repo jest”, a w uruchomionej aplikacji „jakby nie było”.

## Jak bym to robił bez marnowania czasu

Moja kolejność:

1. ustal listę języków,
2. włącz przełącznik,
3. popraw `RequestLocalizationOptions`,
4. zostaw sensowny fallback,
5. sprawdź raporty,
6. dopiero potem baw się dodatkowymi plikami lokalizacji,
7. zrób prawdziwe sprawdzenie w przeglądarce.

Nie tylko build. Nie tylko „kompiluje się”. Normalnie wejść do aplikacji, zmienić język, odświeżyć stronę, wejść w raport, zobaczyć co zostało po staremu.

## Prompt dla agenta AI

Jeżeli chcesz to zlecić agentowi, dałbym mu coś w tym stylu:

```text
Dodaj lub popraw obsługę języków w aplikacji Blazor.

Zrób to end-to-end:
1. Włącz przełącznik języka.
2. Ustaw listę języków w appsettings.json.
3. Skonfiguruj RequestLocalizationOptions w Startup.cs.
4. Domyślnie wybieraj język z przeglądarki/systemu, ale zostaw fallback na pl-PL.
5. Sprawdź raporty i pliki lokalizacyjne DevExpress.
6. Przebuduj aplikację i wypisz zmienione pliki.

Sprawdź dokładnie:
- appsettings.json
- Startup.cs
- _Host.cshtml
- ReportLocalizationController.cs
- .csproj
- wwwroot/js/localization/
```

Nie jest to piękny prompt z konferencji o AI. Ale jest użyteczny. I to mnie bardziej interesuje.

## Najczęstsze wpadki

Najczęściej widzę:

- zmianę `Languages` bez ruszania `RequestLocalizationOptions`,
- brak `AcceptLanguageHeaderRequestCultureProvider`,
- pominięcie raportów,
- brak kopiowania plików `dx-*.json`,
- test tylko na poziomie builda,
- fallback ustawiony z przypadku.

To nie są wielkie błędy architektoniczne. To są raczej drobne zaniedbania, które razem robią bardzo irytujący efekt końcowy.

I właśnie dlatego warto mieć to spisane. Nie po to, żeby napisać „pełny przewodnik po lokalizacji”, tylko po to, żeby drugi raz nie wpaść w ten sam dołek.
