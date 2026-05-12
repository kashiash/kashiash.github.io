---
layout: post
title: "Jakie testy dodać po przejściu XAF na PostgreSQL"
---

Po przejściu na PostgreSQL nie wystarczy, że aplikacja startuje. Musisz sprawdzić, że naprawdę działa poprawnie.

## 1. Co potwierdzasz testami

Testy mają potwierdzić pięć rzeczy:

1. aplikacja łączy się z PostgreSQL
2. schemat bazy daje się utworzyć albo zaktualizować
3. zapis i odczyt danych działa poprawnie
4. filtrowanie i wyszukiwanie działa poprawnie
5. podstawowe widoki i operacje w aplikacji dalej działają

## 2. Testy konfiguracji

Dodaj testy, które sprawdzają:

- `UseNpgsql(...)`
- źródło connection stringa
- spójność konfiguracji między hostem, testami i dodatkowymi procesami
- budowanie poprawnego connection stringa do PostgreSQL

## 3. Testy migracji

Sprawdź:

- czy pusta baza daje się utworzyć od zera
- czy migracja przechodzi bez ręcznych poprawek
- czy aplikacja działa na nowym schemacie

## 4. Testy danych

Obowiązkowo sprawdź:

- `DateTime`
- `string`
- `decimal`
- `Guid`
- `bool`
- `null`
- wartości domyślne

## 5. Testy filtrowania i wyszukiwania

Sprawdź:

- filtrowanie po dacie
- filtrowanie po tekście
- wyszukiwanie po fragmencie tekstu
- porównywanie `null`
- sortowanie danych z polskimi znakami

## 6. Testy końcowe aplikacji

Na końcu sprawdzasz:

1. logowanie
2. otwarcie listy
3. otwarcie formularza
4. zapis nowego rekordu
5. edycję istniejącego rekordu
6. raporty i dashboardy, jeśli projekt ich używa

## 7. Minimalny sensowny pakiet testów

Jeśli chcesz zacząć rozsądnie, dodaj:

1. test konfiguracji PostgreSQL
2. test budowania connection stringa
3. test migracji albo tworzenia schematu
4. test podstawowego połączenia do lokalnego PostgreSQL
5. test zapisu i odczytu prostych danych

## 8. Co zostało dodane u mnie

W moim projekcie dodałem testy:

- budowania stringa połączenia z `FHOST`, `FDATABASE`, `FUSERNAME`, `FPASSWORD`
- pierwszeństwa `ConnectionStrings__ConnectionString`
- budowania stringa połączenia administracyjnego
- prawdziwego połączenia do lokalnego PostgreSQL

To jest pierwszy poziom testów. Następny krok to migracje i zapis danych.

## 9. Dobra kolejność pracy

Rób testy w tej kolejności:

1. konfiguracja
2. połączenie
3. schemat
4. dane
5. filtrowanie
6. końcowe przepływy użytkownika
