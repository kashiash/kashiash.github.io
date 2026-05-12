---
layout: post
title: "Wyłączenie scrolla na DxDateEdit w XAF Blazor — z opt-outem w Model Editorze"
series: "Dostosowanie demówki XAF Blazor do własnych potrzeb"
series_part: 3
---

> **Część 3 serii: Dostosowanie demówki XAF Blazor do własnych potrzeb**
>
> Bierzemy publiczne `MainDemo.NET.EFCore` od DevExpressa i przerabiamy je krok po kroku tak, żeby wyglądało i działało jak nasza własna aplikacja, nie demówka.
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. **Custom DateEditor z parametrem modelowym do blokady kółka myszy** — ten wpis

W DevExpress Blazor `DxDateEdit` ma zachowanie, którego ludzie się nie spodziewają. Klikasz w sekcję daty, kręcisz kółkiem myszy i wartość się zmienia. Niby dobra ergonomia — w praktyce katastrofa, jak operator przewija formularz w dół i przy okazji przekręci datę pacjenta o trzy miesiące. Trzeba to wyłączyć. I trzeba to wyłączyć tak, żeby w niektórych miejscach jednak działało, bo czasem to faktycznie wygodne.

Robiłem to dwa razy. Pierwszy raz w HIS bez opt-outa — w całej aplikacji blokada twardo wycięta. Drugi raz w MainDemo, świadomie dodając przełącznik widoczny w Model Editor XAF-a. Ten drugi wariant opisuję poniżej.

## Co musi się zadziać

Trzy rzeczy razem:

1. Mask `dd.MM.yyyy`. Polski format daty, fixed-width, mask sekcyjna.
2. `MaskCaretMode.Advancing`. Kursor po wbiciu sekcji sam przeskakuje do następnej. Bez tego operator co dwie cyfry musi `Tab`-ować.
3. Blokada kółka myszy. Tylko tam, gdzie chcemy.

Robię to przez custom property editora XAF, marker CSS i jeden listener JS w fazie `capture`. Nic więcej.

## Dlaczego nie samym JS-em po klasach DevExpressa

Pierwsza próba w MainDemo wyglądała tak:

```javascript
document.addEventListener('wheel', function (e) {
    if (e.target.closest('.dxbl-dateedit, .dxbl-timeedit')) {
        e.preventDefault();
    }
}, { passive: false });
```

Nie zadziałało. Trzy rzeczy poszły nie tak naraz:

- DevExpress łapie `wheel` w fazie `capture`. Mój listener w fazie `bubble` przyszedł po czasie. Naprawa: `{ capture: true }`.
- DevExpress prawdopodobnie sam robi `stopPropagation`, więc ten sam listener w fazie capture na `document` też mógł nie dojść. Dorzucenie `e.stopImmediatePropagation()` żeby zatrzymać też równoległe listenery.
- Klasy DevExpress (`dxbl-*`) zmieniają się między majorami. Selektor zbyt specyficzny do biblioteki, na której nie chcę polegać. Lepiej dorzucić **własny marker** do roota kontrolki i celować w niego.

Działająca wersja:

```javascript
(function () {
    document.addEventListener('wheel', function (e) {
        var t = e.target;
        if (t && typeof t.closest === 'function' && t.closest('.maindemo-wheel-blocked')) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
})();
```

Wymagania bez których to nie chodzi:

- `capture: true` — odbieramy zdarzenie przed DevExpressem.
- `passive: false` — bez tego `preventDefault` jest ignorowane na wheel-u w nowoczesnych przeglądarkach.
- `stopImmediatePropagation()` — zatrzymujemy listenery na tym samym elemencie.
- `t.closest('.maindemo-wheel-blocked')` — własna klasa, dodawana tylko z poziomu naszego custom editora.

## Custom property editor z parametrem modelu

Drugi krok to napisanie editora, który **sam decyduje**, czy doczepić marker, na podstawie Application Model.

Najpierw stałe i interfejs:

```csharp
public static class CustomEditorAliases {
    public const string DateEditor = "DateEditor";
    public const string DateEditorNullable = "DateEditorNullable";
    public const string MouseWheelBlockerCssClass = "maindemo-wheel-blocked";
}

public interface IModelMemberViewItemMouseWheel : IModelMemberViewItem {
    [Category("Behavior")]
    [Description("When true, scrolling the mouse wheel inside this date editor will not change the value.")]
    [DefaultValue(true)]
    bool BlockMouseWheel { get; set; }
}
```

`IModelMemberViewItemMouseWheel` rozszerza `IModelMemberViewItem`. XAF, jak go zarejestrujemy, doda do każdego `ViewItem`-a w Application Model property `BlockMouseWheel` w sekcji `Behavior`, domyślnie `True`.

Sam editor:

