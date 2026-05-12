---
layout: post
title: "XAF + EF Core + PostgreSQL krok po kroku"
---

Jeśli masz zwykłą aplikację **XAF na EF Core** i chcesz dodać do niej **PostgreSQL**, to najgorsze, co możesz zrobić, to potraktować temat jak prostą podmianę connection stringa. To prawie nigdy nie kończy się dobrze.

Sam provider bazy to tylko początek. Trzeba jeszcze uporządkować konfigurację EF Core, przygotować bazę, sprawdzić mapowanie typów danych, przejść migracje i upewnić się, że aplikacja naprawdę działa na nowej bazie, a nie tylko się kompiluje.

Ten wpis jest o **zwykłej aplikacji**, bez multi-tenant. Na końcu dopisuję krótko, co dochodzi dodatkowo, jeśli później chcesz pójść w wiele baz albo tenantów.

## 1. Najpierw ustal, co dokładnie dziś masz w projekcie

Zanim dotkniesz PostgreSQL, sprawdź cztery rzeczy:

1. gdzie rejestrowany jest `DbContext`
2. gdzie wybierany jest provider bazy
3. czy projekt już używa migracji EF Core
4. czy w kodzie są miejsca pisane pod SQL Server

To jest ważne, bo w wielu projektach konfiguracja bazy nie siedzi w jednym miejscu. Część jest w `Program.cs`, część w innym projekcie, część w testach, a część w pomocniczych klasach. Jeśli tego nie zbierzesz na początku, to później będziesz poprawiał PostgreSQL na raty i w losowych miejscach.

## 2. Dodaj provider PostgreSQL dla EF Core

W projekcie, który konfiguruje EF Core, dodaj pakiet:

```xml
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />
```

Jeśli projekt korzysta z migracji, dopilnuj też, żeby narzędzia EF Core były spójne z używaną wersją .NET i EF.

To jest pierwszy krok techniczny, ale on sam niczego jeszcze nie załatwia. Po jego dodaniu aplikacja dalej może być skonfigurowana pod SQL Server i dalej może zakładać, że działa na SQL Server.

## 3. Zbierz konfigurację bazy do jednego miejsca

To jest jeden z najważniejszych kroków i bardzo często pomijany.

Dobrze zrobiony projekt powinien mieć **jedno miejsce**, w którym:

- wybierasz provider bazy
- bierzesz connection string
- konfigurujesz `DbContext`

Nie warto mieć jednego `UseSqlServer(...)` w głównym projekcie, drugiego w testach, trzeciego w osobnym hoście i czwartego w design-time factory. To się bardzo źle utrzymuje.

Cel jest prosty: jak zmieniasz bazę, to zmieniasz logikę w jednym punkcie, a nie szukasz jej po całym repo.

## 4. Przełącz EF Core z SQL Server na PostgreSQL

Jeśli dziś masz coś takiego:

```csharp
options.UseSqlServer(connectionString);
```

to docelowo ma być:

```csharp
options.UseNpgsql(connectionString);
```

Brzmi banalnie, ale trzeba to zrobić we wszystkich miejscach, gdzie naprawdę powstaje `DbContext`.

Jeśli aplikacja ma:

- główny host
- osobny worker
- testy integracyjne
- Web API
- narzędzia design-time

to każde z tych miejsc trzeba sprawdzić osobno.

## 5. Przygotuj connection string tak, żeby nie robił wstydu

Connection string do PostgreSQL powinien być trzymany poza kodem. Najczęściej:

- w `appsettings`
- w zmiennych środowiskowych
- w lokalnych sekretach

Nie wpisuj hasła na sztywno do klasy konfiguracyjnej. To działa przez chwilę, a potem zaczyna żyć własnym życiem i ląduje w miejscach, w których nie powinno go być.

Przykład:

```txt
Host=localhost;Port=5432;Database=MyApp;Username=myapp;Password=***;Pooling=true
```

Najważniejsze jest nie to, żeby ten connection string był "ładny", tylko żeby:

- był pobierany z jednego źródła
- dało się go zmienić bez przebudowy aplikacji
- nie mieszał ustawień lokalnych z testowymi i produkcyjnymi

## 6. Załóż lokalną bazę testową

Nie testuj przejścia na PostgreSQL na przypadkowej starej bazie, jeśli możesz tego uniknąć. Dużo bezpieczniej jest zacząć od czystej bazy developerskiej.

Na tym etapie potrzebujesz:

- jednej bazy developerskiej
- jednego użytkownika aplikacyjnego
- uprawnień wystarczających do pracy aplikacji i migracji

W praktyce warto od razu sprawdzić:

- czy aplikacja łączy się z bazą
- czy użytkownik ma prawa do tworzenia i aktualizacji schematu
- czy środowisko działa bez ręcznego poprawiania po starcie

## 7. Zadbaj o polskie znaki i polskie sortowanie

To nie jest temat "na później", jeśli aplikacja ma pracować po polsku.

Baza ma:

- poprawnie przechowywać polskie znaki
- sensownie sortować tekst po polsku

To są dwie różne rzeczy. Sam zapis znaków to jeszcze nie wszystko. Użytkownik końcowy zauważa problem dopiero wtedy, gdy lista wygląda dziwnie albo wyszukiwanie działa inaczej, niż się spodziewał.

Warto więc od początku przygotować bazę tak, żeby:

- tekst był zapisywany bez problemów
- sortowanie było zgodne z polskim użyciem
- testy obejmowały realne dane typu `Łódź`, `Żaneta`, `Świętochłowice`

