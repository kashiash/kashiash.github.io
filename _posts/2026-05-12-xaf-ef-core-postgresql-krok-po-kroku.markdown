---
layout: post
title: "XAF + EF Core + PostgreSQL krok po kroku"
---

Ten tekst jest dla programisty, który ma aplikację XAF na EF Core i chce ją poprawnie uruchomić na PostgreSQL.

Zakres:

- jedna zwykła baza
- bez multi-tenant na start
- na końcu krótko: co dochodzi przy multi-tenant

## 1. Sprawdź stan projektu

Najpierw znajdź:

1. miejsce rejestracji `DbContext`
2. miejsce wyboru providera bazy
3. miejsce budowania connection stringa
4. `IDesignTimeDbContextFactory`, jeśli projekt używa migracji
5. dodatkowe hosty: worker, testy, API

## 2. Dodaj provider PostgreSQL

Dodaj pakiet:

```xml
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />
```

Jeśli używasz migracji EF Core, dopilnuj zgodności wersji EF Core i narzędzi.

## 3. Zbierz konfigurację bazy do jednego miejsca

Projekt ma mieć jeden punkt, który:

- wybiera provider
- bierze connection string
- konfiguruje `DbContext`

Nie trzymaj konfiguracji bazy w kilku różnych plikach.

## 4. Przełącz EF Core na PostgreSQL

Podmień:

```csharp
options.UseSqlServer(connectionString);
```

na:

```csharp
options.UseNpgsql(connectionString);
```

Zrób to we wszystkich punktach wejścia:

- główny host
- worker
- testy integracyjne
- design-time factory

## 5. Przygotuj porządny connection string

Przykład:

```txt
Host=localhost;Port=5432;Database=MyApp;Username=myapp;Password=***;Pooling=true
```

Trzymaj go poza kodem:

- `appsettings`
- zmienne środowiskowe
- sekrety lokalne

## 6. Załóż lokalną bazę testową

Załóż:

- jedną bazę developerską
- jednego użytkownika aplikacyjnego
- prawa wystarczające do migracji i pracy aplikacji

## 7. Ustaw polskie znaki i polskie sortowanie

Baza ma:

- poprawnie zapisywać polskie znaki
- poprawnie sortować polski tekst

Przetestuj to na prawdziwych danych, na przykład `Łódź` i `Żaneta`.

## 8. Uruchom migracje i utwórz schemat

Jeśli używasz migracji EF Core:

1. utwórz migrację
2. uruchom aktualizację bazy
3. sprawdź, czy schemat tworzy się bez ręcznych poprawek

Projekt ma dać się postawić od zera.

## 9. Sprawdź typy danych

Obowiązkowo sprawdź:

- `DateTime`
- `string`
- `decimal`
- `Guid`
- `bool`
- `null`
- wartości domyślne

## 10. Sprawdź zachowanie projektu

Sprawdź:

- filtrowanie po datach
- wyszukiwanie po tekście
- zapis i odczyt pól
- porównywanie `null`

Nie pytaj, czy aplikacja startuje. Pytaj, czy działa poprawnie.

## 11. Zainstaluj `citext`

Jeśli robisz polską aplikację biznesową na PostgreSQL, instalujesz `citext`.

Powód:

- użytkownik wyszukuje tekst bez pilnowania wielkości liter
- pola tekstowe w aplikacji biznesowej prawie zawsze tego wymagają
- to jest praktyczny standard

Komenda SQL:

```sql
CREATE EXTENSION IF NOT EXISTS citext;
```

Przykład dla `psql`:

```powershell
psql -h localhost -U myapp -d MyApp -c "CREATE EXTENSION IF NOT EXISTS citext;"
```

Po instalacji mapujesz pola tekstowe tak, żeby projekt rzeczywiście z `citext` korzystał.

## 12. Zrób test końcowy

Po zmianie bazy sprawdź:

1. logowanie
2. otwieranie list
3. otwieranie formularzy
4. zapis nowego rekordu
5. edycję istniejącego rekordu
6. wyszukiwanie
7. raporty i dashboardy, jeśli projekt ich używa

## 13. Przygotuj wdrożenie

Przed wdrożeniem dopilnuj:

- ustawień bazy poza kodem
- osobnych connection stringów dla środowisk
- powtarzalnego procesu uruchomienia

## 14. Najczęstsze błędy

Najczęściej psuje się to:

1. podmieniony tylko connection string
2. kilka różnych miejsc konfiguracji bazy
3. brak poprawnej migracji
4. zła obsługa dat
5. brak testów po zmianie bazy

## 15. Co dochodzi przy multi-tenant

Przy multi-tenant dochodzi osobna warstwa pracy:

- osobne bazy albo osobne schematy
- trzymanie connection stringów tenantów
- zakładanie nowych baz
- migracje wielu baz
- pilnowanie zgodności schematu

Najpierw doprowadź do porządku jedną zwykłą bazę. Multi-tenant dokładaj dopiero potem.
