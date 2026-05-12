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

Chciałem uzyskać cztery rzeczy naraz:

1. Edytor ma być domyślny globalnie dla `DateTime` i `DateTime?`, bez dokładania `[EditorAlias]` na każdej właściwości.
2. Scroll myszą ma być domyślnie zablokowany wewnątrz edytora daty.
3. Blokadę scrolla musi dać się wyłączyć dla pojedynczego pola w Model Editorze.
4. Edytor nie może narzucać jednej maski. Jeśli pole ma maskę daty, pokazuje datę. Jeśli maska zawiera godzinę, pozwala edytować datę i czas.

Ostatni punkt jest ważny. Pierwsza wersja z twardym `dd.MM.yyyy HH:mm` działała, ale była zbyt agresywna: każde pole datowe nagle dostawało czas. To psuje model aplikacji, bo nie każde `DateTime` w XAF oznacza "data i godzina" z perspektywy użytkownika.

## Dlaczego nie sam JavaScript

Najprostszy pomysł to zablokować `wheel` po klasach DevExpressa:

```javascript
document.addEventListener('wheel', function (e) {
    if (e.target.closest('.dxbl-dateedit, .dxbl-timeedit')) {
        e.preventDefault();
    }
}, { passive: false });
```

To jest za kruche.

Po pierwsze, DevExpress obsługuje część zdarzeń wcześnie, więc listener powinien działać w fazie `capture`. Po drugie, klasy `dxbl-*` są wewnętrznym detalem biblioteki i mogą się zmienić między wersjami. Po trzecie, globalny selektor może zahaczyć kontrolki, których nie chcemy dotykać.

Lepszy wzorzec jest podobny do tego, co można zrobić w `MainDemo.NET.EFCore`: custom editor dodaje własną klasę CSS do swojego roota i inputa, a osobny plik JavaScript najpierw sprawdza opt-out, potem blokuje scroll.

Różnica w aplikacji produkcyjnej jest jedna, ale ważna: moduł JavaScript jest ładowany przez kontroler XAF, a nie wklejany do `_Host.cshtml`. Dzięki temu host aplikacji nie zna szczegółów konkretnego edytora, a odpowiedzialność zostaje tam, gdzie powinna być: model decyduje, editor oznacza kontrolkę, kontroler uruchamia mechanizm dla widoków XAF.

```javascript
let registered = false;

export function ensureRegistered() {
    if (registered) {
        return;
    }

    registered = true;
    document.addEventListener('wheel', function (e) {
        const target = e.target;
        if (!target || typeof target.closest !== 'function') {
            return;
        }

        if (target.closest('.fleetman-dateedit-wheel-allowed')) {
            return;
        }

        if (target.closest('.fleetman-dateedit-wheel-blocked')) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
}
```

Wymagane są trzy szczegóły:

- `capture: true`, żeby złapać zdarzenie zanim zrobi to komponent.
- `passive: false`, bo inaczej przeglądarka może zignorować `preventDefault()`.
- opt-out `fleetman-dateedit-wheel-allowed` sprawdzany przed blokadą.
- brak selektorów `dxbl-*`; decyzja ma wynikać z edytora i modelu, nie z wewnętrznych klas DevExpressa.

## Globalny przełącznik w Options

Główna decyzja nie powinna siedzieć na każdym polu osobno. Domyślne zachowanie dla całej aplikacji trzymam w `Application > Options`, a dopiero wyjątki ustawiam na konkretnych polach.

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

Oba interfejsy trzeba zarejestrować w module aplikacji Blazor:

```csharp
public override void ExtendModelInterfaces(ModelInterfaceExtenders extenders)
{
    base.ExtendModelInterfaces(extenders);
    extenders.Add<IModelOptions, IModelOptionsDateEditMouseWheel>();
    extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
}
```

W samym modelu Blazora ustawienie jest jawne:

```xml
<Options UIType="TabbedMDI" BlockDateEditMouseWheelByDefault="True" DateEditMaskCaretMode="Advancing" />
```

Od tego momentu domyślne zachowanie dla całej aplikacji jest jasne: wszystkie edytory daty blokują zmianę wartości kółkiem myszy.

Kolejność decyzji jest taka:

1. Jeśli property ma atrybut `[DateEditMouseWheel(false)]`, scroll działa dla tego pola.
2. Jeśli `ViewItem` ma ustawione `BlockMouseWheel`, ta wartość wygrywa.
3. Jeśli pole nie ma wyjątku, używane jest `Options.BlockDateEditMouseWheelByDefault`.