## 8. Uruchom migracje EF Core i utwórz schemat

Jeśli projekt używa migracji, to PostgreSQL powinien mieć własną poprawną ścieżkę utworzenia schematu.

Na tym etapie trzeba:

1. utworzyć migrację
2. uruchomić aktualizację bazy
3. sprawdzić, czy schemat tworzy się bez ręcznych obejść

To jest moment, w którym wychodzą różnice między "projekt kompiluje się" a "projekt naprawdę umie działać na PostgreSQL".

Jeśli migracja się wysypuje, to zwykle problem nie jest w samym PostgreSQL, tylko w tym, że model albo konfiguracja wcześniej były pisane pod założenia SQL Server.

## 9. Sprawdź typy danych, które najczęściej robią problemy

Najwięcej uwagi warto poświęcić tym miejscom:

- `DateTime`
- pola tekstowe
- `decimal`
- `Guid`
- `bool`
- pola opcjonalne
- wartości domyślne

Nie dlatego, że PostgreSQL jest "dziwny", tylko dlatego, że właśnie tu najłatwiej wyjdą ukryte założenia projektu.

Szczególnie daty i czas wymagają ostrożności. Jeśli aplikacja wcześniej działała na innych domyślnych zachowaniach providera, to po zmianie bazy różnice mogą wyjść przy filtrowaniu, porównywaniu albo zapisie.

## 10. PostgreSQL dobrze pokazuje błędy konfiguracji, które wcześniej były ukryte

To nie jest problem XAF. Jeśli model i pola są dobrze skonfigurowane, to standardowe filtry i widoki XAF działają normalnie.

Problemy zwykle wychodzą gdzie indziej:

- przy źle ustawionych datach
- przy założeniach o porównywaniu tekstu
- przy polach opcjonalnych i wartościach domyślnych
- przy własnej logice dopisanej poza standardowym mapowaniem

Dlatego po przejściu na PostgreSQL nie warto pytać tylko "czy lista się otwiera", ale też:

- czy da się filtrować po datach
- czy wyszukiwanie po tekście zachowuje się tak, jak oczekujesz
- czy zapis i odczyt pól dają te same wyniki co wcześniej

## 11. Rozważ rozszerzenia PostgreSQL tylko wtedy, gdy naprawdę są potrzebne

Przykład typowy to `citext`, czyli wygodniejsze porównywanie tekstu bez rozróżniania wielkości liter.

To może być bardzo przydatne, ale nie warto wrzucać rozszerzeń tylko dlatego, że "może się kiedyś przyda". Najpierw ustal:

- jaki problem chcesz rozwiązać
- czy standardowa konfiguracja już go nie rozwiązuje
- czy rozszerzenie nie dokłada nowej zależności bez realnej korzyści

Dobra zasada jest prosta: najpierw prosta baza i poprawna konfiguracja, potem dodatki.

## 12. Zrób normalny test końcowy aplikacji

Po zmianie bazy nie wystarczy, że aplikacja się uruchamia.

Trzeba sprawdzić przynajmniej:

1. logowanie
2. otwieranie list i formularzy
3. zapisywanie rekordów
4. filtrowanie
5. wyszukiwanie
6. raporty i dashboardy, jeśli są w projekcie

Ten etap nie służy do "odbębnienia testu", tylko do złapania miejsc, w których projekt niby działa, ale już nie tak samo jak wcześniej.

## 13. Przygotuj projekt do wdrożenia

Jeśli lokalnie wszystko działa, to dopiero wtedy przejdź do środowisk wyższych.

Na etapie wdrożenia pilnuj trzech rzeczy:

- ustawienia bazy mają być poza kodem
- środowiska mają mieć rozdzielone connection stringi
- proces uruchomienia ma być powtarzalny

Najgorszy scenariusz to taki, w którym lokalnie działa, ale na serwerze trzeba "jeszcze tylko ręcznie poprawić dwie rzeczy". To zwykle znaczy, że proces nie jest gotowy.

## 14. Najczęstsze błędy

Najczęściej powtarzają się te same problemy:

1. zmiana tylko connection stringa
2. zostawienie konfiguracji bazy w kilku miejscach
3. brak porządnej migracji
4. nieprzemyślane daty i czas
5. założenia o działaniu tekstu bez testów
6. brak końcowej weryfikacji na prawdziwej bazie

Jeśli tego pilnujesz od początku, to przejście na PostgreSQL jest normalną pracą konfiguracyjną, a nie wielką migracją pełną niespodzianek.

## Co dochodzi później przy multi-tenant

Jeśli później chcesz iść w **multi-tenant**, to dochodzi nowa warstwa problemów:

- czy każdy tenant ma mieć osobną bazę
- jak trzymać connection stringi tenantów
- jak zakładać nowe bazy
- jak uruchamiać migracje na wielu bazach
- jak pilnować zgodności schematu między tenantami

To ma sens, ale to już nie jest "zwykłe dodanie PostgreSQL". To jest osobny temat operacyjny i architektoniczny. Dlatego warto najpierw porządnie ogarnąć jedną zwykłą aplikację na PostgreSQL, a dopiero potem dokładać warstwę tenantów.

Jeśli masz dziś aplikację XAF na EF Core bez PostgreSQL, to najrozsądniejsza kolejność jest taka:

1. uporządkuj konfigurację
2. dodaj provider
3. przełącz EF Core
4. przygotuj bazę
5. uruchom migracje
6. sprawdź typy danych i zachowanie aplikacji
7. dopiero potem myśl o wdrożeniu i multi-tenant

Tak jest po prostu mniej boleśnie.
