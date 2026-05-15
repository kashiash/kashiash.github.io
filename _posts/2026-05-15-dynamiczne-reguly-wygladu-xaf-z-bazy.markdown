---
layout: post
title: "Dynamiczne reguły wyglądu z bazy w XAF: encja, cache i AppearanceController"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 5
---

Sam `[Appearance]` w klasie biznesowej wystarcza tylko wtedy, gdy reguła ma być stała. W prawdziwej aplikacji dość szybko pojawia się potrzeba, żeby administrator mógł zmieniać wygląd bez rekompilacji: podświetlenie rekordów po terminie, ukrycie pola dla konkretnego widoku, wyróżnienie statusu, ostrzeżenie kolorystyczne dla operatora. Wtedy appearance przestaje być tylko atrybutem w kodzie i staje się danymi konfiguracyjnymi.

Właśnie taki wariant dodałem do `MainDemo.NET.EFCore`. Nie jako osobny silnik renderowania, tylko jako rozszerzenie standardowego `ConditionalAppearance` z XAF. Reguły siedzą w bazie jako encja `DynamicAppearanceRule`, są ładowane do prostego cache procesowego `DynamicAppearanceRuleStorage`, a kontroler `DynamicAppearanceRuleViewController` dokłada je do standardowego `AppearanceController` przez zdarzenie `CollectAppearanceRules`. Dzięki temu XAF dalej robi całą robotę z oceną kryteriów i nakładaniem stylu, a my tylko dokładamy dodatkowe źródło reguł.

W praktyce wzorzec składa się z siedmiu kroków:

1. włączasz `ConditionalAppearanceModule` w module i hostach,
2. dodajesz encję implementującą `IAppearanceRuleProperties`,
3. dopisujesz `DbSet` do `DbContext`,
4. tworzysz storage z metodami `Initialize`, `Put`, `Remove` i `GetRules`,
5. podpinasz kontroler do `AppearanceController.CollectAppearanceRules`,
6. inicjalizujesz cache przy starcie aplikacji,
7. seedujesz pierwszą regułę albo wystawiasz ekran administracyjny.

W MainDemo seedowana reguła podświetla zadania po terminie. Działa bez zmian zarówno w podejściu „demo”, jak i jako gotowy punkt wyjścia do osobnego projektu XAF. Najważniejsze jest to, że nie trzeba kopiować całej architektury HIS jeden do jednego. Wystarczy potraktować `IAppearanceRuleProperties` jako kontrakt wejściowy do `AppearanceController` i dołożyć tylko brakującą warstwę danych oraz cache.

Pełna instrukcja z plikami, kolejnością wdrożenia i komendami uruchomieniowymi jest w repo:

[Dynamiczne reguły wyglądu z bazy w XAF Blazor i WinForms](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/dynamiczne-reguly-wygladu-xaf-z-bazy.md)
