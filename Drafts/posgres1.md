# XAF + EF Core + PostgreSQL krok po kroku

![Migracja na PostgreSQL: Słoń i łódka XAF](https://kashiash.github.io/assets/images/xaf-postgresql.png)

Masz aplikację XAF na EF Core z SQL Server. Chcesz przejść na PostgreSQL — może koszty licencji, może wymagania klienta, może własny wybór.

Prosta zamiana connection stringa nie wystarczy. Trzeba:

- zainstalować inną bibliotekę providera,
- zmienić obsługę dat i pól tekstowych,
- znaleźć wszystkie miejsca, gdzie aplikacja łączy się z bazą.

A tych miejsc może być kilka: Web API, aplikacja Blazor, aplikacja Windows, czasem testy integracyjne. Jeśli pominiesz choć jedno — część aplikacji nadal będzie próbować połączyć się przez SQL Server.

Ten wpis prowadzi przez całą zmianę krok po kroku.

## Najpierw znajdź, gdzie projekt wybiera bazę

Zmiana w jednym miejscu nie wystarczy. Projekt ma zwykle kilka punktów wejścia do bazy — każdy musisz zmienić.

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

## Dodaj provider

Dodaj pakiet przez CLI:

```bash
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL
```

Bez podawania wersji pobierze najnowszą kompatybilną z projektem. Jeśli chcesz przypiąć do konkretnej wersji EF Core (np. 9.x):

```bash
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL --version 9.*
```

### Sprawdź zgodność wersji

Narzędzie `dotnet ef` i biblioteka EF Core muszą być w tej samej wersji głównej. Sprawdzasz tak:

```bash
# wersja zainstalowanych narzędzi globalnych
dotnet ef --version

# wersja EF Core w projekcie
dotnet list package | grep EntityFrameworkCore
```

Jeśli wersje się rozjeżdżają, aktualizujesz narzędzia:

```bash
dotnet tool update --global dotnet-ef
```

albo instalujesz od zera:

```bash
dotnet tool install --global dotnet-ef
```

## Zbierz konfigurację do jednego miejsca

Jeśli projekt ma konfigurację rozsypaną po kilku miejscach — trochę w `Program.cs`, trochę w helperze, trochę w testach, trochę w design-time factory — najpierw to porządkujesz.

Docelowo chcesz mieć jedną decyzję:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
{
    string connectionString = configuration.GetConnectionString("ConnectionString");
    options.UseNpgsql(connectionString);
});
```

## Przełącz wszystkie punkty wejścia

Podmieniasz `UseSqlServer` na `UseNpgsql` — ale nie tylko w głównej aplikacji.

**Web API / Blazor Server — `Program.cs`**

```csharp
builder.Services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("ConnectionString")));
```

**Aplikacja Windows (WinForms/WPF) — `Program.cs`**

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(configuration.GetConnectionString("ConnectionString")));
```

**Worker / osobny host**

Worker ma własny `IHost` — szukasz tam, nie w głównej aplikacji:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(hostContext.Configuration.GetConnectionString("ConnectionString")));
```

**Design-time factory**

Używana przez `dotnet ef` przy generowaniu migracji. Jeśli jej nie zmienisz, migracje nadal będą generowane pod SQL Server:

```csharp
public class MyAppDesignTimeDbContextFactory : IDesignTimeDbContextFactory<MyAppDbContext>
{
    public MyAppDbContext CreateDbContext(string[] args)
    {
        var optionsBuilder = new DbContextOptionsBuilder<MyAppDbContext>();
        optionsBuilder.UseNpgsql("Host=localhost;Database=MyApp;Username=myapp;Password=...");
        return new MyAppDbContext(optionsBuilder.Options);
    }
}
```

**Testy integracyjne**

Jeśli testy stawiają własny `WebApplicationFactory` albo budują `IHost` bezpośrednio:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(configuration.GetConnectionString("ConnectionString")));
```

Jeśli używasz in-memory database (`UseInMemoryDatabase`) — możesz zostawić jak jest, ale pamiętaj że testy in-memory nie sprawdzą problemów specyficznych dla PostgreSQL (daty, case-sensitivity, domyślne wartości).

