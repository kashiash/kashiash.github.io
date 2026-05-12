---
layout: post
title: "XAF + EF Core + PostgreSQL krok po kroku"
---

Masz aplikację XAF na EF Core. Działa na SQL Server. Chcesz ją przełączyć na PostgreSQL i nie utopić dwóch dni w poprawianiu głupot. To jest właśnie ten przypadek.

Nie zaczynasz od connection stringa. To jest ostatnia rzecz, która wygląda niewinnie, a potem się okazuje, że worker dalej siedzi na SQL Server, migracje lecą przez zły provider, a testy w ogóle nie dotykają tej samej konfiguracji co aplikacja.

## Najpierw znajdź, gdzie projekt naprawdę wybiera bazę

W praktyce szukasz czterech miejsc:

- rejestracja `DbContext`
- `IDesignTimeDbContextFactory`
- worker albo osobny host
- testy integracyjne

Typowy stan przed zmianą wygląda tak:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseSqlServer(configuration.GetConnectionString("ConnectionString")));
```

albo tak:

```csharp
public class MyAppDesignTimeDbContextFactory : IDesignTimeDbContextFactory<MyAppDbContext>
{
    public MyAppDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<MyAppDbContext>();
        optionsBuilder.UseSqlServer("...");
        return new MyAppDbContext(optionsBuilder.Options);
    }
}
```

To drugie miejsce ludzie bardzo lubią pominąć.

## Dodaj provider. Bez kombinowania.

Pakiet:

```xml
<PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" />
```

Jeżeli używasz migracji, dopilnuj zgodności wersji EF Core i narzędzi.

## Zbierz konfigurację do jednego miejsca

Jeżeli projekt ma:

- trochę konfiguracji w `Program.cs`
- trochę w helperze
- trochę w testach
- trochę w design-time factory

to najpierw to porządkujesz.

Docelowo chcesz mieć jedną decyzję:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
{
    string connectionString = configuration.GetConnectionString("ConnectionString");
    options.UseNpgsql(connectionString);
});
```

## Przełącz wszystko, nie tylko główny host

Podmieniasz:

```csharp
options.UseSqlServer(connectionString);
```

na:

```csharp
options.UseNpgsql(connectionString);
```

ale nie tylko w głównej aplikacji. Sprawdzasz jeszcze:

- worker
- Web API, jeśli jest osobno
- design-time factory
- testy

## Connection string ma siedzieć poza kodem

Normalny przykład:

```txt
Host=localhost;Port=5432;Database=MyApp;Username=myapp;Password=***;Pooling=true
```

Źródło:

- `appsettings.Development.json`
- zmienne środowiskowe
- lokalne sekrety

## Załóż bazę i użytkownika developerskiego

Na lokalnym środowisku robisz jedną bazę i jednego użytkownika aplikacyjnego.

Przykład:

```sql
CREATE USER myapp WITH PASSWORD 'mocne_haslo';
CREATE DATABASE "MyApp" OWNER myapp;
GRANT ALL PRIVILEGES ON DATABASE "MyApp" TO myapp;
```

Po tym od razu sprawdzasz połączenie:

```powershell
psql -h localhost -U myapp -d MyApp
```

## Polskie znaki i sortowanie

To sprawdzasz od razu:

- zapis `Łódź`
- zapis `Żaneta`
- wyszukiwanie `warszawa` kontra `Warszawa`
- kolejność sortowania na liście

## Zainstaluj `citext`

Dla polskiej aplikacji biznesowej na PostgreSQL instalujesz `citext`.

Komenda:

```sql
CREATE EXTENSION IF NOT EXISTS citext;
```

Przez `psql`:

```powershell
psql -h localhost -U myapp -d MyApp -c "CREATE EXTENSION IF NOT EXISTS citext;"
```

Potem mapujesz pola tekstowe tak, żeby projekt rzeczywiście z `citext` korzystał.

## Migracje. Tu zwykle wychodzi prawda o projekcie.

Normalna ścieżka:

```powershell
dotnet ef migrations add InitPostgres
dotnet ef database update
```

albo, jeśli migracja już istnieje:

```powershell
dotnet ef database update
```

## Co najczęściej pęka

Zwykle te same rzeczy:

- `DateTime`
- `decimal`
- własne domyślne wartości
- tekst i porównywanie napisów
- ręcznie dopisany SQL

## Sprawdź projekt jak człowiek, nie jak README

Po przejściu na PostgreSQL odpalasz i sprawdzasz:

1. logowanie
2. otwarcie listy
3. otwarcie formularza
4. zapis nowego rekordu
5. edycję istniejącego
6. filtrowanie po dacie
7. wyszukiwanie po tekście
8. raporty albo dashboardy, jeśli ich używasz

## Co dochodzi przy multi-tenant

Na końcu dopiero dokładamy multi-tenant.

Dochodzi:

- osobna baza na tenant albo osobny schemat
- trzymanie connection stringów tenantów
- zakładanie nowych baz
- migracje wielu baz
- pilnowanie zgodności schematu

Jeżeli jedna zwykła baza nie jest jeszcze dopięta porządnie, nie wchodzisz w multi-tenant.