```csharp
[PropertyEditor(typeof(DateTime?), CustomEditorAliases.DateEditorNullable, false)]
public class DateEditorNullable(Type objectType, IModelMemberViewItem model)
    : DateTimePropertyEditor(objectType, model)
{
    protected override void OnControlCreated() {
        base.OnControlCreated();
        if (Control is DxDateEditModel<DateTime?> adapter) {
            DxDateEditMaskProperties.DateTime.CaretMode = MaskCaretMode.Advancing;
            DxDateEditMaskProperties.DateOnly.CaretMode = MaskCaretMode.Advancing;
            DxDateEditMaskProperties.DateTimeOffset.CaretMode = MaskCaretMode.Advancing;

            adapter.Format = "dd.MM.yyyy";
            adapter.DisplayFormat = "dd.MM.yyyy";
            adapter.Mask = "dd.MM.yyyy";
            ApplyMouseWheelBlocker(adapter);
        }
    }

    void ApplyMouseWheelBlocker<T>(DxDateEditModel<T> adapter) {
        if (Model is IModelMemberViewItemMouseWheel m && !m.BlockMouseWheel) {
            return;
        }
        adapter.CssClass = string.IsNullOrEmpty(adapter.CssClass)
            ? CustomEditorAliases.MouseWheelBlockerCssClass
            : adapter.CssClass + " " + CustomEditorAliases.MouseWheelBlockerCssClass;
    }
}
```

Trzy świadome decyzje w tym kodzie:

1. **`isDefaultEditor: false`** w `[PropertyEditor]`. Edytor jest dostępny, ale nie nadpisuje globalnego `DateTimePropertyEditor` dla wszystkich `DateTime?` w aplikacji. Włącza się przez `[EditorAlias]` na pojedynczych polach. Mniejsza skala ataku.

2. **`DxDateEditMaskProperties.*` w `OnControlCreated`**. To są globalne statyczne flagi w DevExpress Blazor. Ustawienie ich tu jest **redundantne** (wystarczyłoby raz w `Program.cs`), ale daje gwarancję, że jak ktoś dorzuci nowy projekt referencjujący ten editor, pattern siedzi w jednym miejscu i nie trzeba szukać dlaczego dwa Tab-y zamiast skoku.

3. **`adapter.CssClass`** zamiast renderowania własnego wrappera. DevExpress XAF Blazor adapter `DxDateEditModel<T>` propaguje `CssClass` do roota komponentu Blazor. Marker siedzi tam, gdzie powinien — bez wrappera, który by zaśmiecał DOM.

`ApplyMouseWheelBlocker` czyta `Model` jako `IModelMemberViewItemMouseWheel`. Jeśli ktoś w Model Editorze ustawi `BlockMouseWheel = False`, klasa nie zostanie dorzucona. Default w interfejsie to `true`, więc zachowanie bez konfiguracji = blokada włączona.

## Rejestracja interfejsu w BlazorModule

Sam interfejs to za mało. XAF musi wiedzieć, że ma go doczepić do `IModelMemberViewItem`-a w runtime:

```csharp
public override void ExtendModelInterfaces(ModelInterfaceExtenders extenders) {
    base.ExtendModelInterfaces(extenders);
    extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
}
```

To idzie w klasie modułu Blazora (u mnie `MainDemoBlazorModule : ModuleBase`). Bez tego property `BlockMouseWheel` nie pojawia się w Model Editorze, choć kod kompiluje się i edytor działa z hardcodowanym defaultem.

## Włączenie editora na konkretnym polu

`[EditorAlias]` na klasie biznesowej:

```csharp
[EditorAlias("DateEditorNullable")]
public virtual DateTime? DueDate { get; set; }

[EditorAlias("DateEditorNullable")]
public virtual DateTime? StartDate { get; set; }
```

Wszystkie trzy daty w `DemoTask` w MainDemo dostały ten alias. Też `Employee.Birthday`.

## Jak operator/developer wyłącza blokadę dla jednego pola

Tylko Model Editor. Zero kodu.

```
Application Model
└── Views
    └── DemoTask_DetailView
        └── Items
            └── DueDate
                BlockMouseWheel = False
```

Po reload-zie aplikacji to konkretne pole znów reaguje na scroll. Reszta dat dalej zablokowana.

Konfiguracja siedzi w `Model.xafml` (project-wide) albo w `Model.User.xafml` (per-user) — zależnie z którego poziomu Model Editora wchodzimy. To jest dokładnie ten poziom konfiguracji, na którym takie rzeczy powinny żyć: zachowanie UI, włączane/wyłączane bez deploymentu nowej wersji.

## Co bym powtórzył, gdybym to robił trzeci raz

- **Trzymać `MaskCaretMode = Advancing` w `Program.cs`, nie w `OnControlCreated`**. Globalna flaga w globalnym miejscu. W repo zostawiłem jak w HIS, ale to jest dług techniczny.
- **Nie pchać `[PropertyEditor(..., true)]`**. Defaultowy editor dla całego typu kusi, bo nie trzeba `[EditorAlias]`, ale w praktyce każdy nieprzemyślany `DateTime` w jakimś NPE czy raporcie też dostanie ten format i tę blokadę. Lepiej opt-in.
- **Nazwa klasy CSS prefiksowana projektem** (`maindemo-`, `his-`, cokolwiek). DevExpress dorzuca własne klasy `dxbl-*` do roota — nasza klasa nie może z nimi kolidować ani nie powinna wyglądać generycznie. `wheel-blocked` byłoby zbyt szerokie, gdyby ktoś dorzucił drugą bibliotekę.

## Gdzie to siedzi w repo

[`MainDemoEFCoreCustomization` → `docs/custom-date-editor-mouse-wheel.md`](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/docs/custom-date-editor-mouse-wheel.md) — pełna lista plików, pułapki, fragmenty before/after każdej zmiany.
