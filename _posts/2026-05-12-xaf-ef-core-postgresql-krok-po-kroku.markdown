---
layout: post
title: "XAF + EF Core + PostgreSQL krok po kroku"
---

![Migracja na PostgreSQL: Słoń i łódka XAF](/assets/images/xaf-postgresql.png)

Chcesz przenieść aplikację XAF (EF Core) z SQL Server na PostgreSQL. Sama zmiana connection stringa nie wystarczy — musisz zmienić providera w wielu punktach wejścia, dostosować bazę oraz skonfigurować porównywanie tekstów (citext). Ten poradnik pokazuje, jak przeprowadzić całą migrację krok po kroku.

Migracja na nową bazę obejmuje kilka kroków:

- instalację biblioteki nowego providera,
- dostosowania obsługi dat oraz pól tekstowych,
- znalezienia wszystkich punktów połączenia z bazą.

Punktów wejścia w projekcie bywa wiele. Są to: Web API, aplikacja Blazor, aplikacja desktopowa (WinForms) czy testy integracyjne. Jeśli pominiesz choć jedno miejsce, aplikacja nadal spróbuje połączyć się z SQL Server.

## Najpierw znajdź, gdzie projekt wybiera bazę

Zmiana w jednym pliku nie wystarczy. Projekt ma zwykle kilka punktów wejścia do bazy. Musisz zmodyfikować każdy z nich.

W praktyce szukasz czterech miejsc:

- rejestracji `DbContext`,
- `IDesignTimeDbContextFactory`,
- workera lub osobnego hosta,
- testów integracyjnych.

Typowy stan przed zmianą wygląda następująco:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseSqlServer(configuration.GetConnectionString("ConnectionString")));
```

lub tak:

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

Łatwo pominąć to drugie miejsce.

## Dodaj provider

Dodaj pakiet przez CLI:

```bash
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL
```

Jeśli nie podasz wersji, pobierzesz najnowszą wersję kompatybilną z projektem. Aby przypiąć pakiet do konkretnej wersji EF Core (np. 9.x), użyj:

```bash
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL --version 9.*
```

### Sprawdź zgodność wersji

Narzędzie `dotnet ef` oraz biblioteka EF Core muszą mieć tę samą wersję główną. Wersje sprawdzisz tak:

```bash
# wersja zainstalowanych narzędzi globalnych
dotnet ef --version

# wersja EF Core w projekcie
dotnet list package | grep EntityFrameworkCore
```

Jeśli wersje różnią się od siebie, zaktualizuj narzędzia:

```bash
dotnet tool update --global dotnet-ef
```

lub zainstaluj je od nowa:

```bash
dotnet tool install --global dotnet-ef
```

## Zbierz konfigurację w jednym miejscu

Jeśli projekt ma konfigurację rozsypaną po kilku plikach (trochę w `Program.cs`, trochę w helperze, w testach i w design-time factory), uporządkuj ją w pierwszej kolejności.

Docelowo skonfiguruj to w jednym miejscu:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
{
    string connectionString = configuration.GetConnectionString("ConnectionString");
    options.UseNpgsql(connectionString);
});
```

## Przełącz wszystkie punkty wejścia

Zastąp `UseSqlServer` metodą `UseNpgsql`. Zrób to we wszystkich modułach projektu, nie tylko w głównej aplikacji.

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

Worker uruchamia własny `IHost`. Skonfiguruj bazę w jego klasie startowej, a nie w głównej aplikacji:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(hostContext.Configuration.GetConnectionString("ConnectionString")));
```

**Design-time factory**

Narzędzie `dotnet ef` używa tej fabryki do generowania migracji. Jeśli jej nie zmodyfikujesz, narzędzie wygeneruje migracje dostosowane do SQL Server:

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

Dotyczy to sytuacji, gdy testy uruchamiają własną `WebApplicationFactory` lub bezpośrednio budują `IHost`:

```csharp
services.AddDbContext<MyAppDbContext>(options =>
    options.UseNpgsql(configuration.GetConnectionString("ConnectionString")));
