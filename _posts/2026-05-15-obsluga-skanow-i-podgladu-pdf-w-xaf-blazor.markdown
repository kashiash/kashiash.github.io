---
layout: post
title: "Obsługa skanów i podglądu PDF w XAF Blazor: dokumenty, upload i preview inline"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 6
---

W aplikacji referencyjnej XAF bardzo szybko dochodzi się do ściany: pojedynczy `FileData` gdzieś w encji albo prosty załącznik w jednym module nie wystarcza, gdy trzeba obsłużyć prawdziwe dokumenty. Pojawia się potrzeba słownika typów dokumentów, wielu plików przypinanych do różnych obiektów, drag-drop uploadu i podglądu PDF bez pobierania pliku na dysk.

Taki właśnie wzorzec dołożyłem do `MainDemo.NET.EFCore`. Nie jako nowy subsystem z osobną magią, tylko jako czytelny zestaw elementów XAF Blazor:

1. encja `DocumentFileType` jako słownik typów dokumentów,
2. encja `DocumentFile` z relacjami do właścicieli,
3. interfejs `IHasDocumentFiles`, żeby jeden kontroler obsługiwał wiele typów,
4. popup z `DxUpload` i multi-file uploadem,
5. endpoint API zapisujący `FileData`,
6. custom preview dla PDF i obrazów inline w Blazorze.

W tej iteracji właścicielami dokumentów są `Employee` i `DemoTask`. To wystarczy, żeby wzorzec był realny, a jednocześnie nie rozlewa zmian po całej demówce. Użytkownik wchodzi w zakładkę `Załączniki`, klika `Dodaj pliki`, wybiera typ dokumentu i od razu przeciąga kilka plików do strefy uploadu. Każdy plik zapisuje się jako osobny rekord `DocumentFile`, a po zamknięciu popupu lista się odświeża.

Najważniejsza decyzja techniczna była taka, żeby **nie podmieniać globalnie standardowego edytora `FileData`**. Zamiast tego podgląd siedzi na osobnej właściwości `PreviewFile`, a Blazor-only property editor renderuje:

- `<object>` dla PDF,
- `<img>` dla obrazów,
- czytelny komunikat z przyciskiem pobrania dla pozostałych rozszerzeń.

To pozwala zachować stabilność po stronie WinForms i nie wprowadza zależności platformowych do wspólnego modułu. `DOCX` i `XLSX` są już akceptowane na uploadzie, ale w tym kroku kończą się pobraniem pliku. Konwersję do PDF warto robić dopiero wtedy, gdy naprawdę jest potrzebna i wiadomo, gdzie ten koszt ma siedzieć.

Przy wdrożeniu wyszły też trzy drobne, ale typowe problemy:

- konflikt nazw `EditorAliases` między własnym modułem a DevExpressem,
- zły typ event args w `DxUpload`,
- odwołanie do właściciela nested listy przez niewłaściwe API (`Owner` zamiast `PropertyCollectionSource.MasterObject`).

To są właśnie rzeczy, które odróżniają działający wzorzec od ładnego snippetu. Kod został doprowadzony do zielonego `dotnet build`, a testy integracyjne przechodzą przez prawdziwy endpoint `multipart/form-data`, więc mechanizm jest sprawdzony end-to-end.

Pełny opis wdrożenia w tym repo, z listą plików i konkretnymi poprawkami kompilacji, jest tutaj:

[Obsługa skanów i podglądu PDF w MainDemo Blazor](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/obsluga-skanow-i-podgladu-pdf-w-main-demo-blazor.md)
