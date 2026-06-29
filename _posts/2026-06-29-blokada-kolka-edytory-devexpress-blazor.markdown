---
layout: post
title: "Wyłącz kółko myszy i strzałki w edytorach DevExpress Blazor (v26.1)"
description: "Od DevExpress 26.1 zablokujesz kółko myszy i strzałki w edytorach dat, liczb, masek i czasu jednym ustawieniem AllowMouseWheel — w czystym Blazorze, w gridzie i w XAF. Bez JavaScriptu."
categories: xaf blazor
---

![Blokada kółka w edytorach DevExpress Blazor](/assets/images/blokada-kolka-edytory.png)

Edytory DevExpress reagują na kółko myszy: kiedy kursor jest nad polem, obrót kółka zmienia wartość zamiast przewinąć stronę. Dotyczy to pól dat, liczb, masek i czasu. W aplikacji biznesowej to cichy błąd — operator przewija długi formularz, mija pole i przestawia wartość, bez kliknięcia i bez ostrzeżenia. Od DevExpress 26.1 wyłączasz to jednym ustawieniem: `AllowMouseWheel`. Ten wpis pokazuje jak — w czystym Blazorze, w gridzie i w XAF.

Wcześniej trzeba było pisać własny guard w JavaScripcie. To podejście zostawiłem w [osobnym wpisie]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %}) jako wersję sprzed 26.1.

## Kiedy kółko zmienia wartość

Najpierw warto wiedzieć, gdzie problem w ogóle występuje — bo nie dotyczy każdego pola. Kółko zmienia wartość, gdy pole ma fokus albo kursor jest nad nim, a użytkownik kręci kółkiem. To samo robią strzałki góra/dół.

Reagują na to cztery edytory:

- `DxSpinEdit<T>` — pola liczbowe,
- `DxMaskedInput<T>` — pola z maską (np. waluta),
- `DxDateEdit<T>` — pola dat, **gdy mają maskę**,
- `DxTimeEdit<T>` — pola czasu, **gdy mają maskę**.

Dla dat i czasu jest haczyk: natywna blokada działa tylko przy włączonej masce. Bez maski edytor nie reaguje na kółko, więc nie ma czego blokować.

## Dwie właściwości (v26.1)

DevExpress 26.1 dodał do tych edytorów dwie właściwości — dzięki nim wyłączysz przypadkowe zmiany bez ani linijki JavaScriptu.

- `AllowMouseWheel` — gdy `false`, kółko nie zmienia wartości,
- `AllowUpDownArrowKeys` — gdy `false`, nie zmieniają jej też strzałki góra/dół.

Obie domyślnie są `true`. Masz je na każdym z czterech edytorów i w jego wariancie dla grida (`*Settings`):

| Edytor | Komponent | Ustawienia w gridzie |
| --- | --- | --- |
| Liczby | `DxSpinEdit<T>` | `DxSpinEditSettings` |
| Maska | `DxMaskedInput<T>` | `DxMaskedInputSettings` |
| Data | `DxDateEdit<T>` | `DxDateEditSettings` |
| Czas | `DxTimeEdit<T>` | `DxTimeEditSettings` |

## Czysty Blazor: w znaczniku

Jeśli sam dodajesz edytor w `.razor`, ustawiasz właściwość wprost w znaczniku — to najkrótsza droga.

```razor
<DxSpinEdit @bind-Value="@Quantity"
            AllowMouseWheel="false"
            AllowUpDownArrowKeys="false" />

<DxMaskedInput @bind-Value="@Salary"
               Mask="@NumericMask.Currency"
               AllowMouseWheel="false" />

<DxDateEdit @bind-Date="@HireDate"
            Mask="@DateTimeMask.ShortDate"
            AllowMouseWheel="false"
            AllowUpDownArrowKeys="false" />

<DxTimeEdit @bind-Time="@StartTime"
            Mask="@DateTimeMask.ShortTime"
            AllowMouseWheel="false"
            AllowUpDownArrowKeys="false" />
```

## W gridzie: ustawienia kolumny

W gridzie nie masz dostępu do samego edytora — konfigurujesz go przez `*Settings` w `EditSettings` kolumny. Tu blokadę wpinasz dla pól, w których wpisuje się dane ręcznie.

```razor
<DxGrid Data="@products" EditMode="GridEditMode.EditRow">
    <Columns>
        <DxGridDataColumn FieldName="UnitPrice" DisplayFormat="c">
            <EditSettings>
                <DxSpinEditSettings AllowMouseWheel="false" />
            </EditSettings>
        </DxGridDataColumn>
        <DxGridDataColumn FieldName="HireDate">
            <EditSettings>
                <DxDateEditSettings Mask="@DateTimeMask.ShortDate" AllowMouseWheel="false" />
            </EditSettings>
        </DxGridDataColumn>
    </Columns>
</DxGrid>
```