```

Baza danych w pamięci (`UseInMemoryDatabase`) nie wymaga zmian. Pamiętaj jednak, że testy in-memory nie wykryją problemów specyficznych dla PostgreSQL (takich jak formaty dat, wielkość liter czy domyślne wartości).

## Trzymaj connection string poza kodem

Przykład parametrów połączenia (connection string) dla PostgreSQL:

```txt
Host=localhost;Port=5432;Database=MyApp;Username=myapp;Password=***;Pooling=true
```

### Gdzie trzymać konfigurację

**DEV — User Secrets (ASP.NET Core)**

To natywny mechanizm dla projektów ASP.NET Core. Sekret leży poza repozytorium, w katalogu `%APPDATA%\Microsoft\UserSecrets\<id>\secrets.json`. `Host.CreateDefaultBuilder` scala go automatycznie dla środowiska `Development`.

```bash
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:ConnectionString" "Host=localhost;Port=5432;..."
```

Nie używaj do tego pliku `appsettings.Development.json`. Szablon ASP.NET Core domyślnie dodaje go do Git-a, więc ujawnisz hasło w repozytorium.

**DEV — WinForms / App.config**

Projekt WinForms nie obsługuje mechanizmu User Secrets. Masz do wyboru:

- zmienną środowiskową i ręczny odczyt w `Program.cs` przez `Environment.GetEnvironmentVariable`,
- migrację hosta Windows na `Microsoft.Extensions.Configuration` (wymaga to pracy, ale daje pełen ekosystem konfiguracji).

**Zmienne środowiskowe — notacja z `__`**

ASP.NET Core mapuje `ConnectionStrings:ConnectionString` na zmienną środowiskową `ConnectionStrings__ConnectionString`. Użyj podwójnego podkreślenia (`__`) zamiast dwukropka. Windows nie pozwala na `:` w nazwach zmiennych. Jeśli użyjesz jednego podkreślenia lub dwukropka, framework zignoruje zmienną.

**PROD — zarządzanie poświadczeniami (managed credentials)**

Na produkcji nie trzymaj hasła w zmiennej środowiskowej dostępnej dla całego zespołu DevOps. W chmurze standard to Azure Key Vault z Managed Identity, AWS Secrets Manager z RDS IAM auth lub HashiCorp Vault on-premise. Wszystkie te metody działają podobnie: aplikacja pobiera parametry połączenia z bezpiecznego magazynu podczas startu. Nie musisz przechowywać hasła w kodzie ani w konfiguracji.

Poniżej opisuję konfigurację w Dockerze — popularną w środowiskach własnych (self-hosted) oraz w lokalnym CI/CD.

**Docker — sekrety i zmienne środowiskowe**

Docker oferuje dwa sposoby na przekazanie parametrów połączenia do kontenera.

*Zmienne środowiskowe* to najprostsza metoda. Hasło widać jednak w poleceniu `docker inspect` oraz w logach CI. Używaj ich tylko lokalnie lub w środowiskach testowych bez poufnych danych:

```yaml
# docker-compose.yml
services:
  myapp:
    image: myapp:latest
    environment:
      - ConnectionStrings__ConnectionString=Host=db;Port=5432;Database=MyApp;Username=myapp;Password=tajne
  db:
    image: postgres:17
    environment:
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=tajne
      - POSTGRES_DB=MyApp
```

Użyj podwójnego podkreślenia (`__`) zamiast dwukropka. ASP.NET Core mapuje w ten sposób zagnieżdżone klucze konfiguracji.

*Plik `.env`* pozwala przenieść hasło z pliku `docker-compose.yml` do osobnego pliku `.env`. Pamiętaj, aby dodać go do `.gitignore`:

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
    image: postgres:17
    environment:
      - POSTGRES_USER=myapp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=MyApp
```

Docker Compose automatycznie wczytuje plik `.env` z tego samego katalogu co `docker-compose.yml`.

*Docker Secrets* to właściwe rozwiązanie dla produkcji z Docker Swarm. Klaster szyfruje sekret w swojej bazie (raft store) i montuje go jako plik wewnątrz kontenera:

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

ASP.NET Core nie obsługuje zmiennych z końcówką `_FILE` automatycznie. Musisz dodać odpowiednią logikę w `Program.cs`:

```csharp
// Program.cs — wczytaj connection string z pliku, jeśli istnieje
var secretPath = "/run/secrets/myapp_connection_string";
if (File.Exists(secretPath))
{
    var connectionString = await File.ReadAllTextAsync(secretPath);
    builder.Configuration["ConnectionStrings:ConnectionString"] = connectionString.Trim();
}
```

