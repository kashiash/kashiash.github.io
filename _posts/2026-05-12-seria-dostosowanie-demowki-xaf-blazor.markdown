---
layout: post
title: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 0
---

**Nie zaczynamy od zera.** Postawienie aplikacji XAF Blazor + EF Core jest krok po kroku opisane w [oficjalnej dokumentacji DevExpress](https://docs.devexpress.com/eXpressAppFramework/) — to jest miejsce, w którym każdy może (i powinien) zacząć. Materiał startowy istnieje, jest aktualizowany i nie ma sensu go duplikować.

Ta seria ciągnie temat dalej. Bierzemy publiczny projekt referencyjny `MainDemo.NET.EFCore` udostępniony przez DevExpress — kompletną aplikację XAF Blazor z EF Core, klientem WinForms i osadzonym Web API — i krok po kroku pokazujemy, **co dochodzi po stronie realnego wdrożenia**. To, czego w aplikacji referencyjnej z definicji nie ma: lokalny branding zamiast brandu DevExpressa, polskie nazwy i komunikaty, zachowania kontrolek dopasowane do operatora, własne edytory, archetypy modelu domenowego, integracje z bazą produkcyjną i moduły, które robią z demonstracji gotowy produkt.

Każdy etap to konkretne pliki, konkretne diffy i konkretne pułapki, których nie widać z poziomu prezentacji. Wszystko publicznie w [`MainDemoEFCoreCustomization`](https://github.com/kashiash/MainDemoEFCoreCustomization) — można otworzyć dowolny commit i powtórzyć tę samą zmianę u siebie.

Ta strona jest **indeksem serii**. Każdy kolejny etap to osobny artykuł.

## Etapy

### 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})

Wielojęzyczność z fallbackiem na `en-US` (świadomie, nie z lenistwa — z powodu raportów CSV). `RequestLocalizationOptions`, `Model.DesignedDiffs.Localization.pl.xafml`, lokalizacja DevExpress reportów przez JSON-y w `wwwroot/js/localization/`. Plus konkretny powód, dla którego `pl-PL` jako domyślny się tu nie sprawdza.

### 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})

Trzy SVG (header, pre-loader, splash), nie jeden. `_Host.cshtml` poprawiony razem z `aria-label` i `og:title`. `site.css` z customowym `#applicationLoadingPanel .loading-floated-circle` (conic-gradient łuk). Theme switcher na `Office White`. Plus update opisujący powtórne przejście tego samego patterna w innym repo — pokazuje, że to się trzyma jako checklista.

### 3. [Globalny `DateTimePropertyEditor` z blokadą kółka myszy, polskimi maskami i opt-outem z modelu]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

W aplikacji biznesowej kółko myszy w polu daty nie jest udogodnieniem — jest źródłem cichych zmian danych. Operator przewija formularz, mija edytor i przy okazji przestawia datę zdarzenia. Rozwiązanie nie polega więc na dorzuceniu pojedynczego edytora z `[EditorAlias]` na wybranych polach, tylko na zmianie domyślnego zachowania całej aplikacji. Edytor zostaje zarejestrowany jako globalny `[PropertyEditor(typeof(DateTime), ..., true)]` dla `DateTime` i `DateTime?`, a indywidualne pola, dla których scroll ma jednak działać (np. wewnętrzne pola serwisowe), są oznaczane atrybutem `[DateEditMouseWheel(false)]`. Domyślne zachowanie i tryb maski siedzą w sekcji `Options` modelu XAF (`IModelOptionsDateEditMouseWheel`), więc cała polityka aplikacji jest deklaratywna i widoczna w Model Editorze, a nie rozproszona po kodzie. Maski są dobierane do typu danych: pole `DateTime` traktowane jako data dostaje `dd.MM.yyyy`, a pole, które ma znaczenie czasu, dostaje `dd.MM.yyyy HH:mm`. JavaScript blokujący scroll wisi w fazie `capture`, identyfikuje edytory po własnej klasie CSS (`fleetman-dateedit-wheel-blocked`/`-allowed`) i ignoruje wewnętrzne klasy DevExpressa, dzięki czemu jest odporny na zmiany wersji DevExpress Blazor.

### 4. [Domknięcie polskiej lokalizacji: klasy, enumy i widoki bez mieszanki PL/EN]({% post_url 2026-05-15-domkniecie-polskiej-lokalizacji-xaf %})

Samo dodanie `pl-PL` nie kończy tematu lokalizacji. W prawdziwym wdrożeniu zostają jeszcze resztki angielskiego w modelu XAF: nazwy widoków, klasy frameworkowe, enumy i pozycje nawigacji. Ten odcinek domyka właśnie tę warstwę i pokazuje, jak doprowadzić model językowy do stanu, w którym użytkownik nie widzi już mieszanki polskiego z angielskim.

### 5. [Dynamiczne reguły wyglądu z bazy w XAF: encja, cache i `AppearanceController`]({% post_url 2026-05-15-dynamiczne-reguly-wygladu-xaf-z-bazy %})

Jeżeli `[Appearance]` zapisany w kodzie to za mało, można potraktować reguły wyglądu jako dane. W tym odcinku do `MainDemo.NET.EFCore` dochodzi encja z regułą, cache procesowy i kontroler, który dokłada reguły z bazy do standardowego pipeline `ConditionalAppearance`. To jest gotowy wzorzec do przeniesienia do osobnego projektu XAF.

### 6. [Obsługa skanów i podglądu PDF w XAF Blazor: dokumenty, upload i preview inline]({% post_url 2026-05-15-obsluga-skanow-i-podgladu-pdf-w-xaf-blazor %})

Do demówki dochodzi pełny, przenośny wzorzec dokumentów: słownik typów, encja dokumentu, zakładka `Załączniki`, upload wielu plików przez `DxUpload`, endpoint zapisujący `FileData` i custom preview dla PDF i obrazów w Blazorze. Plus konkretne poprawki błędów, które wychodzą dopiero przy prawdziwej kompilacji.

## Co łączy te sześć zmian

Każda z nich:

- jest **opt-in** (`isDefaultEditor: false`, `[EditorAlias(...)]`, wybór języka per użytkownik) — nie burzymy demówki dla osób, które chcą zostać przy oryginale,
- siedzi w **konfiguracji aplikacji + jednym custom-pliku**, nie w masowych przeróbkach modelu,
- ma **dokumentację w samym repo** (`docs/*.md`), nie tylko na blogu — bo blog jest publiczny, ale repo zostaje przy projekcie.

## Plan dalszych odcinków serii

Poniżej tematy, które konsekwentnie wracają w projektach XAF Blazor i które chcę przerobić publicznie:

- **Sekcja login/logon**: logon parameters, last logon user, custom validation komunikatów — bo standardowy logon ma kilka miejsc, w których "to jest demo" rzuca się w oczy.
- **Customizacja Nawigacji** — ikony, grupowanie, ukrywanie zbędnych pozycji z modułów referencyjnych XAF-a.
- **Własne filtry i zapisywanie filtrów per użytkownik** — własne filtry pasujące do języka biznesu (a nie do schematu bazy), zapisywane filtry per użytkownik i per rola, szybkie filtry „wczoraj / ten tydzień / moje", FilterController, integracja z ListView.
- **Zapisywanie widoków list: kolejność kolumn, szerokości, sortowanie, grupowanie** — jak XAF trzyma to przez `ModelDifference` (project/role/user), kiedy stosować layout per rola vs per użytkownik, dlaczego defaultowo widoki użytkowników po kilku tygodniach wyglądają jak chaos i jak to ogarnąć.
- **Customizacja list view** poza filtrami i kolumnami — frozen columns, sticky header, batch actions.
- **Definiowanie własnych kolorowań i stylów warunkowych** — atrybut `[Appearance]`, dynamiczne kolorowanie wierszy/komórek/pól w detail view z `IAppearanceEnabled` / `IAppearanceVisibility`, kolory zależne od statusu i progów, custom CSS w Blazorze sterowane modelem, kiedy wybrać atrybut a kiedy controller.
- **Audit Trail w UI** — pokazanie historii zmian rekordu w sposób, który nie wymaga otwierania osobnego widoku.
- **Wymiana standardowych powiadomień XAF** na coś, co nie wygląda jak alert sprzed 15 lat.
- **Archetypy Party / Person / Organization / PartyRole** — klasyczny model z analiz Fowlera. `Party` jako abstrakcja kontrahenta, `Person` i `Organization` jako specjalizacje, `PartyRole` zamiast wciskania ról (klient, dostawca, pracownik, kontakt) w hierarchię klas. W XAF: abstrakcyjna klasa bazowa z `[NonPersistent]`/persistent hybrid, polimorficzne kolekcje, search po wszystkich Party, relacje wielokrotne (ta sama osoba jako klient i jako kontakt u dostawcy). Punkt wyjścia dla każdego CRM i ERP.
- **Archetypy Product / ProductType / ProductItem / ProductCatalog** — druga połowa wzorca z Analysis Patterns: `ProductType` jako definicja katalogowa (np. „rower miejski Romet model X"), `ProductItem` jako konkretny egzemplarz (z numerem seryjnym, gwarancją, lokalizacją), `ProductCatalog` jako kolekcja `ProductType` z wersjonowaniem i ważnością cenową. W XAF: kolekcje z grupowaniem po katalogu, walidacja unikalności SKU per katalog, integracja z `FileAttachments` na zdjęcia/dokumentację, `[Aggregated]` dla wariantów. Bez tego sklep, magazyn ani fakturowanie nawet nie startują.
- **Rzeczy kluczowe dla aplikacji CRM** — kartoteka klienta z całą historią kontaktów w jednym widoku, deduplikacja kontrahentów, leady i pipeline szans, follow-up i przypomnienia z powiązaniem do użytkownika, raportowanie aktywności sprzedaży. Czyli warstwa, od której zaczynają się prawdziwe wdrożenia, a której w demówce nie ma.
- **Prosty obieg dokumentów** — model dokumentu z wersjonowaniem, statusami (`Draft → Review → Approved → Closed`) i przejściami sterowanymi `StateMachine`, akcje XAF z walidacją, audit kto kiedy co zatwierdził, podpięcie powiadomień i historii do `FileAttachments`. Bez BPMN i bez engine'a — to, co pokrywa 80% realnych potrzeb w aplikacji biznesowej.
- **Przejście z bazy SQL Server na PostgreSQL** — wymiana providera EF Core (`Microsoft.EntityFrameworkCore.SqlServer` → `Npgsql.EntityFrameworkCore.PostgreSQL`), connection string, migracje, naming convention (cudzysłowy, lowercase), różnice w typach (`uniqueidentifier` → `uuid`, `datetime2` → `timestamp without time zone`), zachowanie audytu i InMemory-fallbacku w `DemoDbEngineDetectorHelper`. W blogu mam już [punkt startowy XAF + EF Core + PostgreSQL krok po kroku]({% post_url 2026-05-12-xaf-ef-core-postgresql-krok-po-kroku %}) — w serii MainDemo powtórzę to z punktu widzenia konkretnej demówki, czyli z migracjami zachowującymi istniejące dane testowe.
- **Inventory** — magazyn na bazie `ProductItem`: ruchy magazynowe (PZ/WZ/MM/inwentaryzacja), poziomy zapasów per lokalizacja, rezerwacje, partie i daty ważności, FIFO/LIFO/średnia ważona w wycenie, integracja z fakturowaniem przez wspólny `ProductItem`. Stan rzeczywisty liczony, nie tylko bookkeepingowy.
- **Invoicing** — faktury sprzedaży i zakupu, korekty, faktury walutowe, schemat VAT, numeracja per seria/rok, generowanie PDF przez XtraReports, podpięcie do KSeF (osobny temat, ale to repo jest dobrym miejscem żeby pokazać minimalną integrację), powiązanie pozycji z magazynem i kontrahentem z `Party`. Moduł, na którym łatwo poległo wielu autorów własnych aplikacji — pokażę gdzie są pułapki.
- **I co tam jeszcze po drodze okaże się sensowne** — uprawnienia per rekord (XAF criteria operators), import danych z CSV/Excel z walidacją, generowanie ofert i umów z mail-merge przez Office module, dashboardy KPI sprzedażowe na `DevExpress.Dashboards`, scheduled jobs na poziomie aplikacji (np. nocne raporty). Lista nie jest zamknięta — seria rośnie wraz z konkretnymi potrzebami z projektów.

Każdy nowy artykuł dorzucę do tego indeksu i do strony głównej.
