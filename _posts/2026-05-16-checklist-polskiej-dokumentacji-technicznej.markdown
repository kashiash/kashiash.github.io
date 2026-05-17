---
layout: post
title: "Polski technical writing — jak pisać dokumentację, którą ktoś rzeczywiście przeczyta"
date: 2026-05-16
categories: technical-writing dokumentacja polska polszczyzna
description: "Praktyczny przewodnik po pisaniu polskiej dokumentacji technicznej w prostym języku. Zasady, przykłady, narzędzia — wszystko z perspektywy developera."
tags: [polski, technical-writing, dokumentacja, prosta-polszczyzna, software-development]
slug: polski-technical-writing-prosta-polszczyzna
author: Jacek
---

# Polski technical writing — jak pisać dokumentację, którą ktoś rzeczywiście przeczyta

**Większość polskiej dokumentacji technicznej to ściana tekstu, której nikt nie czyta.** README zaczynają się od trzech akapitów filozofii, komentarze w kodzie powtarzają oczywistości, a release notes brzmią jak zażalenia urzędowe. Wszystko po polsku, wszystko gramatycznie, wszystko bezużyteczne.

Ten artykuł pokazuje, jak to naprawić. **Polski standard „prosty język"** istnieje od 2010 roku, w październiku 2024 doczekał się oficjalnej standaryzacji ([Ustandaryzowane zasady prostego języka](https://jasnopis.pl/udostepnione/prosty-jezyk/standardy.pdf)) — ale w branży IT prawie nikt go nie zna. Szkoda, bo zasady są proste i dają natychmiastowy efekt.

Dostaniesz tutaj:

- **trzy poziomy** poprawiania tekstu (architektura → składnia → słownictwo),
- **siedem konkretnych zasad** z przykładami z prawdziwego kodu i dokumentacji,
- **narzędzia** do automatycznej walidacji,
- **listę szybkich zmian** — co wdrożyć w swoich dokumentach od jutra.

---

## Dlaczego warto

Trzy konkretne powody dla developera:

**1. Czytelnik szuka odpowiedzi, nie literatury.** Wpada do Twojej dokumentacji z Google'a albo Slacka. Ma 30 sekund. Jeśli w tym czasie nie znajdzie tego, czego szuka, otwiera następną kartę. Nie wybacza, nie wraca.

**2. Dług dokumentacyjny jest realny.** Każde pytanie „a czy mogę zapytać, jak to działa?" od kolegi z zespołu to koszt — Twojego czasu i jego cierpliwości. Im lepiej napisana dokumentacja, tym mniej pytań. Prosta matematyka.

**3. Branża IT w Polsce dojrzeje.** Coraz więcej firm — banki, ubezpieczyciele, sektor publiczny — wymaga prostego języka od dostawców. Od 28 czerwca 2025 r. obowiązuje wymóg poziomu B2 w skali CEFR dla komunikacji banków. Wcześniej czy później dotrze to do branży SaaS.

Dobra wiadomość: nauczyć się pisać prostym językiem **zajmuje dwa wieczory**. Stosować — kilka miesięcy świadomej praktyki.

---

## Trzy poziomy poprawiania tekstu

Każdy tekst można poprawiać na trzech poziomach. Najlepszy efekt daje praca w tej kolejności.

### Poziom 1: Architektura

**Jak ułożone są informacje.** Czy najważniejsze jest na początku? Czy każda sekcja działa samodzielnie? Czy czytelnik może przerwać po pierwszym akapicie i nadal wiedzieć, o co chodzi?

### Poziom 2: Składnia

**Jak zbudowane są zdania.** Czy są krótkie? Strona czynna czy bierna? Czy używasz imiesłowów `-ąc` i rzeczowników odczasownikowych?

### Poziom 3: Słownictwo

**Jakie słowa wybierasz.** Czy zamiast „dedykowany" piszesz „przeznaczony"? Czy unikasz kancelaryzmów typu „aczkolwiek", „bowiem", „w nawiązaniu do"?