*Poziomy bezpieczeństwa (od najsłabszego do najsilniejszego):*

1. Zmienna środowiskowa w `docker-compose.yml` — wyłącznie lokalnie.
2. Plik `.env` poza repozytorium — DEV i staging.
3. Docker Secrets — produkcja na Swarm.
4. Key Vault / Secrets Manager — produkcja w chmurze.

## Załóż bazę i użytkownika aplikacyjnego

Nie łącz się z bazą z konta `postgres` (superuser). Stwórz osobnego użytkownika przeznaczonego dla tej aplikacji. Powody:

- **Zasada minimalnych uprawnień (least privilege)** — jeśli parametry połączenia wyciekną, napastnik nie usunie schematu, nie utworzy ról ani nie uzyska dostępu do innych baz na tym samym serwerze.
- **Audyt** — możesz filtrować logi PostgreSQL według użytkowników. Bez osobnego konta nie odróżnisz zapytań aplikacji od pozostałych operacji.
- **Rotacja haseł** — zmienisz hasło użytkownika aplikacji bez wpływu na konto `postgres` lub inne systemy.

Skrypt zakładający bazę i użytkownika:

```sql
CREATE USER myapp WITH PASSWORD 'mocne_haslo';
CREATE DATABASE "MyApp" OWNER myapp;
```

Baza staje się własnością użytkownika `myapp`. Właściciel ma pełne uprawnienia do swojej bazy, więc nie musisz nadawać dodatkowych praw (`GRANT`). Jeśli baza już istnieje i ma innego właściciela, wykonaj:

```sql
GRANT ALL ON SCHEMA public TO myapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO myapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO myapp;
```

Bez tego użytkownik aplikacji otrzyma błąd `permission denied` na tabelach utworzonych przez XAF. W PostgreSQL 15 i nowszych domyślne uprawnienia do schematu `public` są ograniczone. Każdy użytkownik musi otrzymać je jawnie.

Po utworzeniu użytkownika sprawdź połączenie:

```bash
psql -h localhost -U myapp -d MyApp
```

## Polskie znaki i sortowanie

Po nawiązaniu połączenia sprawdź:

- zapis polskich znaków diakrytycznych (np. `Łódź`, `Żaneta`),
- wyszukiwanie bez uwzględniania wielkości liter (np. `warszawa` i `Warszawa`),
- kolejność sortowania na listach.

## Zainstaluj rozszerzenie `citext`

PostgreSQL domyślnie rozróżnia wielkość liter w tekstach. SQL Server tego nie robi. Aby wyszukiwanie działało w ten sam sposób co wcześniej, zainstaluj rozszerzenie `citext`.

**Ważne: `CREATE EXTENSION` wymaga uprawnień superusera.** Używaj konta administratora. Użytkownik aplikacji (`myapp`) nie ma takich praw. Administrator bazy danych (DBA) musi zainstalować rozszerzenie jednorazowo, ręcznie, po utworzeniu bazy:

```sql
\c "MyApp"
CREATE EXTENSION IF NOT EXISTS citext;
```

Nie umieszczaj tego polecenia w kodzie startowym wprost, bez odpowiedniej obsługi błędów. Jeśli użytkownik aplikacji nie ma praw superusera i spróbuje wykonać `CREATE EXTENSION` przy starcie, baza zwróci błąd `permission denied`, a aplikacja się nie uruchomi. Sposób z bezpiecznym blokiem `try-catch` (który pozwala na ignorowanie tego błędu na produkcji) opisuję w sekcji z konfiguracją poniżej.

W usługach zarządzanych PostgreSQL (AWS RDS, Azure Database for PostgreSQL, Supabase) obowiązuje lista dozwolonych rozszerzeń (whitelist). Musisz włączyć `citext` w panelu zarządzania lub ustawić parametr `rds.allowed_extensions` przed instalacją.

Po instalacji rozszerzenia zmapuj pola tekstowe, aby projekt korzystał z typu `citext`.

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

Na tym etapie najczęściej ujawniają się problemy w projekcie. Błędy w migracjach wskazują miejsca wymagające poprawek.

## Co może pójść nie tak

