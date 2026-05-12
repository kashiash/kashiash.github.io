---
layout: post
title: "XAF + EF Core + PostgreSQL + multi-tenant"
---

Jeżeli jedna baza na PostgreSQL już działa, dopiero wtedy bierzesz się za multi-tenant. Nie wcześniej.

To jest ten moment, w którym kończy się zwykłe „przełączenie providera”, a zaczyna normalna robota architektoniczna.

Najpierw odpowiedz sobie uczciwie na jedno pytanie: po co ci w ogóle multi-tenant.

To ma sens wtedy, gdy:

- jedna aplikacja ma obsługiwać wiele niezależnych firm
- każda firma ma mieć swoje dane odcięte od pozostałych
- chcesz wdrażać jeden kod, ale obsługiwać wielu klientów
- chcesz łatwo założyć nową firmę bez stawiania osobnej aplikacji od zera

Przykład prosty. Masz system dla wypożyczalni, warsztatów albo sieci biur. Klient `Acme` ma swoje auta, swoje dokumenty, swoich użytkowników. Klient `Contoso` ma swoje. Obie firmy używają tej samej aplikacji, ale nie mogą widzieć swoich danych nawzajem.

To właśnie jest normalny przypadek dla multi-tenant.

To nie ma sensu wtedy, gdy:

- masz jedną firmę i jedną bazę
- każdy klient i tak dostaje osobną instancję aplikacji
- różnice między klientami są tak duże, że kończysz z osobnym kodem albo osobnymi modułami
- nie masz procesu zakładania nowej firmy, migracji i utrzymania wielu baz

Jeżeli masz dziś dwóch klientów i dla każdego stawiasz osobny serwer, osobny deploy i osobną bazę, to jeszcze nie jest multi-tenant. To są po prostu dwie osobne instalacje.

Multi-tenant opłaca się wtedy, gdy zyskujesz na wspólnym kodzie i wspólnym utrzymaniu, ale nie mieszasz danych klientów. Nie opłaca się wtedy, gdy dokładasz sobie skomplikowanie, a realnie nie obsługujesz wielu firm z jednego systemu.

Jeżeli jeszcze nie masz dopiętej wersji z jedną zwykłą bazą, najpierw przeczytaj to:

[XAF + EF Core + PostgreSQL krok po kroku](/2026/05/12/xaf-ef-core-postgresql-krok-po-kroku.html)

## Najpierw ustal, jaki multi-tenant w ogóle robisz

Technicznie są trzy warianty:

- jedna baza, wspólne tabele, `TenantId` w rekordach
- jedna baza na tenant
- osobny schemat na tenant

W XAF + EF Core dla normalnej aplikacji biznesowej bierzesz **osobną bazę na firmę**. To jest wariant, pod który DevExpress naprawdę to układa.

## Nie mieszaj problemów

Przy jednej bazie sprawa jest prosta: aplikacja łączy się w jedno miejsce i działa. Przy multi-tenant to się kończy.

Teraz musisz osobno ustalić cztery rzeczy. Jak aplikacja poznaje, do której firmy wchodzi użytkownik. Skąd bierze adres do bazy tej firmy. Kto zakłada nową bazę dla nowej firmy. I kto później aktualizuje wszystkie bazy, kiedy zmienisz model albo dodasz migrację.

Przykład z życia. Dzisiaj dochodzi nowy klient `Acme`. Ktoś musi:

1. dopisać `Acme` do bazy hosta
2. założyć bazę `MyApp_Acme`
3. puścić na niej migracje
4. sprawić, żeby `jan@acme` albo `acme.twojaaplikacja.pl` trafiało właśnie do tej bazy

Jeżeli to nie jest rozdzielone, tylko „jakoś zrobi się przy starcie”, to później zaczyna się chaos.

## Skąd aplikacja ma wiedzieć, do której firmy wejść

W praktyce masz kilka normalnych wariantów:

- firma ma własny adres, na przykład `acme.twojaaplikacja.pl`
- użytkownik loguje się loginem z nazwą firmy, na przykład `jan@acme`
- administrator hosta wybiera firmę z listy i otwiera jej panel
- API dostaje identyfikator firmy w nagłówku albo w claimie tokena

Po rozpoznaniu ma wyjść jedna konkretna rzecz:

- identyfikator firmy
- connection string do jej bazy

Przykład pierwszy:

- `acme.twojaaplikacja.pl` -> baza `MyApp_Acme`
- `contoso.twojaaplikacja.pl` -> baza `MyApp_Contoso`

Przykład drugi:

- `jan@acme` -> baza `MyApp_Acme`
- `anna@contoso` -> baza `MyApp_Contoso`

Jeżeli po zalogowaniu dalej nie wiesz, z którą bazą pracujesz, to multi-tenant nie jest jeszcze gotowy.

## Connection stringi tenantów nie mogą siedzieć w kodzie

Adresy do baz trzymasz w jednym kontrolowanym miejscu:

- centralnej bazie hosta
- ustawieniach środowiska
- menedżerze sekretów, jeśli go używasz

