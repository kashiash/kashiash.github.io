---
layout: post
title: "Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 3
---

> **Część 3 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> Nie tworzymy aplikacji od zera — postawienie projektu XAF Blazor + EF Core jest krok po kroku opisane w [oficjalnej dokumentacji DevExpress](https://docs.devexpress.com/eXpressAppFramework/) i to jest miejsce, w którym każdy może (i powinien) zacząć. My ciągniemy ten temat dalej: bierzemy publiczny projekt referencyjny `MainDemo.NET.EFCore` i pokazujemy, co dochodzi w nim po stronie realnego wdrożenia.
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. **Globalny `DateTimePropertyEditor` z blokadą kółka myszy** — ten wpis

W XAF Blazor standardowy edytor daty bazuje na `DxDateEdit`. Ten komponent ma wygodne, ale ryzykowne zachowanie: gdy fokus jest w polu daty, kółko myszy potrafi zmienić wartość. Operator przewija formularz, a przy okazji przestawia termin, datę urodzenia albo godzinę zdarzenia.

W aplikacji biznesowej to nie jest detal UX. To jest ryzyko cichej zmiany danych.

## Po co to wszystko

Chcemy uzyskać cztery rzeczy:

1. Edytor ma być domyślny globalnie dla `DateTime` i `DateTime?`, bez dokładania `[EditorAlias]` na każdej właściwości.
2. Scroll myszą ma być domyślnie zablokowany wewnątrz edytora daty.
3. Blokadę scrolla musi dać się wyłączyć dla pojedynczego pola, ale tak, żeby decyzja była widoczna w kodzie albo w Model Editorze.
4. Edytor nie może narzucać jednej maski. Jeśli pole ma maskę daty, pokazuje datę. Jeśli maska zawiera godzinę, pozwala edytować datę i czas.

Drugi temat to `MaskCaretMode`. DevExpress domyślnie ma `Static` (kursor stoi w sekcji aż przerzucisz Tab/strzałką). `Advancing` skacze do następnej sekcji, jak skończysz wpisywać poprzednią. Dla maski `dd.MM.yyyy` przy `Static` operator co dwa znaki musi `Tab`-ować — wolimy `Advancing`.

Te dwa fixy chodzą zawsze razem.

## Wersja minimalna — wszystko na sztywno

Jeśli akceptujemy, że scroll będzie zablokowany **wszędzie** i caret mode ma być **zawsze** `Advancing`, bez żadnej możliwości wyjątku per pole, do celu wystarczą dwa pliki: `ViewController` po stronie C# i blok `<script>` w `_Host.cshtml`. Bez własnego property editora, bez atrybutu, bez `ExtendModelInterfaces`.

### Krok 1: kontroler doczepiający klasę CSS i ustawiający caret mode

```csharp
using DevExpress.Blazor;
using DevExpress.ExpressApp;
using DevExpress.ExpressApp.Blazor.Components.Models;
using DevExpress.ExpressApp.Blazor.Editors;
using DevExpress.ExpressApp.Blazor.Editors.Adapters;
using DevExpress.ExpressApp.Editors;

namespace MainDemo.Blazor.Server.Controllers;

public class GlobalDateEditorTweaksController : ViewController<DetailView>
{
    protected override void OnViewControlsCreated()
    {
        base.OnViewControlsCreated();
        foreach (var item in View.Items.OfType<DateTimePropertyEditor>())
        {
            item.DxDateEditMaskProperties.DateTime.CaretMode = MaskCaretMode.Advancing;
            item.DxDateEditMaskProperties.DateOnly.CaretMode = MaskCaretMode.Advancing;
            item.DxDateEditMaskProperties.DateTimeOffset.CaretMode = MaskCaretMode.Advancing;

            Type t = item.MemberInfo.MemberType;
            if (t == typeof(DateTime) && item.Control is DxDateEditModel<DateTime> a1)
            {
                AppendCss(a1);
            }
            else if (t == typeof(DateTime?) && item.Control is DxDateEditModel<DateTime?> a2)
            {
                AppendCss(a2);
            }
        }
    }

    static void AppendCss<T>(DxDateEditModel<T> adapter)
    {
        const string cls = "fleetman-dateedit-wheel-blocked";
        adapter.CssClass = string.IsNullOrEmpty(adapter.CssClass) ? cls : adapter.CssClass + " " + cls;
        adapter.InputCssClass = string.IsNullOrEmpty(adapter.InputCssClass) ? cls : adapter.InputCssClass + " " + cls;
    }
}
```

XAF rejestruje ten kontroler automatycznie — nie ma `AddTransient`, `services.Add` ani innego wpisu w DI. Na każdym `DetailView` iterujemy po `DateTimePropertyEditor`-ach, dla każdego z nich ustawiamy `CaretMode = Advancing` przez property `DxDateEditMaskProperties` (jest dziedziczona z `DateTimePropertyEditor`, dostępna przez instancję editora) i doczepiamy stałą klasę CSS do `CssClass` oraz `InputCssClass` adaptera.

### Krok 2: globalny listener `wheel` w `_Host.cshtml`

Po `_framework/blazor.server.js`:

```html
<script>
(function () {
    document.addEventListener('wheel', function (e) {
        var t = e.target;
        if (t && typeof t.closest === 'function' && t.closest('.fleetman-dateedit-wheel-blocked')) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
})();
</script>
```

Trzy szczegóły są kluczowe:

- `capture: true` — listener łapie zdarzenie **przed** DevExpressem, w fazie capture. Bez tego DevExpress dostaje wheel pierwszy i zmienia wartość zanim my zdążymy `preventDefault`.
- `passive: false` — nowoczesne przeglądarki domyślnie traktują `wheel` jako passive, w którym `preventDefault()` jest cicho ignorowane. Trzeba jawnie wymusić non-passive.
- `stopImmediatePropagation()` — zatrzymuje też inne listenery na tym samym elemencie.

Selektor `.fleetman-dateedit-wheel-blocked` celuje wyłącznie w naszą klasę, więc działa niezależnie od wewnętrznych klas DevExpressa (`dxbl-dateedit` i pochodne), które zmieniają się między wersjami.

### Czego ta wersja nie daje

- **Nie ma wyjątków per pole.** Jeśli jedno pole ma scrollować — np. data urodzenia, gdzie wygodniej cofnąć rok kółkiem — musimy zmienić kod kontrolera. Nie ma deklaratywnego mechanizmu opt-out.
- **Nie ma wyjątków per widok.** Jeden kontroler dla wszystkich `DetailView`.
- **Nie ma konfiguracji bez recompile.** Admin nie wpłynie na zachowanie inaczej niż przez nowy build i deploy.
- **Nie obsługuje maski.** Wszystkie pola dostają domyślne ustawienia DevExpressa — pole z `DisplayFormat="dd.MM.yyyy HH:mm"` nie pokaże sekcji czasu, jeśli DevExpress tego nie zrobił sam.
- **`ListView` (grid inline edit) nie jest pokryty**, bo kontroler jest `ViewController<DetailView>`. Dla grida trzeba dorobić analogiczny albo zmienić bazę na samo `ViewController` i obsłużyć oba typy widoków.

Dla projektu demo z jedną domeną to wystarczy. Dla aplikacji, w której pojedyncze pola wymagają wyjątku, admin ma móc zmienić zachowanie bez rebuilda, a maski są mieszane (daty + daty z czasem), przechodzimy na wersję pełną.

## Co dorzucić, żeby zarządzać tym z Model Editora

Każdy z poniższych elementów rozwiązuje jeden konkretny problem wersji minimalnej. Można je wprowadzać iteracyjnie — niekoniecznie wszystkie naraz.

1. **Custom `DateTimePropertyEditor` dla `DateTime` i `DateTime?` z `isDefaultEditor: true`** — dwie klasy, bo XAF property editory są typo-specyficzne. Powód: property editor ma własne `Model` (`IModelMemberViewItem`), do którego XAF dorzuca property widoczne w Model Editor. Generyczny `ViewController` nie ma „własnego Model" i jego konfiguracja nie pojawia się w Model Editorze.
2. **Atrybut `[DateEditMouseWheel(false)]`** na property w business objectcie. Powód: są pola, gdzie decyzja „scroll OK / scroll blokuje" należy do modelu domenowego, nie do xafml.
3. **Interfejs `IModelMemberViewItemMouseWheel`** z nullable `BlockMouseWheel`. Powód: w Model Editor każdy `MemberViewItem` dostaje nowe property — pole może być scrollowalne w jednym widoku, zablokowane w drugim.
4. **Interfejs `IModelOptionsDateEditMouseWheel`** z `BlockDateEditMouseWheelByDefault` i `DateEditMaskCaretMode`. Powód: globalna wartość domyślna zapisana w `Model.xafml`, zmiana bez recompile.
5. **`ExtendModelInterfaces` w module Blazor**. Powód: bez tego XAF Model Editor nie pokaże nowych property — interfejsy istnieją, ale nie są zaczepione do bazowych `IModelMemberViewItem` / `IModelOptions`.
6. **Konfigurator z kaskadą trzech poziomów** (atrybut → ViewItem → IModelOptions). Powód: logika decyzji w jednym miejscu, jednoznaczna kolejność precedencji.
7. **Wykrywanie sekcji czasu z formatu**. Powód: pole z `DisplayFormat="dd.MM.yyyy HH:mm"` powinno mieć widoczną sekcję czasu; pole z `dd.MM.yyyy` — nie.
8. **Dwie klasy CSS (`-blocked` i `-allowed`)**. Powód: opt-out per pole działa tak, że pole „dozwolone" dostaje klasę `-allowed`, a JS guard widząc tę klasę robi `return` przed sprawdzeniem `-blocked`.
9. **JS jako moduł ESM ładowany przez kontroler XAF**. Powód: pozbywamy się hardcoded `<script>` w `_Host.cshtml` i mamy gwarancję, że listener nie jest rejestrowany dwa razy.

Reszta artykułu rozwija każdy z tych punktów.

## Globalny przełącznik w Options

Główna decyzja nie powinna siedzieć na każdym polu osobno. Domyślne zachowanie dla całej aplikacji trzymam w `Application > Options`, a wyjątki ustawiam na konkretnych polach albo widokach.

```csharp
public static class CustomEditorAliases
{
    public const string DateTimeEditor = "CustomDateTimeEditor";
    public const string MouseWheelBlockerCssClass = "fleetman-dateedit-wheel-blocked";
    public const string MouseWheelAllowedCssClass = "fleetman-dateedit-wheel-allowed";
}

[AttributeUsage(AttributeTargets.Property)]
public sealed class DateEditMouseWheelAttribute(bool blockMouseWheel) : Attribute
{
    public bool BlockMouseWheel { get; } = blockMouseWheel;
}

public interface IModelOptionsDateEditMouseWheel
{
    [Category("Behavior")]
    [Description("Globalne ustawienie domyslne. Gdy True, przewijanie kolkiem myszy wewnatrz edytorow daty nie zmienia wartosci.")]
    [DefaultValue(true)]
    bool BlockDateEditMouseWheelByDefault { get; set; }

    [Category("Behavior")]
    [Description("Globalny tryb przesuwania kursora w maskach edytorow daty.")]
    [DefaultValue(MaskCaretMode.Advancing)]
    MaskCaretMode DateEditMaskCaretMode { get; set; }
}

public interface IModelMemberViewItemMouseWheel : IModelMemberViewItem
{
    [Category("Behavior")]
    [Description("Opcjonalne ustawienie dla konkretnego pola. Null oznacza wartosc z Options.BlockDateEditMouseWheelByDefault.")]
    bool? BlockMouseWheel { get; set; }
}
```

Atrybut `[DateEditMouseWheel]` i stałe aliasów wkładam do projektu modułowego (poza projektem Blazor), żeby business objecty mogły go używać bez referencji do Blazor.Server. Interfejsy modelu zostają w projekcie Blazor, bo tylko Blazor je honoruje.

Oba interfejsy trzeba zarejestrować w module Blazor:

```csharp
public override void ExtendModelInterfaces(ModelInterfaceExtenders extenders)
{
    base.ExtendModelInterfaces(extenders);
    extenders.Add<IModelOptions, IModelOptionsDateEditMouseWheel>();
    extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
}
```

Bez tych dwóch rejestracji Model Editor nie pokaże nowych property — interfejsy istnieją, ale są niezaczepione.

W głównym `Model.xafml` ustawienie jest jawne:

```xml
<Options ... BlockDateEditMouseWheelByDefault="True" DateEditMaskCaretMode="Advancing" />
```

Kolejność decyzji jest taka:

1. Jeśli property ma atrybut `[DateEditMouseWheel(false)]`, scroll działa dla tego pola.
2. Jeśli `MemberViewItem` w Model Editorze ma ustawione `BlockMouseWheel`, ta wartość wygrywa.
3. Jeśli pole nie ma wyjątku, używane jest `Options.BlockDateEditMouseWheelByDefault`.

## Edytor jako globalny domyślny editor

Wersja opt-in przez `[EditorAlias]` jest bezpieczna w małej próbce kodu, ale w prawdziwej aplikacji łatwo zapomnieć o jednym polu. Świadomie robię editor globalnym domyślnym dla `DateTime` i `DateTime?`.

```csharp
[PropertyEditor(typeof(DateTime), CustomEditorAliases.DateTimeEditor, true)]
public class CustomDateTimeEditor(Type objectType, IModelMemberViewItem model)
    : DateTimePropertyEditor(objectType, model)
{
    protected override void OnControlCreated()
    {
        base.OnControlCreated();
        if (Control is DxDateEditModel<DateTime> adapter)
        {
            ConfigureMaskCaretMode();
            FleetmanDateTimeEditorConfigurator.Configure(adapter, Model);
        }
    }

    void ConfigureMaskCaretMode()
    {
        MaskCaretMode caretMode = FleetmanDateTimeEditorConfigurator.GetMaskCaretMode(Model);
        DxDateEditMaskProperties.DateTime.CaretMode = caretMode;
        DxDateEditMaskProperties.DateOnly.CaretMode = caretMode;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = caretMode;
    }
}

[PropertyEditor(typeof(DateTime?), CustomEditorAliases.DateTimeEditor, true)]
public class CustomNullableDateTimeEditor(Type objectType, IModelMemberViewItem model)
    : DateTimePropertyEditor(objectType, model)
{
    protected override void OnControlCreated()
    {
        base.OnControlCreated();
        if (Control is DxDateEditModel<DateTime?> adapter)
        {
            ConfigureMaskCaretMode();
            FleetmanDateTimeEditorConfigurator.Configure(adapter, Model);
        }
    }

    void ConfigureMaskCaretMode()
    {
        MaskCaretMode caretMode = FleetmanDateTimeEditorConfigurator.GetMaskCaretMode(Model);
        DxDateEditMaskProperties.DateTime.CaretMode = caretMode;
        DxDateEditMaskProperties.DateOnly.CaretMode = caretMode;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = caretMode;
    }
}
```

Trzeci parametr `true` w `[PropertyEditor]` mówi XAF-owi, że ten editor jest domyślny dla danego typu — nie trzeba już `[EditorAlias]` na każdej property.

Cała logika konfiguracji adaptera (maska, format, klasa CSS) siedzi w jednym statycznym konfiguratorze, do którego oba editory delegują. Caret mode też przechodzi przez konfigurator, ale jest wciąż ustawiany **w klasie editora**, nie wewnątrz konfiguratora — wymaga dostępu do property `DxDateEditMaskProperties` z `DateTimePropertyEditor`.

## Maska decyduje o czasie

Nie wolno globalnie ustawiać `adapter.Mask = "dd.MM.yyyy HH:mm"` ani `adapter.TimeSectionVisible = true`. To zmienia semantykę wszystkich pól datowych — nie każde `DateTime` w XAF oznacza „data i godzina". Zamiast tego editor czyta `EditMask` i `DisplayFormat` z Application Model. Jeśli maska zawiera tokeny czasu (`H`, `h`, `m`, `s`, `t`, `f`, `F`, `K`, `z`) albo standardowy format typu `g`, `G`, `t`, `T`, sekcja czasu jest pokazywana. Jeśli maska jest datowa (`d`, `dd.MM.yyyy`), sekcja czasu pozostaje ukryta.

```csharp
internal static class FleetmanDateTimeEditorConfigurator
{
    static readonly HashSet<char> TimeFormatTokens = new()
    {
        'H', 'h', 's', 't', 'f', 'F', 'K', 'z'
    };

    static readonly HashSet<string> DateTimeStandardFormats = new(StringComparer.Ordinal)
    {
        "f", "F", "g", "G", "o", "O", "r", "R", "s", "t", "T", "u", "U"
    };

    public static MaskCaretMode GetMaskCaretMode(IModelMemberViewItem model)
    {
        if (model?.Application?.Options is IModelOptionsDateEditMouseWheel options)
        {
            return options.DateEditMaskCaretMode;
        }
        return MaskCaretMode.Advancing;
    }

    public static void Configure<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model)
    {
        string editMask = NormalizeModelFormat(model?.EditMask);
        string displayFormat = NormalizeModelFormat(model?.DisplayFormat);

        if (!string.IsNullOrWhiteSpace(displayFormat))
        {
            adapter.Format = displayFormat;
            adapter.DisplayFormat = displayFormat;
        }
        if (!string.IsNullOrWhiteSpace(editMask))
        {
            adapter.Mask = editMask;
        }

        string effectiveFormat = editMask ?? displayFormat;
        bool hasTime = IncludesTimeSection(effectiveFormat);
        adapter.TimeSectionVisible = hasTime;
        if (hasTime)
        {
            adapter.TimeSectionScrollPickerFormat = "H m";
        }

        ApplyMouseWheelBehavior(adapter, model);
    }

    static string NormalizeModelFormat(string format)
    {
        if (string.IsNullOrWhiteSpace(format)) return null;
        string normalized = format.Trim();
        if (normalized.StartsWith("{0:", StringComparison.Ordinal) && normalized.EndsWith("}"))
        {
            normalized = normalized.Substring(3, normalized.Length - 4);
        }
        return string.IsNullOrWhiteSpace(normalized) ? null : normalized;
    }

    static bool IncludesTimeSection(string format)
    {
        if (string.IsNullOrWhiteSpace(format)) return false;
        string normalized = NormalizeModelFormat(format) ?? string.Empty;
        if (DateTimeStandardFormats.Contains(normalized)) return true;

        string maskWithoutLiterals = RemoveQuotedAndEscapedLiterals(normalized);
        for (int i = 0; i < maskWithoutLiterals.Length; i++)
        {
            char token = maskWithoutLiterals[i];
            if (TimeFormatTokens.Contains(token)) return true;
            if (token == 'm' && normalized.Length > 1) return true;
        }
        return false;
    }

    // RemoveQuotedAndEscapedLiterals + ApplyMouseWheelBehavior + AppendCssClass — patrz pełen kod w repo
}
```

W praktyce daje to oczekiwane zachowanie:

- `d` albo `dd.MM.yyyy` → tylko data
- `g` albo `dd.MM.yyyy HH:mm` → data i godzina
- `HH:mm` → tylko czas
- `{0:g}` jako `DisplayFormat` → po normalizacji traktowane jak `g`

Parser dodatkowo pomija literały w apostrofach (`'r.'`), cudzysłowach (`"r."`) i znaki escapowane backslashem — dzięki temu maska `dd.MM.yyyy 'r.'` nie wykryje `r` jako tokenu czasu.

## CSS: blokada i opt-out

Editor dodaje jedną z dwóch klas: `fleetman-dateedit-wheel-blocked` dla pól, na których scroll ma być blokowany, albo `fleetman-dateedit-wheel-allowed` dla pól, które mają kodowy albo modelowy opt-out.

```csharp
static void ApplyMouseWheelBehavior<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model)
{
    bool shouldBlock = ShouldBlockMouseWheel(model);
    AppendCssClass(adapter, shouldBlock
        ? CustomEditorAliases.MouseWheelBlockerCssClass
        : CustomEditorAliases.MouseWheelAllowedCssClass);
}

static bool ShouldBlockMouseWheel(IModelMemberViewItem model)
{
    var attribute = model.ModelMember?.MemberInfo?.FindAttribute<DateEditMouseWheelAttribute>();
    if (attribute is not null)
    {
        return attribute.BlockMouseWheel;
    }

    if (model is IModelMemberViewItemMouseWheel { BlockMouseWheel: bool viewItemValue })
    {
        return viewItemValue;
    }

    if (model.Application.Options is IModelOptionsDateEditMouseWheel options)
    {
        return options.BlockDateEditMouseWheelByDefault;
    }

    return true;
}

static void AppendCssClass<T>(DxDateEditModel<T> adapter, string cssClass)
{
    adapter.CssClass = string.IsNullOrWhiteSpace(adapter.CssClass)
        ? cssClass
        : $"{adapter.CssClass} {cssClass}";
    adapter.InputCssClass = string.IsNullOrWhiteSpace(adapter.InputCssClass)
        ? cssClass
        : $"{adapter.InputCssClass} {cssClass}";
}
```

Dwie ważne rzeczy: klasa trafia i na `CssClass`, i na `InputCssClass`, bo zdarzenie `wheel` może startować z inputa, nie z roota. Opt-out ma własną klasę, żeby JavaScript mógł przepuścić scroll nawet przy globalnej blokadzie — listener sprawdza `-allowed` najpierw, robi `return` przed `-blocked`.

## Kontroler ładujący moduł JS

`_Host.cshtml` nie powinien zawierać logiki konkretnego edytora. W wersji minimalnej akceptujemy `<script>` w hoście, ale w aplikacji produkcyjnej zamykamy to w warstwie XAF.

```csharp
public class DateEditMouseWheelGuardController : ViewController
{
    IJSRuntime jsRuntime;

    protected override void OnActivated()
    {
        base.OnActivated();
        jsRuntime = Application?.ServiceProvider?.GetService<IJSRuntime>();
    }

    protected override void OnViewControlsCreated()
    {
        base.OnViewControlsCreated();
        _ = RegisterWheelGuard();
    }

    async Task RegisterWheelGuard()
    {
        if (jsRuntime is null) return;
        try
        {
            IJSObjectReference module = await jsRuntime.InvokeAsync<IJSObjectReference>(
                "import",
                "./js/fleetman-date-edit-wheel-guard.js");
            await module.InvokeVoidAsync("ensureRegistered");
            await module.DisposeAsync();
        }
        catch (JSException ex)
        {
            Tracing.Tracer.LogError(ex);
        }
    }
}
```

`IJSRuntime` pobieramy w `OnActivated` przez `Application?.ServiceProvider?.GetService<IJSRuntime>()`. Wstrzyknięcie przez konstruktor z `[ActivatorUtilitiesConstructor]` wygląda na poprawne i kompiluje się — ale XAF często wybiera bezparametrowy konstruktor w `application.CreateController<T>()` szybciej, niż doctorowi się wydaje, i wstrzyknięte pole zostaje `null`. Skutek: kontroler się rejestruje, editor doczepia klasę CSS, a scroll dalej zmienia wartości, bo moduł JS nigdy się nie ładuje. Wzorzec przez `ServiceProvider.GetService` jest pewny.

Moduł JS ma własną flagę `registered`, więc listener jest podpinany tylko raz na stronie:

```javascript
let registered = false;

export function ensureRegistered() {
    if (registered) return;
    registered = true;
    document.addEventListener('wheel', function (e) {
        const target = e.target;
        if (!target || typeof target.closest !== 'function') return;
        if (target.closest('.fleetman-dateedit-wheel-allowed')) return;
        if (target.closest('.fleetman-dateedit-wheel-blocked')) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
}
```

W tej wersji `_Host.cshtml` zostaje czysty — żadnego `<script>` blokującego scroll, żadnej zależności od kolejności ładowania.

## Żywy przykład: `Employee.Birthday`

W `MainDemo.NET.EFCore`, którego używamy jako referencji, atrybut `[DateEditMouseWheel(false)]` jest postawiony na polu `Employee.Birthday`. Powód jest praktyczny: data urodzenia to często edycja typu „cofnij o kilkanaście lat" — wygodniej przewinąć rok kółkiem niż wpisywać go ręcznie. Pozostałe pola daty (`DemoTask.DueDate`, `DemoTask.StartDate`, `Employee.Anniversary`) zostają zablokowane.

```csharp
// MainDemo.Module/BusinessObjects/Employee.cs
[DateEditMouseWheel(false)]
public virtual DateTime? Birthday { get; set; }
```

Editor podpina wtedy klasę `fleetman-dateedit-wheel-allowed` zamiast `-blocked` do tej kontrolki. Globalny listener `wheel` widzi `-allowed`, robi `return` przed sprawdzeniem `-blocked`, i scroll przelatuje do DevExpressa normalnie.

W devtools przeglądarki można szybko zweryfikować:

```javascript
document.querySelectorAll('.fleetman-dateedit-wheel-allowed').length
```

zwróci ≥ 1 na widoku z polem `Birthday`. Atrybut wybrałem zamiast ustawienia w Model Editorze, bo decyzja „data urodzenia jest scrollowalna" wynika z modelu domenowego (typ pola, sposób użycia), nie z kontekstu konkretnego widoku. Gdyby było odwrotnie — gdyby pole było scrollowalne w widoku rekrutera, a zablokowane w widoku HR — wybrałbym wariant z `BlockMouseWheel = False` per ViewItem w Model Editorze.

## Checklist wdrożeniowy

Checklist jest rozbity na dwa warianty, do wyboru. Można też zacząć od minimalnego i przejść na pełny, kiedy pojawi się pierwsze pole z wyjątkiem.

### Wariant minimalny — wszystko na sztywno

1. **Dodaj `GlobalDateEditorTweaksController.cs`** w folderze kontrolerów projektu Blazor. Klasa dziedziczy po `ViewController<DetailView>`. W `OnViewControlsCreated` iteruj po `View.Items.OfType<DateTimePropertyEditor>()`, dla każdego ustaw `item.DxDateEditMaskProperties.{DateTime,DateOnly,DateTimeOffset}.CaretMode = MaskCaretMode.Advancing` i doczep klasę `fleetman-dateedit-wheel-blocked` do `CssClass` oraz `InputCssClass` adaptera (cast na `DxDateEditModel<DateTime>` lub `DxDateEditModel<DateTime?>` zależnie od `MemberInfo.MemberType`). XAF rejestruje kontroler automatycznie.
2. **Wklej blok `<script>`** w `Pages/_Host.cshtml` po `_framework/blazor.server.js`. Listener musi mieć trzy flagi: `capture: true`, `passive: false`, `e.stopImmediatePropagation()` po `preventDefault()`. Selektor `.fleetman-dateedit-wheel-blocked`.

### Wariant pełny — sterowany z Model Editora

1. **Dodaj custom property editor dla `DateTime` i `DateTime?` z `isDefaultEditor: true`.** Dwie klasy dziedziczące po `DateTimePropertyEditor`. W `OnControlCreated` cast na `DxDateEditModel<T>`, ustaw caret mode przez `DxDateEditMaskProperties.*.CaretMode`, deleguj resztę do `Configurator.Configure(adapter, Model)`.
2. **Zarejestruj `IModelOptionsDateEditMouseWheel` i `IModelMemberViewItemMouseWheel`** przez `ExtendModelInterfaces` w module Blazor.
3. **Ustaw w głównym `Model.xafml`** atrybuty `BlockDateEditMouseWheelByDefault="True"` i `DateEditMaskCaretMode="Advancing"` na elemencie `<Options>`.
4. **Dodaj `[DateEditMouseWheel(false)]` jako kodowy opt-out** dla pojedynczego pola. Atrybut trzymaj w warstwie modułowej (poza projektem Blazor), żeby business objecty mogły go używać bez referencji do Blazor.Server.
5. **Ładuj moduł JS przez kontroler XAF** (`DateEditMouseWheelGuardController`). `IJSRuntime` pobieraj w `OnActivated` przez `Application?.ServiceProvider?.GetService<IJSRuntime>()` — nie przez konstruktor z `[ActivatorUtilitiesConstructor]`. Moduł JS pobierany przez `import` zostawia listener z idempotentnym `ensureRegistered()`.
6. **Nie ustawiaj jednej maski globalnie.** Czytaj `EditMask` i `DisplayFormat` z modelu, normalizuj zewnętrzny `{0:...}`, ustaw `adapter.Mask` / `adapter.Format` / `adapter.DisplayFormat`.
7. **Pokazuj sekcję czasu tylko wtedy, gdy maska zawiera czas.** Parser sprawdza tokeny `H h s t f F K z`, standardowe formaty `f F g G o O r R s t T u U` i samodzielne `m` w masce > 1 znak. Literały w apostrofach/cudzysłowach pomijaj.
8. **Sprawdź pola z maskami `d`, `g`, `dd.MM.yyyy`, `dd.MM.yyyy HH:mm` i `HH:mm`** plus `{0:g}` jako `DisplayFormat`.

### Weryfikacja po wdrożeniu

1. Build aplikacji w trybie Debug bez błędów i ostrzeżeń.
2. W Model Editorze, w `Application > Options`, są widoczne `BlockDateEditMouseWheelByDefault` i `DateEditMaskCaretMode` (tylko wariant pełny).
3. Detail view z polem daty — scroll na inpucie nie zmienia wartości, caret przeskakuje po wpisaniu pełnej liczby znaków.
4. Dropdown kalendarza działa normalnie, scroll wewnątrz popupu też.
5. W devtools input daty ma klasę `fleetman-dateedit-wheel-blocked` (zwykłe pola) albo `fleetman-dateedit-wheel-allowed` (pola z opt-outem).
6. Wyłącz blokadę dla wybranego pola przez `[DateEditMouseWheel(false)]` albo `BlockMouseWheel = False` w Model Editorze — input dostaje `-allowed`, scroll znowu zmienia wartość, reszta widoku zostaje zablokowana.
7. Konsola przeglądarki bez błędów `Could not import module` przy pierwszym wejściu na widok z datą (tylko wariant pełny — sprawdza, że `IJSRuntime` zadziałał).

---

To jest mała zmiana w kodzie, ale duża zmiana w jakości pracy operatora: przewijanie formularza nie zmienia danych, edytor pozwala wpisywać dokładnie taki zakres informacji, jaki wynika z modelu, a wyjątki dla pól typu „data urodzenia" są deklaratywne i widoczne.
