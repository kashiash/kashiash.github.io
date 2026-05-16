---
layout: post
title: "Domknięcie polskiej lokalizacji w XAF: klasy, enumy i widoki bez mieszanki PL/EN"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 4
---

![Polska lokalizacja: Gumka i ołówek](/assets/images/polish-localization.png)

> **Część 4 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> Nie tworzymy aplikacji od zera — postawienie projektu XAF Blazor + EF Core jest krok po kroku opisane w [oficjalnej dokumentacji DevExpress](https://docs.devexpress.com/eXpressAppFramework/) i to jest miejsce, w którym każdy może (i powinien) zacząć. My ciągniemy ten temat dalej: bierzemy publiczny projekt referencyjny `MainDemo.NET.EFCore` i pokazujemy, co dochodzi w nim po stronie realnego wdrożenia.
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. [Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})
> 4. **Domknięcie polskiej lokalizacji: klasy, enumy i widoki** — ten wpis

Samo dodanie `pl-PL` do aplikacji nie zamyka lokalizacji. To dopiero pierwszy etap. Problem wychodzi zwykle wtedy, gdy użytkownik zaczyna normalnie pracować w systemie i okazuje się, że menu jest po polsku, ale nazwa raportu, widok stanowisk albo część słowników dalej wraca do angielskiego.

To nie jest błąd Blazora. To zwykle oznacza niedomknięty model XAF.

## Gdzie najczęściej zostaje angielski

Po pierwszym wdrożeniu języka polskiego zwykle przykrywasz:

- przełącznik języka,
- `RequestLocalizationOptions`,
- pliki lokalizacyjne DevExpress dla JavaScriptu,
- podstawowe tłumaczenia w modelu.

I to działa. Tylko że zwykle nie obejmuje wszystkiego.

Najczęstsze resztki:

- klasy biznesowe dodane później niż pierwszy plik lokalizacji,
- typy frameworkowe XAF widoczne w UI, np. raporty, audyt albo kalendarz,
- wartości enumów,
- nazwy list, nawigacji i teksty logowania.

W efekcie część interfejsu jest po polsku, a część pozostaje po angielsku. W aplikacji biznesowej taki stan jest po prostu niespójny.

## Zakres zmian

W repo:

- [kashiash/MainDemoEFCoreCustomization](https://github.com/kashiash/MainDemoEFCoreCustomization)

dopisałem kolejną warstwę polskiej lokalizacji do pliku:

- `CS/MainDemo.Module/Model.DesignedDiffs.Localization.pl.xafml`

Nie zmieniałem mechanizmu wyboru języka, bo ten już działał. Uzupełniłem natomiast to, co użytkownik faktycznie widzi na ekranie:

- `Position` -> `Stanowisko`,
- `Resume` -> `CV`,
- `ReportDataV2` -> `Raporty`,
- `AuditDataItemPersistent` -> `Historia zmian`,
- polskie wartości `Priority`, `TaskStatus` i `DocumentType`,
- polskie nazwy pozycji w nawigacji i widokach list.

Do tego dorzuciłem test regresyjny, który pyta Web API o nazwy wyświetlane dla tych typów w `pl-PL`, żeby przy kolejnej przeróbce modelu nie wrócić przypadkiem do angielskiego.

## Dlaczego sama klasa biznesowa nie wystarcza

W XAF termin `Business Object` jest nazwą własną używaną przez framework dla klasy biznesowej widocznej w modelu i UI. Sama taka klasa nie zamyka jednak całej lokalizacji. W praktyce użytkownik widzi miks:

- własnych obiektów biznesowych,
- typów DevExpressa,
- wpisów z modelu aplikacji,
- tekstów wygenerowanych przez moduły raportów, audytu i bezpieczeństwa.

Jeśli przetłumaczysz tylko `Employee`, `Department` i `DemoTask`, a zostawisz po angielsku `ReportDataV2`, `Event` albo listę ról, użytkownik od razu zobaczy niespójność.

Lokalizacja w XAF nie kończy się więc na klasach. Ona kończy się dopiero wtedy, kiedy cały przepływ po aplikacji wygląda spójnie językowo.

## Gdzie domykać to technicznie

Najwygodniejsze miejsce to nadal model lokalizacji:

```xml
<Class Name="MainDemo.Module.BusinessObjects.Position" Caption="Stanowisko">
  <OwnMembers>
    <Member Name="Departments" Caption="Działy" />
    <Member Name="Employees" Caption="Pracownicy" />
    <Member Name="Title" Caption="Nazwa" />
  </OwnMembers>
</Class>
```

Ale nie kończysz na `BOModel`. Trzeba też zajrzeć do:

- `Localization` — wartości enumów i komunikaty,
- `NavigationItems` — nazwy pozycji menu,
- `Views` — nazwy list, logowania i grup w układach.

Właśnie to odróżnia "mamy polski język" od "mamy polski interfejs".

## Test przez API

Sprawdzenie w UI jest potrzebne, ale warto mieć też szybki test na poziomie HTTP.

Jeśli aplikacja ma endpoint lokalizacyjny, można to sprawdzić banalnie:

```csharp
var result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Position");
Assert.Equal("Stanowisko", result);
```

W tym repo to nie jest pseudokod. Mamy realny test:

```csharp
public class LocalizationTests : BaseWebApiTest {
    const string ApiUrl = "/api/Localization/";

    [Fact]
    public async Task GetAdditionalPolishClassCaptions() {
        var result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Position");
        Assert.Equal("Stanowisko", result);

        result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Resume");
        Assert.Equal("CV", result);

        result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=DevExpress.Persistent.BaseImpl.EF.ReportDataV2");
        Assert.Equal("Raporty", result);
    }

    protected async Task<string> SendRequestAsync(string locale, string url) {
        var request = new HttpRequestMessage(HttpMethod.Get, ApiUrl + url);
        request.Headers.Add("Accept-Language", locale);

        var httpResponse = await WebApiClient.SendAsync(request);
        return await httpResponse.Content.ReadAsStringAsync();
    }
}
```

To dobrze pokazuje, co się dzieje: test uderza w zwykły endpoint HTTP `api/Localization`, ustawia `Accept-Language: pl-PL` i sprawdza, czy aplikacja oddaje caption z modelu lokalizacji XAF.

Taki test ma dwie praktyczne zalety:

- test jest szybki,
- łapie regresję dokładnie tam, gdzie aplikacja faktycznie konsumuje lokalizację z modelu XAF.

Nie trzeba uruchamiać całego UI, żeby zauważyć, że ktoś usunął albo nadpisał wpis w `.xafml`.

## Co trzeba zrobić przy dodawaniu kolejnego języka

Jeżeli do działającej aplikacji dodajesz następny język, na przykład polski albo niemiecki, warto przejść przez ten zestaw kroków:

1. Dodać nowy język do konfiguracji aplikacji.
2. Dodać ten język do `RequestLocalizationOptions`, żeby aplikacja umiała przełączyć kulturę żądania.
3. Dołożyć pliki lokalizacyjne DevExpress dla warstwy JavaScript, jeżeli dany język ma być widoczny także w komponentach klienckich.
4. Uzupełnić tłumaczenia własnych klas biznesowych i ich pól w modelu XAF.
5. Sprawdzić klasy frameworkowe widoczne w UI, na przykład raporty, role, audyt albo kalendarz, i także dodać im tłumaczenia.
6. Uzupełnić wartości enumów, nazwy widoków, pozycje nawigacji i teksty logowania.
7. Dodać przynajmniej jeden test regresyjny, który wysyła żądanie z nagłówkiem `Accept-Language` i sprawdza, czy aplikacja zwraca właściwe captiony.

Jeżeli zrobisz tylko punkty 1-4, to język będzie formalnie dodany, ale użytkownik nadal zobaczy w różnych miejscach mieszankę nowego języka i angielskiego.

## Wersja repo

Pełny, repozytoryjny opis tej konkretnej zmiany jest tutaj:

- [`CS/docs/domkniecie-polskiej-lokalizacji-klas-i-widokow-w-maindemo-blazor.md`](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/domkniecie-polskiej-lokalizacji-klas-i-widokow-w-maindemo-blazor.md)

Tam są już konkretne pliki, konkretne typy i konkretne miejsca w modelu, które zostały dopisane.