Podczas migracji z SQL Server na PostgreSQL najczęściej pojawiają się te same problemy.

**Daty i czas** — PostgreSQL rozróżnia `timestamp` (bez strefy) i `timestamptz` (ze strefą). EF Core domyślnie mapuje `DateTime` na `timestamp without time zone`. Jeśli w aplikacji zakładasz korzystanie z UTC lub lokalnej strefy czasowej, zapis lub odczyt dat może wygenerować błędy.

**Liczby dziesiętne** — `decimal` w SQL Server i `numeric` w PostgreSQL zachowują się podobnie, ale mogą różnić się precyzją i skalą. Sprawdź pola przeznaczone na ceny, stawki i kwoty.

**Domyślne wartości kolumn** — jeśli w migracjach ręcznie definiujesz `defaultValueSql`, składnia SQL Server nie zadziała w PostgreSQL. Przepisz te polecenia, dopasowując je do PostgreSQL.

**Porównywanie tekstów** — SQL Server domyślnie ignoruje wielkość liter, natomiast PostgreSQL ją rozróżnia. Wyszukiwanie `"warszawa"` nie wskaże `"Warszawa"`. Aby to naprawić, zainstaluj rozszerzenie `citext`, które opisałem wyżej.

**Ręcznie pisany SQL** — jeśli w projekcie używasz `FromSqlRaw(...)` lub `ExecuteSqlRaw(...)`, ich składnia może zależeć od SQL Server. Przejrzyj ręcznie każdy taki fragment.

## Jak naprawić wyszukiwanie bez uwzględniania wielkości liter

Jeśli po migracji wyszukiwanie nie ignoruje wielkości liter (np. `"warszawa"` nie wskazuje `"Warszawa"`), oznacza to, że kolumny wciąż mają typ `text` zamiast `citext`. Poniżej znajdziesz kroki, które to naprawią.

### 1. DbContext — mapuj kolumny string na `citext`

W metodzie `OnModelCreating` dodaj dwa elementy: rejestrację rozszerzenia oraz pętlę modyfikującą typ kolumn.

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

Typ `citext` zapewnia porównywanie bez uwzględniania wielkości liter (case-insensitive) bezpośrednio w bazie. Nie musisz stosować metody `ToLower()` w kodzie. Wyjątek stanowi pole `StoredPassword`. Hash hasła wymaga porównania binarnego, dlatego pozostaw dla niego typ `text`.

### 2. Updater — zainstaluj rozszerzenie przed poleceniami DDL

XAF korzysta z własnego mechanizmu synchronizacji schematu (schema syncer) — nie uruchamia migracji EF Core bezpośrednio, lecz porównuje model z bazą i wysyła polecenia DDL. Jeśli rozszerzenie `citext` nie istnieje w bazie przed wysłaniem przez XAF instrukcji `ALTER COLUMN ... TYPE citext`, system zgłosi błąd. Dlatego zainstaluj je w metodzie `UpdateDatabaseBeforeUpdateSchema`, przechwytując błąd braku uprawnień:

```csharp
// Module/DatabaseUpdate/Updater.cs
using Microsoft.EntityFrameworkCore;

public override void UpdateDatabaseBeforeUpdateSchema()
{
    base.UpdateDatabaseBeforeUpdateSchema();

    if (ObjectSpace is DevExpress.ExpressApp.EFCore.EFCoreObjectSpace efCoreObjectSpace
        && efCoreObjectSpace.DbContext.Database.IsNpgsql())
    {
        try
        {
            efCoreObjectSpace.DbContext.Database.ExecuteSqlRaw(
                "CREATE EXTENSION IF NOT EXISTS citext;");
        }
        catch (Npgsql.PostgresException ex) when (ex.SqlState == "42501") // Insufficient Privilege
        {
            // Ignorujemy brak uprawnień. Jeśli rozszerzenie zostało już zainstalowane
            // przez DBA, aplikacja pomyślnie przejdzie do aktualizacji schematu.
        }
    }
}
```

Klauzula `IF NOT EXISTS` zapewnia idempotentność kodu.

**Ważne:** dzięki filtrowi `when (ex.SqlState == "42501")` kod staje się odporny na brak uprawnień superusera na produkcji. Jeśli aplikacja łączy się z uprawnieniami zwykłego użytkownika, a administrator bazy danych (DBA) wdrożył już rozszerzenie ręcznie, program zignoruje ten błąd i przejdzie dalej do wykonywania poleceń DDL.