Gdy musisz zmienić to w trakcie działania, sięgasz po ustawienia kolumny przez `GetColumnEditSettings` — między `BeginUpdate` i `EndUpdate`:

```csharp
var settings = grid.GetColumnEditSettings<ISpinEditSettings>("UnitPrice");
grid.BeginUpdate();
settings.AllowMouseWheel = false;
grid.EndUpdate();
```

## W XAF: jednym kontrolerem dla całej aplikacji

W XAF nie ustawiasz edytorów ręcznie — generuje je framework. Żeby zablokować kółko wszędzie, dopisz jeden kontroler. Zyskujesz spójne pola w całej aplikacji, bez dotykania pojedynczych widoków.

XAF wystawia kontrolkę edytora przez jego *component model*: dla liczb to `DxSpinEditModel<T>` (w `NumericPropertyEditor`), dla dat `DxDateEditModel<T>` (w `DateTimePropertyEditor`). Obie mają `AllowMouseWheel`. Metoda `View.CustomizeViewItemControl` daje do nich dostęp:

```csharp
using DevExpress.ExpressApp;
using DevExpress.ExpressApp.Blazor.Editors;

public class DisableMouseWheelController : ViewController<DetailView> {
    protected override void OnActivated() {
        base.OnActivated();

        View.CustomizeViewItemControl<NumericPropertyEditor>(this, editor => {
            editor.ComponentModel.AllowMouseWheel = false;
            editor.ComponentModel.AllowUpDownArrowKeys = false;
        });

        View.CustomizeViewItemControl<DateTimePropertyEditor>(this, editor => {
            editor.ComponentModel.AllowMouseWheel = false;
            editor.ComponentModel.AllowUpDownArrowKeys = false;
        });
    }
}
```

Dla pól dat pamiętaj o masce: ustaw `EditMask` na właściwości (np. `[ModelDefault("EditMask", "dd.MM.yyyy")]`), inaczej natywna blokada nie ma na czym działać.

## W XAF: wyjątek dla pojedynczego pola

Czasem na jednym polu chcesz kółko zostawić — np. data urodzenia, gdzie szybkie cofnięcie o lata bywa wygodne. Taki wyjątek robisz na podstawie modelu pola, bez ruszania reszty.

`CustomizeViewItemControl` daje w callbacku `editor.Model`, więc możesz sprawdzić atrybut na właściwości i pominąć pole:

```csharp
View.CustomizeViewItemControl<DateTimePropertyEditor>(this, editor => {
    if (KeepMouseWheel(editor.Model)) return;   // pole z wyjątkiem — zostaw
    editor.ComponentModel.AllowMouseWheel = false;
    editor.ComponentModel.AllowUpDownArrowKeys = false;
});
```

`KeepMouseWheel` zwraca `true` dla pól oznaczonych własnym atrybutem — na nich kółko zostaje. Atrybut i metoda:

```csharp
[AttributeUsage(AttributeTargets.Property)]
public sealed class KeepMouseWheelAttribute : Attribute { }

static bool KeepMouseWheel(IModelMemberViewItem model) =>
    model?.ModelMember?.MemberInfo?.FindAttribute<KeepMouseWheelAttribute>() != null;
```

Atrybutem oznaczasz właściwość, na której kółko ma działać:

```csharp
[KeepMouseWheel]
public virtual DateTime Birthday { get; set; }
```

## Wcześniej: ręczny guard w JavaScripcie

Przed 26.1 tej właściwości nie było. Blokadę robiło się przez kontroler, który doczytywał moduł JavaScript łapiący zdarzenie kółka, plus klasy CSS na polach. Działało, ale to dużo ruchomych części.

Opisałem to podejście w osobnym wpisie: [Globalny DateEditor w XAF Blazor — guard w JavaScripcie]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %}). Zostaw je tylko, gdy siedzisz na wersji starszej niż 26.1.

## Podsumowanie

Od DevExpress 26.1 blokada kółka to jedna właściwość: `AllowMouseWheel = false` (plus `AllowUpDownArrowKeys` na strzałki). Masz ją na czterech edytorach — liczby, maski, daty i czas — w czystym Blazorze, w gridzie i w XAF. W XAF jeden kontroler z `CustomizeViewItemControl` załatwia całą aplikację, a wyjątek dla pojedynczego pola robisz z modelu. JavaScript zostaje już tylko w historii.