**Klucz:** zaczynaj od poziomu 1. Zła architektura zabija tekst niezależnie od jakości zdań. Świetne zdania nie uratują tekstu, w którym wniosek jest na końcu.

---

## Siedem zasad — z przykładami

### Zasada 1: BLUF — wniosek na początku

**Bottom Line Up Front.** Pierwsze zdanie odpowiada na pytanie czytelnika. Reszta to uzasadnienie.

To jest **najważniejsza zmiana**, jaką możesz zrobić w swoich tekstach.

#### Release notes — porównanie

❌ **Źle:**

> Po wielu tygodniach intensywnych prac, w odpowiedzi na sugestie naszych klientów oraz w wyniku analizy zgłoszonych incydentów, zespół deweloperski podjął decyzję o przeprowadzeniu zmian w mechanizmie autoryzacji w module FleetManager. Wynika to z potrzeby zwiększenia bezpieczeństwa oraz konieczności dostosowania się do wymogów regulacyjnych obowiązujących klientów z sektora publicznego.

✅ **Dobrze:**

> **W wersji 4.2 zmieniamy logowanie z hasła na SSO.** Stare hasła przestają działać 30 listopada. Konfiguracja w sekcji „Co musisz zrobić" niżej.

Pierwsze trzy słowa odpowiadają na pytanie „co się zmienia". Następne — „kiedy". Trzecie — „co mam zrobić". Reszta dokumentu może zawierać szczegóły, ale podstawową odpowiedź mamy w 25 słowach.

#### Pull request description — porównanie

❌ **Źle:**

> Ten PR zawiera szereg zmian, które zostały wprowadzone w celu refaktoryzacji modułu autoryzacji, w odpowiedzi na potrzeby zgłoszone w ramach ostatniego sprint review oraz w nawiązaniu do dyskusji odbytej na kanale #architecture.

✅ **Dobrze:**

> **Wydzielam logikę autoryzacji z `UserService` do nowego `AuthService`.** Powód: `UserService` urósł do 800 linii i robi za dużo. Zmiana umożliwia testowanie autoryzacji bez stubowania całego usera.

### Zasada 2: Kropka miłości

**Maksymalnie 20 słów na zdanie.** Jeśli zdanie ma 25+, znajdź najbliższy spójnik (*i*, *oraz*, *ponieważ*, *który*, *co*, *że*) i postaw tam kropkę.

Reguła nadrzędna: **jedno zdanie = jedna myśl**.

#### Dokumentacja API — porównanie

❌ **Źle** (37 słów):

> Endpoint `/api/v2/vehicles/{id}/telemetry` zwraca dane telemetryczne pojazdu z ostatnich 24 godzin, agregowane co 5 minut, z wyłączeniem okresów gdy pojazd był zaparkowany, chyba że parametr `include_idle=true`, w którym to przypadku zwracane są również okresy postoju.

✅ **Dobrze:**

> Endpoint `/api/v2/vehicles/{id}/telemetry` zwraca dane telemetryczne pojazdu z ostatnich 24 godzin. Dane są agregowane co 5 minut. Domyślnie pomijamy okresy postoju. Aby je dołączyć, ustaw `include_idle=true`.

Cztery zdania, każde z jedną myślą. Czytelnik może przerwać po dowolnym i zrozumieć, do czego doszedł.

### Zasada 3: Strona czynna, nie bierna

Polski lubi stronę bierną w pismach urzędowych — i ten nawyk przeniósł się do dokumentacji IT. Wyrzuć go.

| ❌ Strona bierna | ✅ Strona czynna |
|---|---|
| Pakiet został zainstalowany | Zainstalowaliśmy pakiet |
| Konfiguracja została zmieniona | Zmieniliśmy konfigurację |
| Wszystkie dane zostały zarchiwizowane | Zarchiwizowaliśmy wszystkie dane |
| Plik manifestu jest analizowany przez system | System analizuje plik manifestu |
| Twój wniosek zostanie rozpatrzony | Rozpatrzymy Twój wniosek |

