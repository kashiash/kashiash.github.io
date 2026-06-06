---
layout: post
title: "W której zakładce wstążki ląduje akcja — kategoria kontra nazwa zakładki (XAF Blazor)"
---

Jeżeli chcesz, żeby użytkownik znajdował wszystkie akcje importu w jednej zakładce
paska, musisz ustawić im właściwą kategorię. W trybie wstążki XAF o zakładce
(Home / View / Tools) decyduje kategoria akcji, a nie nazwa zakładki. To dwie różne
rzeczy i łatwo je pomylić.

![Wstążka na liście pojazdów: zakładki Home, View, Tools](/assets/images/xaf-wstazka-home.png)

## Po co to wiedzieć

Akcja importu zadań pojawiła się w innym miejscu paska niż importy pojazdów.
Importy pojazdów były w zakładce Tools, a import zadań — w grupie edycji.
Różnica brała się z jednej wartości w konstruktorze akcji.

Gdy zrozumiesz ten łańcuch, ustawisz przycisk dokładnie tam, gdzie chcesz.

## Trzy poziomy: kategoria → kontener → strona wstążki

Od akcji do zakładki prowadzą trzy poziomy:

1. **Kategoria akcji** — trzeci argument konstruktora. Decyduje, do którego
   kontenera trafia przycisk.
2. **Kontener akcji** — placeholder z przyciskami, np. `Tools` albo `Edit`.
   Kontenery powstają w szablonie aplikacji.
3. **Strona wstążki** — zakładka. Grupuje kontenery. Definiujesz ją w modelu.

Kategorię podajesz tak:

```csharp
var importAction = new PopupWindowShowAction(
    this, "Vehicle.Import", PredefinedCategory.Tools);
```

`PredefinedCategory` to enum z `DevExpress.Persistent.Base`. Gdy podasz `Tools`,
przycisk trafia do kontenera Tools, a ten pokazuje się w zakładce Tools.

## Przykład: przenosimy akcję do zakładki Tools

W aplikacji importy pojazdów, kosztów i klientów używają kategorii `Tools`. Po
kliknięciu zakładki Tools widać wszystkie przyciski importu w jednym miejscu:

![Zakładka Tools z akcjami importu](/assets/images/xaf-wstazka-tools.png)

Przykład z importu pojazdów:

```csharp
// VehicleImportController.cs
_importAction = new PopupWindowShowAction(
    this, $"{Name}.{nameof(_importAction)}", PredefinedCategory.Tools) {
    Caption = "Import pojazdów z Excela",
    ImageName = "Action_Import",
};
```

Akcja „Dodaj zadania testowe" miała kategorię `Edit`, więc trafiała gdzie indziej.
Wystarczyła zmiana kategorii:

```csharp
// SeedTestDataController.cs
_addTasksAction = new SimpleAction(
    this, $"{nameof(AddTestTasksController)}.{nameof(_addTasksAction)}",
    PredefinedCategory.Tools) {           // wcześniej: PredefinedCategory.Edit
    Caption = "Dodaj zadania testowe",
    ImageName = "Action_New",
};
```

Po tej zmianie przycisk jest w zakładce Tools, obok importów. Kategoria to jedyna
różnica — typ akcji i reszta kodu zostają bez zmian.

## Nazwa zakładki to nie kategoria

`Tools` to nazwa **kategorii** (standard XAF). Napis na zakładce to osobna rzecz —
**Caption strony wstążki**. Łatwo je pomylić.

Aplikacja działa w trybie wstążki:

```xml
<!-- Model.xafml -->
<Options UIType="TabbedMDI" FormStyle="Ribbon" />
```

Strony wstążki ustawiasz w modelu: `Action Design → ActionToRibbonMapping`. Każda
strona ma własny Caption i grupuje kontenery. Chcesz, żeby zakładka nazywała się
„Imports"? Nadpisz Caption strony, która pokazuje kontener Tools:

```xml
<!-- Model.xafml -->
<ActionDesign>
  <ActionToRibbonMapping>
    <RibbonPage Id="Tools" Caption="Imports" />
  </ActionToRibbonMapping>
</ActionDesign>
```

Kodu akcji nie ruszasz — kategoria `Tools` zostaje. Zakładka nazywa się teraz Imports,
a w środku ma te same przyciski importu:

![Zakładka przemianowana na Imports z akcjami importu](/assets/images/xaf-wstazka-imports.png)

## Pułapka: własny kontener wymaga własnego szablonu

Może kusić, żeby wpisać własną kategorię, np. `Category = "Imports"`, i liczyć na
nową zakładkę. To nie zadziała. Kontenery powstają w szablonie aplikacji, nie z
samej kategorii. Jeśli kategoria nie ma kontenera, XAF umieszcza akcję w `Unspecified`.

Osobna zakładka „Imports" **obok** „Tools" wymaga więc własnego kontenera, a ten —
własnego szablonu Blazora. To duża zmiana w powłoce aplikacji. Jeśli w „Tools"
masz dziś same importy, taniej jest przemianować stronę „Tools" na „Imports"
w modelu.

Jeden kontener nie rozdzieli się na dwie zakładki. Albo przemianowujesz stronę,
albo budujesz własny kontener.

## Jakie kategorie masz pod ręką

Do układania zakładek służą gotowe kategorie z `PredefinedCategory`:

- tworzenie i zapis: `ObjectsCreation`, `Save`, `SaveOptions`
- edycja: `Edit`, `RecordEdit`, `UndoRedo`
- nawigacja i widok: `RecordsNavigation`, `Close`, `View`, `OpenObject`
- dane: `Reports`, `Export`, `Print`
- wyszukiwanie: `Search`, `FullTextSearch`, `Filters`
- narzędzia: `Tools`
- bez kategorii: `Unspecified`

Każdą z nich możesz wydzielić na osobną zakładkę w modelu, bez pisania kodu.
Własną nazwę zakładki podasz w Caption. Własny kontener z nową nazwą kategorii —
dopiero przez własny szablon.

## Źródła

- Action Containers — `docs.devexpress.com/eXpressAppFramework/112610`
- Ribbon w XAF Blazor — `docs.devexpress.com/eXpressAppFramework/405643`
