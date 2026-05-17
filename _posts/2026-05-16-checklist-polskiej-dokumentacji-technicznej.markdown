---
layout: post
title: "Checklist polskiej dokumentacji technicznej"
date: 2026-05-16
categories: technical-writing dokumentacja polska polszczyzna
---

Lista kontrolna do sprawdzania tekstu **przed publikacją**. Uniwersalna dla README, dokumentacji API, release notes, komunikatów błędów i pism do klientów.

Stosuj **w tej kolejności** — najpierw architektura, potem składnia, na końcu słowa. Każdy punkt: odhacz albo wróć i popraw.

---

## A. Architektura tekstu

- [ ] **BLUF** — pierwsze zdanie/akapit odpowiada na pytanie czytelnika
- [ ] **Skanowalność** — mając 10 sekund, odbiorca znajdzie to, czego szuka
- [ ] **Nagłówki co 2-3 akapity** — czytelnik ma „mapę" tekstu
- [ ] **Listy zamiast wyliczeń w zdaniach** — co najmniej 3 elementy → lista
- [ ] **Just-in-time** — żaden akapit nie da się pominąć bez utraty sensu
- [ ] **Top-Down Bridge** — każde nowe pojęcie zakotwiczone w znanym
- [ ] **Maksymalnie 2 nieznane terminy w zdaniu** — i każdy wyjaśniony
- [ ] **Wszystkie skróty rozwinięte przy pierwszym wystąpieniu** (SSO, MFA, JWT itp.)

## B. Składnia

- [ ] **Maksymalnie 20 słów na zdanie** — sprawdź najdłuższe ręcznie
- [ ] **Jedno zdanie = jedna myśl** — bez „i", „oraz", „a także" łączących różne tematy
- [ ] **Strona czynna** — wyszukaj `został*` i przepisz na „my/ja zrobiliśmy"
- [ ] **Bez imiesłowów `-ąc`** — wyszukaj `ąc ` (ze spacją) i przepisz
- [ ] **Bez imiesłowów `-łszy`, `-wszy`** — wyszukaj `łszy`, `wszy`
- [ ] **Bez rzeczowników odczasownikowych w łańcuchach** — żaden „mięsny jeż"
- [ ] **Zdania twierdzące, nie przeczące** — *zapłać w terminie*, nie *nie spóźniaj się*
- [ ] **Bez podwójnej negacji** — *musimy*, nie *nie możemy nie*

## C. Komunikacja osobowa

- [ ] **Używasz „my/ja"** — nie *zaleca się*, *należy*, *zostanie wykonane*
- [ ] **Zwracasz się bezpośrednio** — *Ty* (dokumentacja) / *Pan/Pani* (formalnie)
- [ ] **Bez trzeciej osoby o odbiorcy** — *Ty*, nie *klient*, *użytkownik*, *strona*
- [ ] **Czasowniki w formie osobowej** — *naprawiliśmy*, nie *zostało naprawione*

## D. Słownictwo

- [ ] **Bez kancelaryzmów** — wyrzuć: *aczkolwiek, bowiem, niniejszym, w nawiązaniu do, w przedmiotowej sprawie, na dzień dzisiejszy, w chwili obecnej*
- [ ] **Bez archaizmów** — *iż* → *że*, *posiadać* → *mieć*, *przybyć* → *przyjść*
- [ ] **Bez modnych wyrazów** — *dedykowany* → *przeznaczony*, *implementować* → *wdrażać*, *finalizować* → *kończyć*, *optymalny* → *najlepszy*
- [ ] **Bez kalk z angielskiego** — *adresować problem* → *rozwiązać*, *dedykowane rozwiązanie* → *przeznaczone*
- [ ] **Bez pleonazmów** — *okres czasu* → *czas*, *najbardziej optymalny* → *optymalny*
- [ ] **Konstrukcje analityczne → czasowniki** — *dokonać analizy* → *przeanalizować*

## E. Puste formuły — wyrzuć całkowicie

- [ ] *Pragnę nadmienić / poinformować, że...*
- [ ] *Uprzejmie informuję / wyjaśniam...*
- [ ] *Chciałem zapytać...*
- [ ] *W trosce o najwyższą jakość...*
- [ ] *Wychodząc naprzeciw oczekiwaniom...*
- [ ] *Mam nadzieję, że ten e-mail zastaje...*
- [ ] *Pozostaję do dyspozycji*
- [ ] *Dokładamy wszelkich starań*

Zasada Bralczyka: **nie piszemy o pisaniu, nie mówimy o mówieniu**.

## F. Walidacja narzędziami