Kodowy opt-out wygląda tak:

```csharp
[DateEditMouseWheel(false)]
public virtual DateTime? DataKtoraMaReagowacNaScroll { get; set; }
```

## Edytor jako globalny domyślny editor

Wersja opt-in przez `[EditorAlias]` jest bezpieczna w małej próbce kodu, ale w prawdziwej aplikacji łatwo zapomnieć o jednym polu. Tutaj świadomie robię editor globalnym domyślnym dla `DateTime` i `DateTime?`.

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

    private void ConfigureMaskCaretMode()
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

    private void ConfigureMaskCaretMode()
    {
        MaskCaretMode caretMode = FleetmanDateTimeEditorConfigurator.GetMaskCaretMode(Model);
        DxDateEditMaskProperties.DateTime.CaretMode = caretMode;
        DxDateEditMaskProperties.DateOnly.CaretMode = caretMode;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = caretMode;
    }
}
```

Trzeci parametr `[PropertyEditor(..., true)]` oznacza, że editor jest domyślny dla danego typu. Nie trzeba już dopisywać `[EditorAlias]` do każdej właściwości.

`DateEditMaskCaretMode` nie jest ustawieniem pojedynczego pola. To globalna opcja w `Application > Options`, którą editor odczytuje i przekłada na `DxDateEditMaskProperties` w runtime.

## Najważniejsza poprawka: maska decyduje o czasie

Nie wolno globalnie ustawiać:

```csharp
adapter.Mask = "dd.MM.yyyy HH:mm";
adapter.TimeSectionVisible = true;
```

To zmienia semantykę wszystkich pól datowych. Zamiast tego editor czyta `EditMask` i `DisplayFormat` z Application Model. Jeśli maska zawiera tokeny czasu (`H`, `h`, `m`, `s`, `t`, itd.) albo standardowy format typu `g`, `G`, `t`, `T`, wtedy pokazuje sekcję czasu. Jeśli maska jest datowa (`d`, `dd.MM.yyyy`), sekcja czasu pozostaje ukryta.

```csharp
internal static class FleetmanDateTimeEditorConfigurator
{
    private static readonly HashSet<char> TimeFormatTokens = new()
    {
        'H', 'h', 's', 't', 'f', 'F', 'K', 'z'
    };

    private static readonly HashSet<string> DateTimeStandardFormats = new(StringComparer.Ordinal)
    {
        "f", "F", "g", "G", "o", "O", "r", "R", "s", "t", "T", "u", "U"
    };