## Connection string trzymaj poza kodem

Przykład connection stringa dla PostgreSQL:

```txt
Host=localhost;Port=5432;Database=MyApp;Username=myapp;Password=***;Pooling=true
```

### Gdzie trzymać — zależy od środowiska

**DEV — User Secrets (ASP.NET Core)**

To natywny mechanizm dla projektów ASP.NET Core. Sekret leży poza repo, w `%APPDATA%\Microsoft\UserSecrets\<id>\secrets.json`. `Host.CreateDefaultBuilder` scala go automatycznie dla środowiska `Development`.

```bash
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:ConnectionString" "Host=localhost;Port=5432;..."
```

Nie używaj do tego `appsettings.Development.json` — ten plik w domyślnym szablonie ASP.NET Core jest commitowany do gita. Hasło w tym pliku = hasło w repo.

**DEV — WinForms / App.config**

User Secrets to funkcja ASP.NET Core — w projekcie WinForms jej nie ma. Opcje:

- zmienna środowiskowa + ręczny odczyt w `Program.cs` przez `Environment.GetEnvironmentVariable`,
- migracja hosta Windows na `Microsoft.Extensions.Configuration` (więcej pracy, ale daje pełen ekosystem konfiguracji).

**Zmienne środowiskowe — notacja z `__`**

ASP.NET Core mapuje `ConnectionStrings:ConnectionString` na zmienną środowiskową `ConnectionStrings__ConnectionString` (dwa podkreślenia zamiast dwukropka — Windows nie pozwala na `:` w nazwach zmiennych). Jeśli ustawisz zmienną z jednym podkreśleniem albo z dwukropkiem, zostanie zignorowana.

**PROD — managed credentials**

Na produkcji nie trzymaj hasła w zmiennej środowiskowej dostępnej dla całego zespołu DevOps. W chmurze standard to Azure Key Vault + Managed Identity, AWS Secrets Manager + RDS IAM auth, albo HashiCorp Vault on-premise. Każde z tych rozwiązań działa podobnie: aplikacja sama pobiera connection string z sejfu przy starcie, bez żadnego hasła w kodzie ani konfiguracji.

Poniżej opisuję podejście z Dockerem — najczęstsze w środowiskach self-hosted i lokalnym CI/CD.

**Docker — sekrety i zmienne środowiskowe**

Docker oferuje dwa sposoby na przekazanie connection stringa do kontenera.

*Zmienne środowiskowe* — najprostsze, ale hasło jest widoczne w `docker inspect` i logach CI. Używaj tylko lokalnie lub w środowiskach bez wrażliwych danych:

```yaml
# docker-compose.yml
services:
  myapp:
    image: myapp:latest
    environment:
      - ConnectionStrings__ConnectionString=Host=db;Port=5432;Database=MyApp;Username=myapp;Password=tajne
  db:
    image: postgres:18
    environment:
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=tajne
      - POSTGRES_DB=MyApp
```

Pamiętaj o podwójnym podkreśleniu (`__`) zamiast dwukropka — ASP.NET Core tak mapuje zagnieżdżone klucze konfiguracji.

*Plik `.env`* — hasło wyciągasz poza `docker-compose.yml` do osobnego pliku, który nie trafia do gita (dodajesz go do `.gitignore`):

```bash
# .env  ← ten plik wpisujesz do .gitignore
DB_PASSWORD=tajne
```

```yaml
# docker-compose.yml
services:
  myapp:
    image: myapp:latest
    environment:
      - ConnectionStrings__ConnectionString=Host=db;Port=5432;Database=MyApp;Username=myapp;Password=${DB_PASSWORD}
  db:
    image: postgres:18
    environment:
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=MyApp
```

Docker Compose automatycznie wczytuje `.env` z tego samego katalogu co `docker-compose.yml`.

*Docker Secrets* — właściwe rozwiązanie dla produkcji z Docker Swarm. Sekret jest szyfrowany w raft store klastra i montowany jako plik wewnątrz kontenera:

```bash
# tworzysz sekret raz na klastrze
echo "Host=db;Port=5432;Database=MyApp;Username=myapp;Password=tajne" \
  | docker secret create myapp_connection_string -
```

