---
layout: post
title: "Jakie testy dodać po przejściu XAF na PostgreSQL"
---

Najczęstszy błąd po przejściu na PostgreSQL wygląda tak: aplikacja startuje, więc wszyscy zakładają, że temat zamknięty. Nie jest.

To, że UI się podniesie, nic jeszcze nie mówi o:

- migracjach
- zapisie danych
- filtrowaniu
- tekstach
- datach

## Od czego zacząć

Najpierw testy najtańsze.

Pierwszy pakiet:

1. konfiguracja
2. połączenie
3. schemat
4. zapis prostych danych

## Testy konfiguracji

Sprawdzasz:

- czy projekt rzeczywiście używa `UseNpgsql(...)`
- skąd bierze connection string
- czy testy, worker i główny host nie mają różnych ustawień
- czy budowanie connection stringa działa tak, jak zakładasz

## Test migracji

Jeżeli używasz migracji EF Core, to masz obowiązek sprawdzić, czy baza daje się postawić od zera.

Tu testujesz:

- pustą bazę
- `database update`
- poprawne utworzenie schematu

## Testy danych

Te rzeczy sprawdzasz obowiązkowo:

- `DateTime`
- `string`
- `decimal`
- `Guid`
- `bool`
- `null`
- wartości domyślne

## Testy filtrowania i wyszukiwania

Tu nie chodzi o to, czy XAF „umie filtrować”. Umie.

Chodzi o to, czy projekt dobrze działa na PostgreSQL przy:

- filtrowaniu po dacie
- wyszukiwaniu po tekście
- porównywaniu `null`
- sortowaniu polskich znaków

## Testy końcowe

Na końcu i tak trzeba przejść po podstawowych przepływach:

1. logowanie
2. otwarcie listy
3. otwarcie formularza
4. zapis nowego rekordu
5. edycję istniejącego
6. raport albo dashboard, jeśli projekt ich używa

## Co dodałem tutaj

W tym repo dodałem najpierw lekkie testy konfiguracji PostgreSQL.

Sprawdzają:

- budowanie stringa połączenia z `FHOST`, `FDATABASE`, `FUSERNAME`, `FPASSWORD`
- pierwszeństwo `ConnectionStrings__ConnectionString`
- budowanie stringa połączenia administracyjnego
- prawdziwe połączenie do lokalnego PostgreSQL

To nie są jeszcze testy całej aplikacji. To jest warstwa podstawowa. Potem dokładamy migracje i dane.

## Dobra kolejność

Rób to tak:

1. konfiguracja
2. połączenie
3. migracje
4. dane
5. filtrowanie
6. końcowe przepływy