**Test prosty:** wyszukaj (Ctrl+F) w dokumencie końcówki `został*`, `została*`, `zostało*`, `zostały*`. Jeśli jest ich więcej niż 1 na 10 zdań — przepisz.

Wyjątek: strona bierna jest OK, kiedy nie znamy wykonawcy lub nie jest istotny:

> ✅ *Hasła są szyfrowane algorytmem bcrypt.*
> ✅ *Endpoint jest dostępny pod adresem `/api/v2`.*

### Zasada 4: Imiesłowy `-ąc` — wyrzuć

Trzecia gramatyczna pułapka: konstrukcje typu *Konfigurując X, należy pamiętać o Y*. Brzmi mądrze, czyta się fatalnie.

#### W dokumentacji

❌ **Źle:**

> Konfigurując ten parametr, należy pamiętać o zrestartowaniu serwisu.

✅ **Dobrze:**

> Po skonfigurowaniu tego parametru zrestartuj serwis.

❌ **Źle:**

> Wykonując kopię zapasową, zwróć uwagę na rozmiar dysku.

✅ **Dobrze:**

> Przed wykonaniem kopii zapasowej sprawdź rozmiar dysku.

**Test prosty:** wyszukaj końcówki `-ąc`, `-łszy`, `-wszy`. Każde wystąpienie — kandydat do przepisania.

### Zasada 5: Komunikacja osobowa, nie bezosobowa

Pisz **„my/ja"** zamiast form bezosobowych typu *zaleca się*, *należy*, *zostanie wykonane*. Zwracaj się bezpośrednio do czytelnika: *Ty* (w dokumentacji technicznej), *Pan/Pani* (w korespondencji formalnej).

| ❌ Bezosobowo | ✅ Osobowo |
|---|---|
| Zaleca się sprawdzenie ustawień | Zalecamy sprawdzić ustawienia |
| Należy złożyć wniosek | Złóż wniosek / Proszę złożyć wniosek |
| Dokonano przeglądu danych | Przejrzeliśmy dane |
| Klient zobowiązany jest do zapłaty | Zapłać w terminie 14 dni |
| Użytkownik powinien aktywować konto | Aktywuj konto |

To zmienia ton dokumentacji z urzędowego na pomocny. Wbrew pozorom: **mniej formalnie znaczy bardziej profesjonalnie**.

### Zasada 6: Top-Down Bridge — od znanego do nowego

**Każde nowe pojęcie zakotwicz w czymś znanym.** Nigdy nie wprowadzaj dwóch nieznanych rzeczy w jednym zdaniu.

#### Dokumentacja architektury — porównanie

❌ **Źle:**

> Wdrażamy CQRS z event sourcingiem na Marten i Wolverine.

Pięć nieznanych terminów w jednym zdaniu. Czytelnik, który zna tylko jeden, zatrzymuje się i googluje pozostałe cztery. Jeden zostawia stronę, dwóch wraca do Slacka po pomoc.

✅ **Dobrze:**

> Zmieniamy sposób zapisu danych. Zamiast nadpisywać stan w bazie, będziemy zapisywać każdą zmianę jako osobne zdarzenie — to wzorzec **event sourcing**. Do obsługi użyjemy biblioteki **Marten**, opartej na PostgreSQL, który już mamy.

Cztery nieznane pojęcia, ale każde zakotwiczone w znanym kontekście. Czytelnik schodzi warstwami.

Ta sama reguła działa wewnątrz zdania: **na początku znane, na końcu nowe**.

❌ *Aktualizacja modułu Hangfire do wersji 1.8.5 została wykonana wczoraj.*
✅ *Wczoraj zaktualizowaliśmy moduł Hangfire — przeszliśmy na wersję 1.8.5.*

### Zasada 7: Wyrzuć puste formuły

Te zwroty nie wnoszą nic poza długością tekstu. Wyrzuć je **całkowicie**, nie zastępuj niczym.

