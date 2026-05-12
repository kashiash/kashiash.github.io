---
layout: post
title: "Jak naprawdę testować XAF po przejściu na PostgreSQL"
---

Po zmianie providera bazy bardzo łatwo wpaść w tę samą pułapkę: aplikacja startuje, logowanie działa, więc wszyscy uznają temat za zamknięty.

To jest za mało.

Przy migracji na PostgreSQL najczęściej nie psuje się sam start procesu. Psują się rzeczy bardziej podstępne:

- migracje
- filtry po dacie
- wyszukiwanie po tekście
- zachowanie polskich liter
- testy, które nadal lecą na starej bazie

Dlatego testy po zmianie bazy nie są dodatkiem na koniec. One są częścią samej migracji.

## Od czego zacząć, żeby nie utknąć w chaosie

Nie zaczynaj od ciężkich scenariuszy E2E. Najpierw zrób testy, które szybko odpowiadają na pytanie: czy projekt w ogóle gada z PostgreSQL tak, jak myślisz.

Dobra kolejność wygląda tak:

1. test konfiguracji
2. test połączenia
3. test utworzenia schematu
4. test prostego zapisu i odczytu
5. test wyszukiwania
6. dopiero potem grubsze przepływy aplikacyjne

Jeżeli zaczniesz od końca, to przy pierwszym błędzie nie będziesz wiedział, czy problem siedzi w bazie, modelu, migracjach czy samej aplikacji.

## Pierwszy poziom: sprawdź, czy testujesz właściwy provider

To brzmi banalnie, ale naprawdę często właśnie tutaj wychodzi bałagan.

Masz sprawdzić:

- czy host aplikacji używa `UseNpgsql(...)`
- czy `IDesignTimeDbContextFactory` też używa `UseNpgsql(...)`
- czy testy integracyjne nie mają własnego starego connection stringa
- czy worker albo osobne API nie zostały na SQL Server

Taki test nie musi być rozbudowany. Czasem wystarczy zwykły smoke test konfiguracji albo krótka kontrola kodu:

```csharp
var optionsBuilder = new DbContextOptionsBuilder<MyAppDbContext>();
optionsBuilder.UseNpgsql(connectionString);

using var context = new MyAppDbContext(optionsBuilder.Options);
Assert.Contains("Host=", context.Database.GetConnectionString());
```

To nie zastępuje testów integracyjnych. To po prostu szybko łapie sytuację, w której ktoś poprawił jeden host, a drugi nadal żyje po staremu.

## Drugi poziom: połączenie i prosty round-trip danych

To jest pierwszy test, który daje realną wartość. Nie "czy kod się kompiluje", tylko czy naprawdę:

- da się połączyć z bazą
- da się utworzyć prosty schemat
- da się zapisać dane
- da się je odczytać bez przekłamań

Przykład lekkiego testu smoke:

```csharp
[Fact]
public async Task Can_connect_and_roundtrip_polish_text() {
    await using var scope = await ProviderSmokeDatabaseScope.CreateAsync(TestDatabaseProvider.PostgreSql);

    var record = new ProviderSmokeRecord {
        Id = Guid.NewGuid(),
        SearchText = "Zażółć gęślą jaźń",
        City = "Łódź",
        Amount = 1234.56m,
        OccurredOn = new DateTime(2026, 05, 12, 11, 30, 0, DateTimeKind.Unspecified),
        IsActive = true,
        OptionalNote = "Żaneta lubi Kraków"
    };

    scope.Context.Records.Add(record);
    await scope.Context.SaveChangesAsync();
    scope.Context.ChangeTracker.Clear();

    var loaded = await scope.Context.Records.SingleAsync(x => x.Id == record.Id);

    Assert.Equal("Zażółć gęślą jaźń", loaded.SearchText);
    Assert.Equal("Łódź", loaded.City);
    Assert.Equal(1234.56m, loaded.Amount);
    Assert.True(loaded.IsActive);
}
```

Ten test jest tani, ale mówi bardzo dużo. Od razu widać, czy połączenie działa, czy baza poprawnie przyjmuje polskie znaki i czy podstawowe typy nie rozjeżdżają się po zapisie.

## Trzeci poziom: daty trzeba sprawdzić osobno

Jeżeli coś ma zacząć sprawiać problemy dopiero po przejściu na PostgreSQL, to bardzo często będą to daty.

W XAF zwykle wychodzi to później:

- przy filtrach zapisanych przez użytkownika
- przy listach z kryteriami
- przy porównaniach zakresów dat
- przy polach `DateTime?`