```yaml
# docker-compose.yml (tryb Swarm)
services:
  myapp:
    image: myapp:latest
    secrets:
      - myapp_connection_string
    environment:
      # wskazujesz ścieżkę do pliku z sekretem wewnątrz kontenera
      - ConnectionStrings__ConnectionString_FILE=/run/secrets/myapp_connection_string

secrets:
  myapp_connection_string:
    external: true
```

ASP.NET Core nie czyta `_FILE` natywnie — musisz dodać obsługę w `Program.cs`:

```csharp
// Program.cs — wczytaj connection string z pliku jeśli istnieje
var secretPath = "/run/secrets/myapp_connection_string";
if (File.Exists(secretPath))
{
    var connectionString = await File.ReadAllTextAsync(secretPath);
    builder.Configuration["ConnectionStrings:ConnectionString"] = connectionString.Trim();
}
```

*Kolejność bezpieczeństwa od najsłabszego do najsilniejszego:*

1. zmienna środowiskowa w `docker-compose.yml` — tylko lokalnie
2. plik `.env` poza repo — DEV i staging
3. Docker Secrets — produkcja na Swarm
4. Key Vault / Secrets Manager — produkcja w chmurze

## Załóż bazę i użytkownika aplikacyjnego

Aplikacja nie powinna łączyć się z bazą jako `postgres` (superuser). Zamiast tego tworzysz osobnego użytkownika dla tej aplikacji. Po co?

- **Least privilege** — jeśli connection string wycieknie, atakujący nie dropnie schematu, nie założy nowych ról ani nie wejdzie do innych baz na tym samym serwerze.
- **Audit** — logi PostgreSQL można filtrować per-użytkownik. Bez osobnego usera nie wiesz, które zapytania pochodzą z aplikacji, a które od kogoś innego.
- **Rotacja hasła** — hasło app usera możesz zmienić bez dotykania konta `postgres` ani innych aplikacji na serwerze.

Skrypt zakładający bazę i usera:

```sql
CREATE USER myapp WITH PASSWORD 'mocne_haslo';
CREATE DATABASE "MyApp" OWNER myapp;
```

Baza jest własnością `myapp` — właściciel ma pełne prawa do swojej bazy, więc dodatkowy `GRANT` nie jest potrzebny. Jeśli z jakiegoś powodu baza już istnieje i właściciel jest inny, dorzuć:

```sql
GRANT ALL ON SCHEMA public TO myapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO myapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO myapp;
```

Bez tego app user dostanie `permission denied` na tabelach, które XAF dopiero co utworzył. W PostgreSQL 18 domyślne uprawnienia do schematu `public` są ograniczone — każdy user musi mieć je nadane explicite.

Po założeniu usera od razu sprawdzasz połączenie:

```bash
psql -h localhost -U myapp -d MyApp
```

## Polskie znaki i sortowanie

Zaraz po podłączeniu sprawdzasz:

- zapis `Łódź`
- zapis `Żaneta`
- wyszukiwanie `warszawa` kontra `Warszawa`
- kolejność sortowania na liście

## Zainstaluj `citext`

PostgreSQL domyślnie rozróżnia wielkość liter przy porównywaniu tekstów. SQL Server tego nie robi. Żeby wyszukiwanie działało tak samo jak wcześniej, instalujesz rozszerzenie `citext`.

**Ważne: `CREATE EXTENSION` wymaga uprawnień superusera.** App user (`myapp`) tego nie zrobi. Rozszerzenie instaluje DBA raz, ręcznie, po założeniu bazy:

```sql
\c "MyApp"
CREATE EXTENSION IF NOT EXISTS citext;
```

Nie wrzucaj tego do kodu startowego aplikacji (np. `UpdateDatabaseBeforeUpdateSchema`). Jeśli app user spróbuje wykonać `CREATE EXTENSION` przy starcie — dostanie `permission denied` i aplikacja nie wstanie.

Na managed PostgreSQL (AWS RDS, Azure Database for PostgreSQL, Supabase) dodatkowo obowiązuje whitelist rozszerzeń — `citext` trzeba włączyć przez panel lub parametr `rds.allowed_extensions` zanim w ogóle będzie można go zainstalować.