### 3. Migracja EF Core — zaktualizuj snapshot

Wygeneruj nową migrację. Nie uruchomisz jej bezpośrednio (XAF tego nie robi), ale zaktualizujesz w ten sposób snapshot modelu. Na jego podstawie XAF porówna model z bazą i określi polecenia DDL do wysłania.

```bash
dotnet ef migrations add AddCitextSupport
```

Migracja zawiera:
- `migrationBuilder.AlterDatabase().Annotation("Npgsql:PostgresExtension:citext", ",,")` — rejestrację rozszerzenia w snaphocie,
- `AlterColumn<string>(..., type: "citext", oldType: "text")` — konwersję dla kolumn typu string.

Bez tej operacji snapshot wskaże typ `text`, a XAF nie wyśle polecenia `ALTER COLUMN`.

### 4. Baza — zainstaluj rozszerzenie ręcznie (raz)

Uruchom polecenie jako użytkownik `postgres` (superuser):

```bash
psql -h localhost -U postgres -d MyApp -c "CREATE EXTENSION IF NOT EXISTS citext;"
```

Sprawdź, czy baza zainstalowała rozszerzenie:

```sql
SELECT * FROM pg_extension WHERE extname = 'citext';
-- citext  1.8  zainstalowane w schemacie public
```

### 5. Uruchom aplikację z parametrem `--updateDatabase`

XAF wykryje różnicę między snapshotem (kolumny `citext`) a bazą (kolumny `text`), a następnie wyśle polecenie `ALTER COLUMN ... TYPE citext` dla każdej kolumny:

```bash
dotnet run --project YourApp.Blazor.Server -- --updateDatabase --forceUpdate --silent
```

Zweryfikuj stan po aktualizacji:

```sql
SELECT column_name, udt_name
FROM information_schema.columns
WHERE table_name = 'PermissionPolicyUser'
  AND column_name IN ('UserName', 'StoredPassword');

-- UserName       | citext
-- StoredPassword | text   ← celowe wykluczenie
```

### Podsumowanie kroków wdrożenia citext

| Krok | Plik / Narzędzie | Cel |
|---|---|---|
| Rejestracja `HasPostgresExtension` + pętla | `DbContext.OnModelCreating` | EF Core wygeneruje DDL z typem `citext` zamiast `text` |
| `ExecuteSqlRaw("CREATE EXTENSION...")` | `Updater.UpdateDatabaseBeforeUpdateSchema` | Rozszerzenie powstanie przed wysłaniem DDL przez XAF |
| `dotnet ef migrations add` | Terminal | Aktualizacja snapshotu modelu do typu `citext` |
| `CREATE EXTENSION citext` | psql (jako superuser) | Jednorazowa instalacja rozszerzenia w bazie |
| Uruchomienie z `--updateDatabase --forceUpdate` | Konsola startowa | XAF przekonwertuje kolumny z `text` na `citext` |

Po wdrożeniu PostgreSQL uruchom aplikację i przetestuj:

1. logowanie,
2. otwieranie list danych,
3. otwieranie formularzy szczegółów,
4. zapis nowego rekordu,
5. edycję istniejących rekordów,
6. filtrowanie po datach,
7. wyszukiwanie tekstowe,
8. działanie raportów i dashboardów.

## Co dochodzi przy multi-tenant

Architekturę wielodostępną (multi-tenant) wdróż dopiero wtedy, gdy pojedyncza baza działa stabilnie. W przeciwnym razie diagnozowanie błędów stanie się wyjątkowo trudne.

Po pomyślnej konfiguracji podstawowej migracji musisz dodatkowo zadbać o:

- osobną bazę lub osobny schemat dla każdego tenanta,
- przechowywanie parametrów połączenia poszczególnych tenantów,
- automatyczne zakładanie nowych baz danych,
- uruchamianie migracji na wielu bazach jednocześnie,
- kontrolowanie zgodności schematów.

Opisałem to zagadnienie w osobnym artykule:

[XAF + EF Core + PostgreSQL + multi-tenant](/2026/05/12/xaf-ef-core-postgresql-multitenant.html)