Minimalny model wygląda tak:

```csharp
public sealed class TenantInfo
{
    public string Key { get; init; } = null!;
    public string Name { get; init; } = null!;
    public string ConnectionString { get; init; } = null!;
    public bool Active { get; init; }
}
```

## W XAF masz dwa światy: host i tenant

Masz:

- **Host UI** - panel do zarządzania listą firm
- **Tenant UI** - właściwą aplikację konkretnej firmy

Host widzi listę tenantów, może ich założyć, włączyć, wyłączyć, zmienić dane połączenia.

Tenant pracuje tylko na swojej bazie, swoich użytkownikach, swoich rolach i swoich danych.

To oznacza dwie osobne bazy:

- **Host Database** - lista tenantów, ustawienia wspólne, obiekty współdzielone jeśli naprawdę ich potrzebujesz
- **Tenant Database** - dane jednej konkretnej firmy

Tego nie mieszasz. Host i tenant nie mogą używać tego samego connection stringa.

## `DbContext` musi powstawać osobno dla każdej firmy

To jest proste. Jeśli firma `Acme` ma inną bazę niż `Contoso`, to `DbContext` nie może być zbudowany raz na sztywno dla wszystkich.

Robisz to w `scoped`, na podstawie rozpoznanej firmy:

```csharp
services.AddDbContext<MyAppDbContext>((serviceProvider, options) =>
{
    var tenantContext = serviceProvider.GetRequiredService<ITenantContext>();
    options.UseNpgsql(tenantContext.ConnectionString);
});
```

Jeżeli najpierw tworzysz `DbContext`, a dopiero potem próbujesz ustalić firmę, to jedziesz w ciemno.

## Musisz mieć osobną bazę hosta

Przy modelu „osobna baza na tenant” potrzebujesz:

- bazy hosta
- tabeli `Tenants`
- wpisu z connection stringiem i statusem tenantu

Bez tego zaczyna się ręczne zarządzanie konfiguracją.

## Założenie nowej firmy musi być procedurą

Nowy klient ma przejść dokładnie przez to:

1. utworzenie bazy
2. nadanie właściciela albo użytkownika
3. dołożenie `citext`
4. puszczenie migracji
5. dopisanie firmy do bazy hosta

Przykład:

```sql
CREATE DATABASE "MyApp_TenantA" OWNER myapp;
```

Potem:

```sql
CREATE EXTENSION IF NOT EXISTS citext;
```

I dopiero potem:

```powershell
dotnet ef database update
```

## XAF ma tu jeszcze kilka twardych zasad

Z dokumentacji DevExpress wynikają trzy rzeczy:

- jedna baza tenantowa nie może przechowywać danych kilku różnych firm
- baza hosta nie może być jednocześnie bazą któregoś tenantu
- każdy tenant musi mieć własny, unikalny connection string

Jeżeli ktoś próbuje zrobić jedną wspólną bazę dla hosta i jednej firmy, to robi to źle.

## Migracje na wielu bazach to osobny problem

Na jednej bazie wystarcza:

```powershell
dotnet ef database update
```

Przy wielu firmach musisz przejść po wszystkich aktywnych firmach i puścić migrację dla każdej bazy osobno.

W praktyce robisz to tak:

1. pobierasz listę aktywnych firm z bazy hosta
2. bierzesz connection string każdej firmy
3. odpalasz migrację na tej konkretnej bazie
4. zapisujesz, gdzie poszło dobrze, a gdzie się wywaliło

Przy EF Core nowa baza ma już być gotowa przed pierwszym logowaniem użytkownika.

## Nie wkładaj zakładania nowych firm do zwykłego startu aplikacji

Lepszy układ:

- zwykły runtime tylko korzysta z istniejących firm
- założenie nowej firmy robi osobny proces, ekran administracyjny albo narzędzie
- migracje wielu baz robi osobny krok operacyjny

## Co trzeba testować przy multi-tenant

Sprawdzasz:

1. czy tenant jest poprawnie rozpoznawany
2. czy tenant dostaje właściwy connection string
3. czy dwa tenanty nie widzą swoich danych
4. czy nowy tenant daje się założyć od zera
5. czy migracje przechodzą po wszystkich tenantach
6. czy użytkownik hosta widzi listę firm
7. czy zwykły użytkownik firmy nie widzi panelu hosta

## Gdzie to się zwykle wykłada

Najczęstsze wtopy:

- tenant rozpoznawany za późno
- zły lifetime `DbContext`
- connection string cache'owany nie tam, gdzie trzeba
- migracje puszczane tylko na jednej bazie
- ręczne zakładanie nowych baz
- host i tenant na tej samej bazie

## Rozsądna kolejność

Rób to tak:

1. dopnij jedną zwykłą bazę PostgreSQL
2. przygotuj katalog tenantów
3. wprowadź resolver tenantu
4. przełącz `DbContext` na connection string per tenant
5. zautomatyzuj zakładanie nowej bazy
6. zautomatyzuj migracje wielu baz
