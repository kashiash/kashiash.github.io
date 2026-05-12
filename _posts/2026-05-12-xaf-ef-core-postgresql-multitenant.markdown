---
layout: post
title: "XAF + EF Core + PostgreSQL + multi-tenant"
---

Jeżeli jedna baza na PostgreSQL już działa, dopiero wtedy bierzesz się za multi-tenant. Nie wcześniej.

To jest ten moment, w którym kończy się zwykłe „przełączenie providera”, a zaczyna normalna robota architektoniczna.

Jeżeli jeszcze nie masz dopiętej wersji z jedną zwykłą bazą, najpierw przeczytaj to:

[XAF + EF Core + PostgreSQL krok po kroku](/2026/05/12/xaf-ef-core-postgresql-krok-po-kroku.html)

## Najpierw ustal, jaki multi-tenant w ogóle robisz

Są trzy typowe układy:

- jedna baza, wspólne tabele, `TenantId` w rekordach
- jedna baza na tenant
- osobny schemat na tenant

W XAF + EF Core dla systemu biznesowego najczyściej wychodzi zwykle **osobna baza na tenant**.

## Nie mieszaj problemów

Przy multi-tenant dochodzą naraz cztery osobne tematy:

- jak rozpoznać tenant
- skąd wziąć connection string
- kto zakłada nową bazę
- jak puścić migracje na wielu bazach

## Skąd aplikacja ma wiedzieć, który tenant wybrać

Najczęściej tenant wybierasz po:

- subdomenie
- nazwie klienta w URL
- loginie użytkownika
- nagłówku albo claimie, jeśli to API

Po rozpoznaniu tenant ma być już jedna konkretna odpowiedź:

- identyfikator tenantu
- jego connection string

## Connection stringi tenantów nie mogą siedzieć w kodzie

Connection stringi tenantów trzymasz w:

- centralnej bazie hosta
- bezpiecznej konfiguracji
- vault

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

## `DbContext` musi powstawać per tenant

Normalny wzorzec:

```csharp
services.AddDbContext<MyAppDbContext>((serviceProvider, options) =>
{
    var tenantContext = serviceProvider.GetRequiredService<ITenantContext>();
    options.UseNpgsql(tenantContext.ConnectionString);
});
```

Jeżeli tenant jest rozpoznawany za późno, wszystko zaczyna działać losowo.

## Musisz mieć osobną bazę hosta albo katalog tenantów

Przy modelu „osobna baza na tenant” zwykle potrzebujesz:

- bazy hosta
- tabeli `Tenants`
- wpisu z connection stringiem i statusem tenantu

Bez tego zaczyna się ręczne zarządzanie konfiguracją.

## Zakładanie nowego tenantu to proces

Nowy tenant ma przejść dokładnie przez to:

1. utworzenie bazy
2. nadanie właściciela albo użytkownika
3. dołożenie `citext`
4. puszczenie migracji
5. dopisanie tenantu do katalogu

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

## Migracje na wielu bazach to osobny problem

Na jednej bazie wystarcza:

```powershell
dotnet ef database update
```

Przy multi-tenant musisz przejść po wszystkich aktywnych tenantach i puścić migrację dla każdej bazy osobno.

To znaczy, że potrzebujesz:

- listy tenantów
- skryptu albo joba migracyjnego
- logu, która baza została zaktualizowana

## Nie rób tenant provisioning w zwykłym runtime

Lepszy układ:

- zwykły runtime tylko korzysta z istniejących tenantów
- provisioning tenantu robi osobny proces albo endpoint administracyjny
- migracje wielu baz robi osobny krok operacyjny

## Co trzeba testować przy multi-tenant

Sprawdzasz:

1. czy tenant jest poprawnie rozpoznawany
2. czy tenant dostaje właściwy connection string
3. czy dwa tenanty nie widzą swoich danych
4. czy nowy tenant daje się założyć od zera
5. czy migracje przechodzą po wszystkich tenantach

## Gdzie to się zwykle wykłada

Najczęstsze wtopy:

- tenant rozpoznawany za późno
- zły lifetime `DbContext`
- connection string cache'owany nie tam, gdzie trzeba
- migracje puszczane tylko na jednej bazie
- ręczne zakładanie nowych baz

## Rozsądna kolejność

Rób to tak:

1. dopnij jedną zwykłą bazę PostgreSQL
2. przygotuj katalog tenantów
3. wprowadź resolver tenantu
4. przełącz `DbContext` na connection string per tenant
5. zautomatyzuj zakładanie nowej bazy
6. zautomatyzuj migracje wielu baz