    public static void Configure<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model)
    {
        string? editMask = NormalizeModelFormat(model.EditMask);
        string? displayFormat = NormalizeModelFormat(model.DisplayFormat);

        if (!string.IsNullOrWhiteSpace(displayFormat))
        {
            adapter.Format = displayFormat;
            adapter.DisplayFormat = displayFormat;
        }

        if (!string.IsNullOrWhiteSpace(editMask))
        {
            adapter.Mask = editMask;
        }

        string? effectiveFormat = editMask ?? displayFormat;
        bool hasTime = IncludesTimeSection(effectiveFormat);
        adapter.TimeSectionVisible = hasTime;
        if (hasTime)
        {
            adapter.TimeSectionScrollPickerFormat = "H m";
        }

        ApplyMouseWheelBlocker(adapter, model);
    }

    private static string? NormalizeModelFormat(string? format)
    {
        if (string.IsNullOrWhiteSpace(format))
        {
            return null;
        }

        string normalized = format.Trim();
        if (normalized.StartsWith("{0:", StringComparison.Ordinal) && normalized.EndsWith('}'))
        {
            normalized = normalized[3..^1];
        }

        return string.IsNullOrWhiteSpace(normalized) ? null : normalized;
    }

    private static bool IncludesTimeSection(string? format)
    {
        if (string.IsNullOrWhiteSpace(format))
        {
            return false;
        }

        string normalized = NormalizeModelFormat(format) ?? string.Empty;
        if (DateTimeStandardFormats.Contains(normalized))
        {
            return true;
        }

        string maskWithoutLiterals = RemoveQuotedAndEscapedLiterals(normalized);
        for (int i = 0; i < maskWithoutLiterals.Length; i++)
        {
            char token = maskWithoutLiterals[i];
            if (TimeFormatTokens.Contains(token))
            {
                return true;
            }

            if (token == 'm' && normalized.Length > 1)
            {
                return true;
            }
        }

        return false;
    }

    private static string RemoveQuotedAndEscapedLiterals(string value)
    {
        var result = new System.Text.StringBuilder(value.Length);
        bool inSingleQuote = false;
        bool inDoubleQuote = false;

        for (int i = 0; i < value.Length; i++)
        {
            char current = value[i];
            if (current == '\\')
            {
                i++;
                continue;
            }

            if (current == '\'' && !inDoubleQuote)
            {
                inSingleQuote = !inSingleQuote;
                continue;
            }

            if (current == '"' && !inSingleQuote)
            {
                inDoubleQuote = !inDoubleQuote;
                continue;
            }

            if (!inSingleQuote && !inDoubleQuote)
            {
                result.Append(current);
            }
        }

        return result.ToString();
    }
}
```

W praktyce daje to oczekiwane zachowanie:

- `d` albo `dd.MM.yyyy` → użytkownik edytuje tylko datę.
- `g` albo `dd.MM.yyyy HH:mm` → użytkownik edytuje datę i godzinę.
- `HH:mm` → użytkownik edytuje czas.
- `[DateEditMouseWheel(false)]` albo `BlockMouseWheel = False` → scroll działa tylko na tym konkretnym polu.

## Klasy CSS: blokada i opt-out

Editor dodaje jedną z dwóch klas:

- `fleetman-dateedit-wheel-blocked` dla pól, na których scroll ma być blokowany.
- `fleetman-dateedit-wheel-allowed` dla pól, które mają kodowy albo modelowy opt-out.

```csharp
private static void ApplyMouseWheelBehavior<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model)
{
    bool shouldBlock = ShouldBlockMouseWheel(model);
    if (shouldBlock)
    {
        AppendCssClass(adapter, CustomEditorAliases.MouseWheelBlockerCssClass);
        return;
    }

    AppendCssClass(adapter, CustomEditorAliases.MouseWheelAllowedCssClass);
}