- *Pragnę nadmienić, że...*
- *Uprzejmie informuję, że...*
- *Chciałbym zapytać...*
- *W trosce o najwyższą jakość naszych usług...*
- *Wychodząc naprzeciw oczekiwaniom naszych klientów...*
- *Dokładamy wszelkich starań...*
- *Mam nadzieję, że ten e-mail zastaje Pana w dobrym zdrowiu*
- *Pozostaję do dyspozycji*

Zasada Bralczyka: **nie piszemy o pisaniu, nie mówimy o mówieniu**. Czytelnik wie, że piszesz. Po prostu napisz, co masz do napisania.

**Plus lista modnych wyrazów do wyrzucenia z dokumentacji IT:**

| ❌ Modne | ✅ Naturalne |
|---|---|
| dedykowany | przeznaczony |
| implementować | wdrażać |
| finalizować | kończyć |
| inicjować | zaczynać |
| funkcjonować | działać |
| optymalny | najlepszy |
| dokonać analizy | przeanalizować |
| podjąć decyzję | zdecydować |
| ulec modyfikacji | zmienić się |
| posiadać | mieć |

---

## Specyfika: dokumentacja IT a inne typy

Reguły są te same. Akcenty są różne.

### README projektu

- **Szybki start przed pełną dokumentacją.** Twój czytelnik szuka najkrótszej drogi do działającego rozwiązania.
- **Sekcja „Wymagania" na początku.** Odbiorca musi szybko wiedzieć, czy ten projekt jest dla niego.
- **Działające przykłady kodu.** Kopiowalne bez modyfikacji.
- **Bez filozofii projektu na początku.** Wrzuć ją do osobnego dokumentu `docs/philosophy.md`.

### Dokumentacja API

- **Struktura przed opisem** — czytelnik chce najpierw zobaczyć schemat request/response, opis za tym.
- **Wszystkie kody błędów wymienione** — łącznie z tymi, które wydają się oczywiste.
- **`curl` example dla każdego endpointu.** Programista skopiuje i sprawdzi w 5 sekund.
- **Limit rate, autentykacja, paginacja — w sekcji „Zasady ogólne"**, nie w każdym endpoincie.

### Release notes

- **Z perspektywy użytkownika, nie z perspektywy kodu.** „Naprawiliśmy bug w klasie `InvoiceProcessor`" jest dla developera. „Faktury z kwotą zero nie generują już błędu" jest dla użytkownika.
- **Trzy sekcje:** Nowości / Poprawki / Breaking changes.
- **Breaking changes wyraźnie oznaczone** — osobnym kolorem lub ikoną.
- **Bez wewnętrznego numeru taska.** „Naprawiliśmy JIRA-1234" nikomu poza Tobą nic nie mówi.

### Komunikaty błędów

To też dokumentacja — najmniejsza i najczęściej czytana. Każdy komunikat powinien **mówić, co zrobić**, nie tylko, co się stało.

❌ *Connection refused.*
✅ *Nie udało się połączyć z serwerem. Sprawdź, czy serwis działa: `systemctl status fleetmanager`.*

❌ *Invalid input.*
✅ *Numer telefonu musi mieć 9 cyfr bez spacji. Wpisałeś: `+48 123 456 789`.*

❌ *Operation failed.*
✅ *Nie udało się zapisać. Sprawdź połączenie z bazą i spróbuj ponownie.*

---

## Narzędzia

Trzy narzędzia, które warto znać.