Po zainstalowaniu rozszerzenia mapujesz pola tekstowe tak, żeby projekt rzeczywiście z `citext` korzystał.

## Migracje

Normalna ścieżka:

```bash
dotnet ef migrations add InitPostgres
dotnet ef database update
```

Jeśli masz już istniejącą migrację:

```bash
dotnet ef database update
```

Tu zwykle wychodzi prawda o projekcie — błędy w migracjach często wskazują na miejsca, które trzeba jeszcze poprawić.

## Co może pójść nie tak

Przy przejściu z SQL Server na PostgreSQL najczęściej wysypują się te same rzeczy.

**Daty i czas** — PostgreSQL rozróżnia `timestamp` (bez strefy) i `timestamptz` (ze strefą). EF Core domyślnie mapuje `DateTime` na `timestamp without time zone`. Jeśli aplikacja gdzieś zakłada UTC albo lokalną strefę czasową, mogą pojawić się błędy przy zapisie lub odczycie dat.

**Liczby dziesiętne** — `decimal` w SQL Server i `numeric` w PostgreSQL zachowują się podobnie, ale mogą różnić się precyzją i skalą. Warto sprawdzić pola cen, stawek i kwot.

**Domyślne wartości kolumn** — jeśli w migracjach masz ręcznie ustawione `defaultValueSql`, składnia SQL Server nie zadziała na PostgreSQL. Trzeba przepisać na składnię PostgreSQL.

**Porównywanie tekstów** — SQL Server domyślnie ignoruje wielkość liter. PostgreSQL rozróżnia. Wyszukiwanie `"warszawa"` nie znajdzie `"Warszawa"`. Dlatego warto zainstalować rozszerzenie `citext` — opisuję to w osobnej sekcji powyżej.

**Ręcznie pisany SQL** — jeśli w projekcie są fragmenty `FromSqlRaw(...)` albo `ExecuteSqlRaw(...)`, ich składnia może być specyficzna dla SQL Server. Każdy taki fragment trzeba przejrzeć ręcznie.

## Jak naprawić wyszukiwanie małe/wielkie litery

Jeśli po migracji wyszukiwanie przestało działać case-insensitive — tzn. `"warszawa"` nie znajduje `"Warszawa"` — to znaczy że kolumny są typem `text` zamiast `citext`. Poniżej komplet zmian, które to naprawiają.

### 1. DbContext — mapuj wszystkie kolumny string na `citext`

W `OnModelCreating` dodajesz dwa bloki: rejestrację rozszerzenia i pętlę zamieniającą typ kolumn.

```csharp
// Module/BusinessObjects/AplikacjaDoPrzechowywaniaUmowDbContext.cs
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);

    modelBuilder.HasPostgresExtension("citext");

    foreach (var entity in modelBuilder.Model.GetEntityTypes())
    {
        foreach (var property in entity.GetProperties())
        {
            if (property.ClrType != typeof(string)) continue;
            if (property.Name == "StoredPassword") continue; // hash hasła zostaje text
            property.SetColumnType("citext");
        }
    }
}
```

`citext` robi case-insensitive equality na poziomie bazy — bez żadnych `ToLower()` w kodzie. Wyjątek to `StoredPassword`: hash hasła musi być porównywany binarnie, więc zostawiasz go jako `text`.

### 2. Updater — zainstaluj rozszerzenie przed DDL

XAF ma własny schema-syncer — nie wykonuje migracji EF Core, tylko porównuje model do bazy i wysyła DDL. Jeśli rozszerzenie `citext` nie istnieje w bazie zanim XAF wyśle `ALTER COLUMN ... TYPE citext`, dostaniesz błąd. Dlatego instalujesz je w `UpdateDatabaseBeforeUpdateSchema`:

```csharp
// Module/DatabaseUpdate/Updater.cs
using Microsoft.EntityFrameworkCore;

public override void UpdateDatabaseBeforeUpdateSchema()
{
    base.UpdateDatabaseBeforeUpdateSchema();

    if (ObjectSpace is DevExpress.ExpressApp.EFCore.EFCoreObjectSpace efCoreObjectSpace
        && efCoreObjectSpace.DbContext.Database.IsNpgsql())
    {
        efCoreObjectSpace.DbContext.Database.ExecuteSqlRaw(
            "CREATE EXTENSION IF NOT EXISTS citext;");
    }
}
```

`IF NOT EXISTS` sprawia że kod jest idempotentny — możesz go zostawiać na zawsze, nie zaszkodzi.

**Ważne:** ten kod zadziała tylko jeśli user bazodanowy ma uprawnienia do `CREATE EXTENSION`. Jeśli aplikacja łączy się jako app user (nie superuser) — `CREATE EXTENSION` musi wykonać DBA raz ręcznie, a powyższy kod będzie wtedy no-op.

### 3. Migracja EF Core — zaktualizuj snapshot

Generujesz migrację nie po to żeby ją wykonać (XAF tego nie zrobi), ale żeby zaktualizować snapshot modelu. Na jego podstawie XAF porównuje model do bazy i decyduje jakie DDL wysłać.

```bash
dotnet ef migrations add AddCitextSupport
```

Migracja będzie zawierać:
- `migrationBuilder.AlterDatabase().Annotation("Npgsql:PostgresExtension:citext", ",,")` — rejestracja rozszerzenia w snaphocie
- `AlterColumn<string>(..., type: "citext", oldType: "text")` — dla każdej kolumny string

Bez tego snapshot nadal myśli że kolumny są `text` i XAF nigdy nie wyśle `ALTER COLUMN`.

### 4. Baza — zainstaluj rozszerzenie ręcznie (raz)

Jako użytkownik `postgres` (superuser):

```bash
psql -h localhost -U postgres -d MyApp -c "CREATE EXTENSION IF NOT EXISTS citext;"
```

Sprawdzenie czy rozszerzenie jest zainstalowane:

```sql
SELECT * FROM pg_extension WHERE extname = 'citext';
-- citext  1.8  zainstalowane w schemacie public
```

### 5. Uruchom aplikację z `--updateDatabase`

XAF zobaczy różnicę między snapshotem (kolumny `citext`) a bazą (kolumny `text`) i wyśle `ALTER COLUMN ... TYPE citext` dla każdej kolumny:

```bash
dotnet run --project YourApp.Blazor.Server -- --updateDatabase --forceUpdate --silent
```

Weryfikacja po aktualizacji:

```sql
SELECT column_name, udt_name
FROM information_schema.columns
WHERE table_name = 'PermissionPolicyUser'
  AND column_name IN ('UserName', 'StoredPassword');

-- UserName       | citext
-- StoredPassword | text   ← wykluczone celowo
```

### Podsumowanie zmian

| Co | Gdzie | Po co |
|---|---|---|
| `HasPostgresExtension` + pętla na kolumnach | `DbContext.OnModelCreating` | EF Core generuje DDL z `citext` zamiast `text` |
| `ExecuteSqlRaw("CREATE EXTENSION...")` | `Updater.UpdateDatabaseBeforeUpdateSchema` | rozszerzenie istnieje zanim XAF wyśle DDL |
| `dotnet ef migrations add` | terminal | snapshot modelu zaktualizowany do `citext` |
| `CREATE EXTENSION citext` | psql jako superuser | rozszerzenie zainstalowane w bazie |
| `--updateDatabase --forceUpdate` | uruchomienie aplikacji | XAF konwertuje kolumny z `text` na `citext` |



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

Multi-tenant ma sens dopiero wtedy, gdy pojedyncza baza działa stabilnie. Inaczej troubleshooting staje się koszmarem.

Kiedy podstawowa migracja jest dopięta, dochodzi:

- osobna baza na tenant albo osobny schemat
- trzymanie connection stringów tenantów
- zakładanie nowych baz
- migracje wielu baz
- pilnowanie zgodności schematu

Osobno rozpisałem to tutaj:

[XAF + EF Core + PostgreSQL + multi-tenant](https://kashiash.github.io/2026/05/12/xaf-ef-core-postgresql-multitenant.html)