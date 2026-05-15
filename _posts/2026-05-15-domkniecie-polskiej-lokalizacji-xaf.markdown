---
layout: post
title: "Domknięcie polskiej lokalizacji w XAF: klasy, enumy i widoki bez mieszanki PL/EN"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 4
---

> **Część 4 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> Nie tworzymy aplikacji od zera — postawienie projektu XAF Blazor + EF Core jest krok po kroku opisane w [oficjalnej dokumentacji DevExpress](https://docs.devexpress.com/eXpressAppFramework/) i to jest miejsce, w którym każdy może (i powinien) zacząć. My ciągniemy ten temat dalej: bierzemy publiczny projekt referencyjny `MainDemo.NET.EFCore` i pokazujemy, co dochodzi w nim po stronie realnego wdrożenia.
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. [Custom DateEditor z parametrem modelowym do blokady kółka myszy]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})
> 4. **Domknięcie polskiej lokalizacji: klasy, enumy i widoki** — ten wpis

Samo dodanie `pl-PL` do aplikacji nie zamyka lokalizacji. To dopiero pierwszy etap. Prawdziwy test przychodzi wtedy, kiedy użytkownik zaczyna normalnie klikać po systemie i nagle okazuje się, że menu jest po polsku, ale nazwa raportu, widok stanowisk albo część słowników dalej wraca do angielskiego.

To nie jest błąd samego Blazora. To jest bardzo typowy niedomknięty model XAF.

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

W efekcie dostajesz interfejs, który jest "prawie po polsku". A "prawie" w biznesowej aplikacji wygląda po prostu niedbale.

## Konkret z repo, nie teoria

W repo:

- [kashiash/MainDemoEFCoreCustomization](https://github.com/kashiash/MainDemoEFCoreCustomization)

dopisałem kolejną warstwę polskiej lokalizacji do pliku:

- `CS/MainDemo.Module/Model.DesignedDiffs.Localization.pl.xafml`

Nie ruszałem mechanizmu wyboru języka. Ten już działał. Domknąłem za to to, co użytkownik naprawdę widzi na ekranie:

- `Position` -> `Stanowisko`,
- `Resume` -> `CV`,
- `ReportDataV2` -> `Raporty`,
- `AuditDataItemPersistent` -> `Historia zmian`,
- polskie wartości `Priority`, `TaskStatus` i `DocumentType`,
- polskie nazwy pozycji w nawigacji i widokach list.

Do tego dorzuciłem test regresyjny, który pyta Web API o nazwy wyświetlane dla tych typów w `pl-PL`, żeby przy kolejnej przeróbce modelu nie wrócić przypadkiem do angielskiego.

## Dlaczego sam business object nie wystarcza

To jest rzecz, którą łatwo przeoczyć.

W XAF część ekranów nie składa się tylko z twoich klas domenowych. W praktyce użytkownik widzi miks:

- własnych obiektów biznesowych,
- typów DevExpressa,
- wpisów z modelu aplikacji,
- tekstów wygenerowanych przez moduły raportów, audytu i bezpieczeństwa.

Jeśli przetłumaczysz tylko `Employee`, `Department` i `DemoTask`, a zostawisz po angielsku `ReportDataV2`, `Event` albo listę ról, to użytkownik i tak od razu zobaczy pęknięcie.

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

## Dobra praktyka: sprawdzaj to przez API, nie na oko

Klikanie po UI jest potrzebne, ale ja wolę mieć jeszcze szybki test na poziomie HTTP.

Jeśli aplikacja ma endpoint lokalizacyjny, można to sprawdzić banalnie:

```csharp
var result = await SendRequestAsync("pl-PL", "ClassCaption?classFullName=MainDemo.Module.BusinessObjects.Position");
Assert.Equal("Stanowisko", result);
```

To ma dwie zalety:

- test jest szybki,
- łapie regresję dokładnie tam, gdzie model językowy faktycznie jest konsumowany.

Nie musisz odpalać całego UI, żeby zauważyć, że ktoś usunął albo nadpisał wpis w `.xafml`.

## Co bym zrobił za każdym razem przy nowym języku

Moja checklista:

1. Włącz język w konfiguracji aplikacji.
2. Ustaw wybór kultury w `RequestLocalizationOptions`.
3. Dograj pliki lokalizacyjne DevExpress dla warstwy JavaScript.
4. Przetłumacz podstawowe klasy i pola w modelu.
5. Przejrzyj typy frameworkowe widoczne w UI.
6. Uzupełnij enumy, nawigację, nazwy list i logowanie.
7. Dodaj przynajmniej jeden test regresyjny po `Accept-Language`.

Bez punktów 5-7 zwykle kończysz z półproduktem.

## Wersja repo

Pełny, repozytoryjny opis tej konkretnej zmiany jest tutaj:

- [`CS/docs/domkniecie-polskiej-lokalizacji-klas-i-widokow-w-maindemo-blazor.md`](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/domkniecie-polskiej-lokalizacji-klas-i-widokow-w-maindemo-blazor.md)

Tam są już konkretne pliki, konkretne typy i konkretne miejsca w modelu, które zostały dopisane.