**[jasnopis.pl](https://jasnopis.pl/)** — wkleić tekst, dostać klasę trudności w skali 1-7. Dla dokumentacji technicznej cel: klasa 4-5. Dla pism do klientów: klasa 3-4.

**[logios.pl](http://www.logios.pl/)** — indeks mglistości FOG-PL. Liczba lat edukacji potrzebnych do zrozumienia tekstu. Cel dla tekstów technicznych: 9-14.

**[Ustandaryzowane zasady prostego języka 2024](https://jasnopis.pl/udostepnione/prosty-jezyk/standardy.pdf)** — oficjalny standard, jednostronicowy PDF. Współautorzy: Jasnopis, Fundacja Języka Polskiego, UAM, USz, POLONICUM UW.

Plus dwie rzeczy dla pogłębienia:

- **[Vlog „Prosto i kropka"](https://www.funduszeeuropejskie.gov.pl/strony/o-funduszach/promocja/prosto-o-funduszach-europejskich-1/vlog-prosto-i-kropka/)** — 10 odcinków po kilka minut, dr hab. Tomasz Piekot. Najlepszy darmowy materiał edukacyjny o prostym języku w Polsce.
- **[Encyklopedia prostej polszczyzny PZU](https://www.pzu.pl/grupa-pzu/o-nas/prosty-jezyk)** — 424 strony, słownik korpomowy, zasady dobrej komunikacji.

---

## Co zmienić od jutra

Pięć rzeczy, które możesz wdrożyć w swojej dokumentacji **w pół godziny**:

**1. Otwórz najstarszy README w swoim repo.** Przeczytaj pierwszy akapit. Czy odpowiada na pytanie „co to jest i czy mi to potrzebne"? Jeśli nie — przepisz pierwsze trzy zdania.

**2. Znajdź wszystkie wystąpienia „został" w dokumentacji.** Przepisz na stronę czynną.

**3. Znajdź wszystkie wystąpienia kończące się na `-ąc`.** Przepisz każde na zdanie współrzędne.

**4. Wyrzuć z opisu projektu zwroty marketingowe.** „Innowacyjny", „dedykowany", „kluczowy", „wiodący". Jeśli zostanie pustka po wyrzuceniu — masz problem głębszy niż językowy.

**5. Sprawdź dokumentację w Jasnopisie.** Jeśli wychodzi klasa 6 lub 7 — masz na czym popracować. Klasa 4-5 — jesteś OK.

---

## Test rzeczywisty: 10 sekund

Najlepszy test: daj swój dokument koledze, którego dziedzina nie pokrywa się z tematem. Zegar na 10 sekund. Po 10 sekundach zabierz tekst i zapytaj:

- O czym to jest?
- Co masz zrobić po lekturze?
- Kiedy / do kiedy?

Jeśli odpowiedzi są precyzyjne — tekst gotowy. Jeśli mgliste — wracaj do BLUF.

---

## Posłowie

Pisanie w prostym języku jest jak refaktoring kodu — łatwo zrozumieć zasady, trudno wyrobić sobie nawyk. Po pierwszych przepisaniach możesz mieć poczucie, że tracisz „profesjonalny ton". To złudzenie. **Prosty język brzmi profesjonalnie u kogoś, kto wie, co chce powiedzieć.** Skomplikowany — u kogoś, kto stara się, żeby tego nie było widać.

Po roku świadomej praktyki piszesz inaczej. Po dwóch — czytasz swoje stare teksty i łapiesz się za głowę. Po trzech — koledzy zaczynają Cię pytać, jak to robisz.

Powodzenia. I — ważne — **nie piszemy o pisaniu, nie mówimy o mówieniu**. Wracaj do swojego README.

---

*Źródła: [Ustandaryzowane zasady prostego języka 2024](https://jasnopis.pl/udostepnione/prosty-jezyk/standardy.pdf) · [Pracownia Prostej Polszczyzny UWr](https://prostapolszczyzna.uwr.edu.pl/) · [Encyklopedia prostej polszczyzny PZU](https://www.pzu.pl/grupa-pzu/o-nas/prosty-jezyk) · [„10 zasad prostej polszczyzny" — My Company Polska](https://mycompanypolska.pl/artykul/10-zasad-prostej-polszczyzny/16380)*

---

## Checklist — lista kontrolna przed publikacją

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

*Bazuje na [Ustandaryzowanych zasadach prostego języka 2024](https://jasnopis.pl/udostepnione/prosty-jezyk/standardy.pdf) (Jasnopis + Fundacja Języka Polskiego + UAM + USz + POLONICUM UW), 6 zasadach „Prosto i kropka" Pracowni Prostej Polszczyzny UWr oraz Encyklopedii prostej polszczyzny PZU (2021).*