private static bool ShouldBlockMouseWheel(IModelMemberViewItem model)
{
    DateEditMouseWheelAttribute? attribute =
        model.ModelMember?.MemberInfo?.FindAttribute<DateEditMouseWheelAttribute>();
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

private static void AppendCssClass<T>(DxDateEditModel<T> adapter, string cssClass)
{
    adapter.CssClass = string.IsNullOrWhiteSpace(adapter.CssClass)
        ? cssClass
        : $"{adapter.CssClass} {cssClass}";

    adapter.InputCssClass = string.IsNullOrWhiteSpace(adapter.InputCssClass)
        ? cssClass
        : $"{adapter.InputCssClass} {cssClass}";
}
```

Ważne są dwie rzeczy:

- klasa trafia i na `CssClass`, i na `InputCssClass`, bo zdarzenie `wheel` może startować z inputa, nie z roota;
- opt-out ma własną klasę, żeby JavaScript mógł przepuścić scroll nawet przy globalnej blokadzie.

## Kontroler ładujący guard

`_Host.cshtml` nie powinien zawierać logiki konkretnego edytora. W demo można spotkać wariant z `<script src="js/disable-wheel-on-editors.js"></script>` w hoście, ale w aplikacji produkcyjnej lepiej zamknąć to w warstwie XAF.

Kontroler ładuje moduł JS po utworzeniu kontrolek widoku. Wzorzec jest taki sam jak w `MainDemo.NET.EFCore`:

```csharp
public class DateEditMouseWheelGuardController : ViewController
{
    private IJSRuntime? jsRuntime;

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

    private async Task RegisterWheelGuard()
    {
        if (jsRuntime is null)
        {
            return;
        }

        try
        {
            IJSObjectReference module = await jsRuntime.InvokeAsync<IJSObjectReference>(
                "import",
                "./js/fleetman-date-edit-wheel-guard.js");
            await module.InvokeVoidAsync("ensureRegistered");
            await module.DisposeAsync();
        }
        catch
        {
            // Brak modułu (np. pierwszy render zanim wwwroot jest gotowe) — kolejne
            // wywołanie przy następnym widoku zarejestruje listener przez idempotentne
            // ensureRegistered.
        }
    }
}
```

Moduł JS ma własną flagę `registered`, więc listener jest podpinany tylko raz na stronie.

### Pułapka: dwa konstruktory i `null` w `IJSRuntime`

W pierwszej wersji kontrolera spróbowałem wstrzyknąć `IJSRuntime` przez konstruktor:

```csharp
public DateEditMouseWheelGuardController() { }

[ActivatorUtilitiesConstructor]
public DateEditMouseWheelGuardController(IJSRuntime jsRuntime)
{
    this.jsRuntime = jsRuntime;
}
```

Build przechodził, kontroler był rejestrowany, edytor dodawał klasę CSS — ale **scroll dalej zmieniał wartości**, bo moduł JS nigdy się nie ładował. Diagnoza zajęła więcej niż powinna.

Powód jest mało oczywisty. XAF tworzy kontrolery przez `application.CreateController<T>()` i w wielu ścieżkach życia widoku trafia na bezparametrowy publiczny konstruktor szybciej, niż dochodzi do `ActivatorUtilities.CreateInstance`. `[ActivatorUtilitiesConstructor]` nie jest dla XAF wiążącym selektorem konstruktora w tej samej skali, w jakiej jest dla `IServiceProvider` w ASP.NET Core. W efekcie `jsRuntime` zostaje `null`, `RegisterWheelGuard` od razu wraca, a operator dostaje editor bez guardu.

Dodatkowo, `async void RegisterWheelGuard()` bez `try/catch` jest niebezpieczny: każdy wyjątek z `InvokeAsync` albo `DisposeAsync` leci do `SynchronizationContext` widoku i potrafi cicho rozłożyć kolejne wywołania.

Dlatego we wzorcu właściwym dla XAF Blazor:

- `IJSRuntime` pobieramy z `Application?.ServiceProvider?.GetService<IJSRuntime>()` w `OnActivated`, a nie z konstruktora;
- `RegisterWheelGuard` zwraca `Task`, a w miejscu wywołania jest `_ = RegisterWheelGuard()` (fire-and-forget bez `async void`);
- całe ciało metody siedzi w `try/catch`, bo pierwsze wywołanie potrafi trafić w moment, gdy moduł nie jest jeszcze osiągalny przez `import`.

Jeśli ktoś czyta tylko sygnatury — kontroler wygląda niemal tak samo. Różnica leży w tym, że ten wariant **realnie odpala JS na widoku**, a wariant z `[ActivatorUtilitiesConstructor]` cicho rezygnuje.

## Co było brakującą informacją w pierwszej wersji

Pierwsza wersja opisu była dobra jako demonstracja mechanizmu, ale brakowało w niej trzech informacji potrzebnych do produkcyjnego wdrożenia:

1. **Czy editor ma być globalny, czy opt-in.** W realnej aplikacji lepszy okazał się wariant globalny, bo problem scrolla dotyczy każdego pola daty.
2. **Jak nie zepsuć pól bez godziny.** Globalny editor nie może narzucić `dd.MM.yyyy HH:mm`. Musi uszanować maskę z modelu.
3. **Że blokada scrolla jest zachowaniem editora, nie ogólną regułą JS dla DevExpressa.** Dlatego selektor JS celuje tylko we własną klasę CSS.
4. **Gdzie ustawić `CaretMode`.** W tym wariancie `DateEditMaskCaretMode` jest globalną opcją modelu, a nie ustawieniem pojedynczego ViewItem.
5. **Jak dostać `IJSRuntime` w kontrolerze XAF.** Wstrzyknięcie przez konstruktor z `[ActivatorUtilitiesConstructor]` wygląda na poprawne, kompiluje się, kontroler się rejestruje — ale w praktyce `jsRuntime` bywa `null` i guard cicho nie startuje. Pewny wariant: `Application?.ServiceProvider?.GetService<IJSRuntime>()` w `OnActivated`, jak w `MainDemo.NET.EFCore`.

Po tej zmianie editor jest domyślny w całej aplikacji, ale nadal zachowuje się zgodnie z konfiguracją XAF Model.

## Gotowy prompt dla agenta AI

Poniższy prompt jest wersją operacyjną. Można go wkleić agentowi AI pracującemu w repo XAF Blazor i oczekiwać kompletnego wdrożenia, a nie tylko fragmentu kodu.

```text
Pracujesz w aplikacji DevExpress XAF Blazor. Wdroż globalny domyślny edytor daty dla DateTime i DateTime?, który blokuje zmianę wartości kółkiem myszy, ale nadal respektuje maski XAF.

Wymagania funkcjonalne:
1. Dodaj custom property editor dziedziczący po DateTimePropertyEditor dla DateTime.
2. Dodaj analogiczny custom property editor dla DateTime?.
3. Oba editory zarejestruj przez [PropertyEditor(..., isDefaultEditor: true)], tak żeby były globalnym domyślnym edytorem dla DateTime i DateTime?.
4. Nie wymagaj [EditorAlias] na poszczególnych właściwościach.
5. Dodaj rozszerzenie modelu IModelOptionsDateEditMouseWheel z bool BlockDateEditMouseWheelByDefault, MaskCaretMode DateEditMaskCaretMode, Category("Behavior"), DefaultValue(true) / DefaultValue(MaskCaretMode.Advancing) i opisami dla Model Editora.
6. Dodaj rozszerzenie modelu IModelMemberViewItemMouseWheel z nullable bool? BlockMouseWheel. Null ma oznaczać: użyj globalnego Options.
7. Zarejestruj oba rozszerzenia modelu w module Blazor przez ExtendModelInterfaces:
   extenders.Add<IModelOptions, IModelOptionsDateEditMouseWheel>();
   extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
8. W głównym Model.xafml ustaw jawnie:
   <Options ... BlockDateEditMouseWheelByDefault="True" DateEditMaskCaretMode="Advancing" />
9. Dodaj atrybut [DateEditMouseWheel(false)], który można ustawić na property biznesowej, aby scroll działał dla tego jednego pola.
10. Kolejność decyzji ma być taka: atrybut na property, potem ViewItem.BlockMouseWheel, potem Options.BlockDateEditMouseWheelByDefault.
11. Domyślnie blokuj scroll myszą wewnątrz edytora daty.
12. Jeśli atrybut albo ViewItem wyłącza blokadę, dodaj klasę opt-out, np. "myapp-dateedit-wheel-allowed".
13. Dodaj własną klasę blokującą, np. "myapp-dateedit-wheel-blocked", do adapter.CssClass i adapter.InputCssClass edytora, gdy scroll ma być blokowany.
14. Dodaj moduł JavaScript ładowany przez kontroler XAF, a nie wpisany w _Host.cshtml. Moduł ma dodać listener dla zdarzenia wheel w fazie capture:
    - { capture: true, passive: false }
    - jeśli target.closest('.myapp-dateedit-wheel-allowed'), nic nie blokuj
    - blokuj target.closest('.myapp-dateedit-wheel-blocked')
    - wywołaj e.preventDefault()
    - wywołaj e.stopImmediatePropagation()
15. Nie używaj klas dxbl-* jako mechanizmu detekcji. Własne klasy dodane przez editor muszą sterować blokadą i opt-outem.
16. W kontrolerze ładującym moduł JS pobierz IJSRuntime w OnActivated przez Application?.ServiceProvider?.GetService<IJSRuntime>(). Nie używaj konstruktora z [ActivatorUtilitiesConstructor] — XAF często wybiera bezparametrowy konstruktor i wstrzyknięte pole pozostaje null, przez co guard cicho nie startuje.
17. Metoda ładująca moduł ma zwracać Task (nie async void), wywołanie ma postać fire-and-forget: _ = RegisterWheelGuard(). Całe ciało otocz try/catch — pierwsze wywołanie potrafi trafić w moment, gdy moduł nie jest jeszcze osiągalny przez import.

Wymagania dotyczące masek:
1. Nie ustawiaj globalnie jednej maski typu "dd.MM.yyyy HH:mm".
2. Czytaj model.EditMask i model.DisplayFormat z IModelMemberViewItem.
3. Jeśli DisplayFormat ma postać "{0:g}" albo "{0:dd.MM.yyyy HH:mm}", znormalizuj go do "g" albo "dd.MM.yyyy HH:mm".
4. Jeśli model ma EditMask, ustaw adapter.Mask na tę wartość.
5. Jeśli model ma DisplayFormat, ustaw adapter.Format i adapter.DisplayFormat na tę wartość.
6. Ustaw adapter.TimeSectionVisible = true tylko wtedy, gdy efektywna maska lub format zawiera czas.
7. Traktuj jako formaty z czasem standardowe formaty .NET: f, F, g, G, o, O, r, R, s, t, T, u, U.
8. Traktuj jako formaty z czasem maski zawierające tokeny: H, h, m, s, t, f, F, K, z.
9. Nie traktuj pojedynczego standardowego formatu "m" ani "M" jako czasu, bo to format miesiąc/dzień.
10. Przy analizie maski pomijaj literały w apostrofach, cudzysłowach i znaki escapowane backslashem.

Wymagania DevExpress:
1. Odczytaj DateEditMaskCaretMode z Options modelu i ustaw tę wartość dla:
   - DxDateEditMaskProperties.DateTime
   - DxDateEditMaskProperties.DateOnly
   - DxDateEditMaskProperties.DateTimeOffset
2. Zrób to w miejscu, gdzie editor ma dostęp do DxDateEditMaskProperties.
3. Pracuj na DxDateEditModel<DateTime> i DxDateEditModel<DateTime?>.

Weryfikacja:
1. Uruchom build projektu Blazor w konfiguracji Release.
2. Sprawdź, że kompilacja przechodzi bez błędów.
3. Sprawdź w kodzie lub testowo, że:
   - maska "d" nie pokazuje sekcji czasu,
   - maska "dd.MM.yyyy" nie pokazuje sekcji czasu,
   - maska "g" pokazuje sekcję czasu,
   - maska "dd.MM.yyyy HH:mm" pokazuje sekcję czasu,
   - maska "HH:mm" pokazuje sekcję czasu,
   - "{0:g}" jest interpretowane jak "g".
4. Sprawdź, że Options.BlockDateEditMouseWheelByDefault jest ustawione na True w głównym modelu aplikacji.
5. Sprawdź, że Options.DateEditMaskCaretMode jest ustawione na Advancing w głównym modelu aplikacji.
6. Sprawdź, że scroll nad zwykłym polem daty nie zmienia wartości.
7. Sprawdź, że po dodaniu [DateEditMouseWheel(false)] do property scroll działa dla tego pola.
8. Sprawdź, że po ustawieniu BlockMouseWheel = False dla pojedynczego ViewItem scroll działa dla tego pola.

Ograniczenia:
1. Nie zmieniaj semantyki istniejących pól datowych.
2. Nie przenoś wszystkich pól na datę z godziną.
3. Nie opieraj opt-outu na klasach CSS DevExpressa.
4. Nie pozwalaj, żeby domyślnie scroll zmieniał daty.
5. Nie rób osobnego opt-in przez [EditorAlias], chyba że repo ma wyraźny wymóg przeciwny. Domyślnie editor ma być globalny.
6. Nie dodawaj logiki edytora dat do _Host.cshtml.

Na końcu podaj:
1. listę zmienionych plików,
2. wynik builda,
3. krótką instrukcję, gdzie w Model Editorze wyłączyć BlockMouseWheel dla pojedynczego pola,
4. przykład użycia [DateEditMouseWheel(false)] na property.
```

W praktyce najważniejsze zdania w tym promptcie są dwa: **"Options jest źródłem domyślnego zachowania"** oraz **"Nie ustawiaj globalnie jednej maski typu `dd.MM.yyyy HH:mm`."** Bez pierwszego agent zrobi tylko lokalny hack, bez drugiego zepsuje pola datowe bez godziny.

## Checklist wdrożeniowy

1. Dodaj custom property editor dla `DateTime` i `DateTime?` z `isDefaultEditor: true`.
2. Zarejestruj `IModelOptionsDateEditMouseWheel` i `IModelMemberViewItemMouseWheel` przez `ExtendModelInterfaces`.
3. Ustaw w głównym `Model.xafml`: `BlockDateEditMouseWheelByDefault="True"` i `DateEditMaskCaretMode="Advancing"`.
4. Dodaj `[DateEditMouseWheel(false)]` jako kodowy opt-out dla pojedynczego pola.
5. Ładuj moduł JS przez kontroler XAF i blokuj `wheel` w fazie `capture`, ale najpierw honoruj klasę opt-out. `IJSRuntime` pobieraj w `OnActivated` przez `Application?.ServiceProvider?.GetService<IJSRuntime>()` — nie przez `[ActivatorUtilitiesConstructor]`.
6. Nie ustawiaj jednej maski globalnie. Czytaj `EditMask` i `DisplayFormat`.
7. Pokazuj sekcję czasu tylko wtedy, gdy maska zawiera czas.
8. Sprawdź pola z maskami `d`, `g`, `dd.MM.yyyy`, `dd.MM.yyyy HH:mm` i `HH:mm`.

To jest mała zmiana w kodzie, ale duża zmiana w jakości pracy operatora: przewijanie formularza nie zmienia danych, a edytor dalej pozwala wpisywać dokładnie taki zakres informacji, jaki wynika z modelu.
