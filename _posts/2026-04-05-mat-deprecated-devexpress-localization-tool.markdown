---
layout: post
title: "Koniec MAT. Co dalej z lokalizacją w aplikacjach DevExpress?"
---

Microsoft zakończył wsparcie dla **Multilingual App Toolkit (MAT)** z dniem **15 października 2025 r.**. Dla zespołów, które używały MAT do tłumaczeń aplikacji .NET, oznacza to prostą rzecz: narzędzie nie będzie już miało gwarancji zgodności z nowymi wersjami toolingu i runtime'ów.

Dobra wiadomość jest taka, że samo tłumaczenie nie przepada. MAT opierał się o standardowe formaty **XLIFF** i **RESX**, więc dotychczasowe zasoby można nadal wykorzystać. Trzeba jednak przejść na nowe narzędzia i uporządkować proces lokalizacji.

W swoim wpisie DevExpress wskazuje nowy kierunek: **DevExpress Localization Tool** dostępny obecnie jako **CTP w wersji 25.2**. Narzędzie ma obsługiwać centralne zarządzanie tłumaczeniami, walidację spójności, eksport do różnych formatów, pracę zespołową oraz tłumaczenia wspierane przez AI. Już teraz obejmuje m.in. **WinForms, WPF, Blazor, ASP.NET Core, Reports, Dashboard i XAF**.

## Co robić teraz

1. **Nie rozwijaj już procesu opartego o MAT.** Jeśli jeszcze jest w użyciu, potraktuj go jako rozwiązanie przejściowe.
2. **Zachowaj i uporządkuj obecne pliki RESX/XLIFF.** To najważniejszy kapitał, bo migracja dotyczy narzędzia, nie samych tłumaczeń.
3. **Przetestuj DevExpress Localization Tool na jednym module lub projekcie pilotażowym.** Nie migruj wszystkiego naraz.
4. **Ustal jeden docelowy workflow lokalizacji.** Najlepiej taki, który obejmuje walidację, przegląd zmian i wersjonowanie tłumaczeń.
5. **Jeśli używasz XAF lub kilku produktów DevExpress naraz,** obserwuj rozwój nowego narzędzia, bo DevExpress zapowiada dalszą integrację i uproszczenie pracy w 2026 roku.

## Jak żyć w nowej sytuacji

Najrozsądniejsze podejście to potraktować koniec MAT nie jako problem, tylko jako moment na uporządkowanie lokalizacji. W praktyce oznacza to: trzymać tłumaczenia w standardowych formatach, nie wiązać procesu z jednym przestarzałym narzędziem i przejść na workflow, który da się utrzymać długoterminowo. Jeśli pracujesz w ekosystemie DevExpress, nowy Localization Tool wygląda dziś na naturalnego następcę.

Oryginalny wpis DevExpress:

<https://community.devexpress.com/Blogs/news/archive/2026/04/01/microsoft-multilingual-app-toolkit-mat-has-been-deprecated-what-s-next-for-devexpress-powered-app-localization.aspx>