W testach warto wymusić kontrolę już na etapie prostego modelu:

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder) {
    var entity = modelBuilder.Entity<ProviderSmokeRecord>();

    if(Database.IsNpgsql()) {
        entity.Property(x => x.OccurredOn).HasColumnType("timestamp without time zone");
    }
    else if(Database.IsSqlServer()) {
        entity.Property(x => x.OccurredOn).HasColumnType("datetime2");
    }
}
```

Po co to robić w teście? Bo wtedy widzisz, czy Twój model naprawdę zachowuje się tak samo na obu providerach, a nie tylko na jednym szczęśliwym środowisku.

## Czwarty poziom: wyszukiwanie, małe litery, wielkie litery i polskie znaki

To jest miejsce, które użytkownik zauważy bardzo szybko.

Jeżeli w projekcie są polskie dane, to trzeba sprawdzić:

- zapis `Ł`, `Ż`, `Ś`, `Ą`
- wyszukiwanie po fragmencie tekstu
- różnicę między małymi i wielkimi literami

Dobry test nie musi być skomplikowany:

```csharp
[Fact]
public async Task Can_find_record_ignoring_letter_case() {
    await using var scope = await ProviderSmokeDatabaseScope.CreateAsync(TestDatabaseProvider.PostgreSql);

    scope.Context.Records.Add(new ProviderSmokeRecord {
        Id = Guid.NewGuid(),
        SearchText = "ZAŻÓŁĆ GĘŚLĄ JAŹŃ",
        City = "Warszawa",
        Amount = 10m,
        OccurredOn = new DateTime(2026, 05, 12),
        IsActive = true
    });
    await scope.Context.SaveChangesAsync();

    string searchTerm = "zażółć gęślą jaźń";

    var loaded = await scope.Context.Records.SingleAsync(x =>
        x.SearchText.ToLower() == searchTerm.ToLower());

    Assert.Equal("ZAŻÓŁĆ GĘŚLĄ JAŹŃ", loaded.SearchText);
}
```

I drugi, jeszcze bardziej praktyczny:

```csharp
[Fact]
public async Task Can_find_record_by_fragment_with_polish_letters() {
    await using var scope = await ProviderSmokeDatabaseScope.CreateAsync(TestDatabaseProvider.PostgreSql);

    scope.Context.Records.Add(new ProviderSmokeRecord {
        Id = Guid.NewGuid(),
        SearchText = "Żółta Łódź",
        City = "Gdańsk",
        Amount = 1m,
        OccurredOn = new DateTime(2026, 05, 10),
        IsActive = true
    });
    await scope.Context.SaveChangesAsync();

    string fragment = "łÓD";

    var loaded = await scope.Context.Records
        .Where(x => x.SearchText.ToLower().Contains(fragment.ToLower()))
        .SingleAsync();

    Assert.Equal("Żółta Łódź", loaded.SearchText);
}
```

Takie testy są banalne do napisania, a łapią rzeczy, które potem rozwalają normalną pracę użytkownika.

## A co z SQL Server?

To jest ważne wtedy, gdy:

- projekt przechodzi z SQL Server na PostgreSQL
- chcesz porównać zachowanie obu providerów
- chcesz upewnić się, że nie tracisz czegoś po drodze

Nie musisz od razu odpalać całej aplikacji na dwóch bazach. Często wystarczy mały test provider smoke dla obu stron:

```csharp
[Theory]
[InlineData(TestDatabaseProvider.PostgreSql)]
[InlineData(TestDatabaseProvider.SqlServer)]
public async Task Can_connect_and_roundtrip_polish_text(TestDatabaseProvider provider) {
    await using var scope = await ProviderSmokeDatabaseScope.CreateAsync(provider);
    // ...
}
```

To jest bardzo dobry etap przejściowy. Dzięki temu widzisz, czy sama warstwa EF Core i baza zachowują się sensownie po obu stronach, zanim zaczniesz porównywać całe scenariusze aplikacyjne.

## Co dokładnie dołożyliśmy w OutlookInspiredDemo

Tutaj nie kończy się to na teorii. W `OutlookInspiredDemo` zostały dołożone realne testy smoke w pliku:

```text
CS\DataDrive.Module.Tests\DatabaseProviderSmokeTests.cs
```

One sprawdzają cztery rzeczy:

1. czy da się utworzyć testową bazę dla PostgreSQL
2. czy da się utworzyć testową bazę dla SQL Server LocalDB
3. czy zapis i odczyt polskich znaków działa poprawnie
4. czy wyszukiwanie po tekście działa przy różnych wielkościach liter

Przykład testu uruchamianego dla obu providerów:

```csharp
[Theory]
[InlineData(TestDatabaseProvider.PostgreSql)]
[InlineData(TestDatabaseProvider.SqlServer)]
public async Task Can_find_record_by_fragment_with_polish_letters(TestDatabaseProvider provider) {
    await using var scope = await ProviderSmokeDatabaseScope.CreateAsync(provider);

    scope.Context.Records.AddRange(
        new ProviderSmokeRecord {
            Id = Guid.NewGuid(),
            SearchText = "Żółta Łódź",
            City = "Gdańsk",
            Amount = 1m,
            OccurredOn = new DateTime(2026, 05, 10),
            IsActive = true
        },
        new ProviderSmokeRecord {
            Id = Guid.NewGuid(),
            SearchText = "Czarny Kraków",
            City = "Kraków",
            Amount = 2m,
            OccurredOn = new DateTime(2026, 05, 11),
            IsActive = false
        });
    await scope.Context.SaveChangesAsync();
    scope.Context.ChangeTracker.Clear();

    string fragment = "łÓD";

    var loaded = await scope.Context.Records
        .Where(x => x.SearchText.ToLower().Contains(fragment.ToLower()))
        .SingleAsync();

    Assert.Equal("Żółta Łódź", loaded.SearchText);
}
```

To nie jest test idealnego, produkcyjnego wyszukiwania. To jest test bardzo praktyczny: czy po zmianie providera baza nadal przechowuje i zwraca dane tak, żeby użytkownik mógł normalnie pracować na polskich napisach.

### Jak te testy tworzą bazy

Dla PostgreSQL test buduje nową bazę tymczasową, tworzy schemat przez `EnsureCreated()`, a po teście ją usuwa.

Dla SQL Server robi to samo na LocalDB. Dzięki temu:

- test nie zależy od jednej starej bazy developerskiej
- każdy przebieg startuje od czystego stanu
- łatwiej porównać oba providery uczciwie

To podejście jest bardzo wygodne na etapie migracji. Nie trzeba od razu podpinać pełnego środowiska aplikacyjnego, żeby sprawdzić najważniejsze zachowania providerów.

### Jak uruchomić te testy

Najprostsza komenda:

```powershell
dotnet test CS\DataDrive.Module.Tests\DataDrive.Module.Tests.csproj -c Debug
```

Domyślnie testy korzystają z:

- PostgreSQL na `localhost`
- SQL Server LocalDB `MSSQLLocalDB`

Jeżeli chcesz wskazać inne połączenia, możesz ustawić zmienne środowiskowe:

```powershell
$env:DATADRIVE_TESTS_POSTGRES_CONNECTION = "Host=localhost;Port=5432;Database=DataDrive;Username=fleetman;Password=..."
$env:DATADRIVE_TESTS_SQLSERVER_CONNECTION = "Server=(localdb)\MSSQLLocalDB;Database=DataDriveProviderSmoke;Integrated Security=true;TrustServerCertificate=True"
```

To jest ważne, bo testy nie są przywiązane na sztywno do jednej maszyny. Da się je odpalić także w innym środowisku, o ile dostaną poprawny connection string.

## Nie wszystko musi być od razu E2E

To też jest częsty błąd. Ludzie myślą: skoro to aplikacja XAF, to jedyny sensowny test to klikany scenariusz od logowania do zapisu rekordu.

Nie.

Najtańsze i najbardziej użyteczne są zwykle testy pośrodku:

- już nie unit test czystej logiki
- jeszcze nie pełny test UI

Właśnie tam najlepiej sprawdza się:

- połączenie z bazą
- prosty schemat testowy
- round-trip danych
- wyszukiwanie tekstowe
- zachowanie dat

Dopiero później dokładamy:

1. logowanie
2. otwarcie listy
3. otwarcie formularza
4. zapis nowego rekordu
5. edycję istniejącego
6. raport albo dashboard, jeśli projekt ich używa

## Co warto mieć w repo od razu

Jeżeli masz migrowany projekt XAF, to bardzo dobrze mieć w repo trzy warstwy testów:

### 1. lekkie testy konfiguracji

One odpowiadają na pytanie: czy projekt w ogóle jest spięty na dobry provider i dobry connection string.

### 2. testy provider smoke

To jest dokładnie ta warstwa, w której sprawdzasz:

- połączenie
- zapis
- odczyt
- polskie litery
- wyszukiwanie małe i wielkie litery

### 3. testy aplikacyjne

Tu dopiero wchodzą scenariusze XAF:

- logowanie
- widoki
- zapis z formularza
- filtry
- raporty

Jak odwrócisz tę kolejność, to będziesz tracił czas na debugowanie wielkich scenariuszy dla problemów, które powinny zostać złapane w prostym teście bazy.

## Najkrótsza sensowna checklista po migracji

Jeżeli chcesz wiedzieć, czy po przejściu na PostgreSQL jesteś w dobrym miejscu, sprawdź:

1. testy konfiguracji przechodzą
2. projekt potrafi utworzyć schemat na pustej bazie
3. prosty zapis i odczyt działa
4. polskie litery przechodzą bez zniekształceń
5. wyszukiwanie po tekście działa sensownie
6. filtrowanie po datach nie psuje się
7. podstawowy przepływ XAF działa po starcie

To nie jest przesadny pakiet. To jest minimum, po którym można powiedzieć, że migracja naprawdę zaczyna być wiarygodna.