- [ ] **[jasnopis.pl](https://jasnopis.pl/)** — wklej tekst, sprawdź klasę trudności
- [ ] Klasa trudności zgodna z celem dla typu dokumentu (tabela niżej)
- [ ] **[logios.pl](http://www.logios.pl/)** — sprawdź indeks FOG-PL (cel: 9-14)
- [ ] **Test 10 sekund** — daj koledze, zegar, zadaj 3 pytania

### Cel klasy trudności Jasnopis

| Typ dokumentu | Cel klasy |
|---|---|
| Komunikat UX dla wszystkich | **2-3** |
| Pismo do klienta, FAQ | **3-4** |
| Dokumentacja użytkownika końcowego | **3-4** |
| Mail biznesowy | **3-4** |
| Release notes dla klientów | **3-4** |
| Dokumentacja API, README dev | **4-5** |
| Whitepaper dla ekspertów | **5-6** |
| Spec techniczny dla architektów | **5-6** |

---

## Dodatkowe punkty per typ dokumentu

### README

- [ ] Sekcja **Wymagania** na początku (czy to dla mnie?)
- [ ] **Quick start** przed pełną dokumentacją
- [ ] **Działające przykłady kodu** — kopiowalne bez modyfikacji
- [ ] Filozofia projektu **NIE** na początku (osobny dokument)
- [ ] **Data ostatniej aktualizacji** w stopce
- [ ] **Sekcja „Znane problemy"** jeśli są

### Dokumentacja API

- [ ] **Schema first** — struktura request/response przed opisem
- [ ] **Wszystkie kody błędów wymienione** — łącznie z 401/403/404/500
- [ ] **`curl` example dla każdego endpointu**
- [ ] **Limit rate, autentykacja, paginacja** w sekcji „Zasady ogólne"
- [ ] **Wersjonowanie API** wyraźnie oznaczone
- [ ] **Zmiany breaking** w osobnej sekcji

### Release notes

- [ ] **Wersja + data wydania** na górze
- [ ] **Trzy sekcje:** Nowości / Poprawki / Breaking changes
- [ ] Każda zmiana **z perspektywy użytkownika**, nie kodu
- [ ] **Breaking changes wyraźnie oznaczone** (kolor / ikona)
- [ ] **Bez wewnętrznych numerów zadania** (JIRA-1234) w opisie

### Komunikaty błędów

- [ ] **Mówi, co zrobić** — nie tylko, co się stało
- [ ] **Bez żargonu technicznego** (jeśli widzi je użytkownik końcowy)
- [ ] **Konkretna informacja** — *Numer telefonu musi mieć 9 cyfr*, nie *Invalid input*
- [ ] **Sugestia działania** — *Sprawdź połączenie i spróbuj ponownie*

### Pismo do klienta

- [ ] **Tytuł pisma + numer sprawy/polisy** na górze
- [ ] **Pierwsza linia: o co chodzi**
- [ ] **Druga linia: co klient ma zrobić**
- [ ] **Podstawa prawna na końcu** lub w przypisie
- [ ] **Forma osobowa** (*wypłaciliśmy*, nie *zostało wypłacone*)

---

## Czerwone flagi — natychmiastowa przeróbka

Tekst do **gruntownej przeróbki** (nie kosmetyki), jeśli choć jedno z poniższych:

- [ ] **Pierwszy akapit nie odpowiada na pytanie „po co to czytam?"**
- [ ] **Średnia długość zdania > 25 słów**
- [ ] **Więcej niż 1 strona bierna na 10 zdań**
- [ ] **Pierwsze zdanie zaczyna się od:** *W nawiązaniu do..., Niniejszym..., Uprzejmie...*
- [ ] **W tekście jest *iż* zamiast *że***
- [ ] **3+ rzeczowniki w dopełniaczu w jednym ciągu** (mięsny jeż)
- [ ] **Najważniejsza informacja jest na końcu, nie na początku**
- [ ] **1000+ słów bez żadnego śródtytułu**

Dwie lub więcej flag — przepisz koniecznie.

---

## Test 10-sekundowy

**Procedura:**

1. Daj swój dokument koledze, który go nie widział
2. Zegar na **10 sekund**
3. Po 10 sekundach zabierz tekst
4. Zapytaj:
   - O czym to jest?
   - Co masz zrobić po lekturze?
   - Kiedy / do kiedy?

| Odpowiedzi precyzyjne | Co zrobić |
|---|---|
| 3 z 3 | **Tekst gotowy** |
| 2 z 3 | Drobne poprawki BLUF |
| 1 z 3 | Wracaj do całej struktury |
| 0 z 3 | Tekst do napisania od nowa |

---

## Quick wins — co zmienić od jutra

1. **Otwórz najstarszy README w repo.** Czy pierwszy akapit odpowiada na „co to jest i czy mi potrzebne"? Jeśli nie — przepisz pierwsze trzy zdania.
2. **Znajdź wszystkie wystąpienia „został" w dokumentacji.** Przepisz na stronę czynną.
3. **Znajdź wszystkie końcówki `-ąc`.** Przepisz każdą na zdanie współrzędne.
4. **Wyrzuć z opisu projektu wyrazy marketingowe** — *innowacyjny*, *dedykowany*, *kluczowy*, *wiodący*.
5. **Sprawdź dokumentację w Jasnopisie.** Klasa 4-5 — OK. Klasa 6-7 — masz co poprawiać.

---

*Bazuje na [Ustandaryzowanych zasadach prostego języka 2024](https://jasnopis.pl/udostepnione/prosty-jezyk/standardy.pdf) (Jasnopis + Fundacja Języka Polskiego + UAM + USz + POLONICUM UW), 6 zasadach „Prosto i kropka" Pracowni Prostej Polszczyzny UWr oraz Encyklopedii prostej polszczyzny PZU (2021).*
