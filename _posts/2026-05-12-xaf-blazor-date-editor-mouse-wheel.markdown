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

## Wersja minimalna — wszystko na sztywno, bez konfiguracji

Zanim pójdziemy w stronę interfejsów modelu, atrybutów i konfiguratorów, warto pokazać minimalny wariant, w którym ten sam efekt — globalna blokada scrolla i `MaskCaretMode.Advancing` dla wszystkich pól daty — robi się **dwoma plikami**, bez żadnej możliwości wyjątku per pole czy per widok. To jest wzorzec, który DevExpress dokumentuje pod hasłem „Customize a Built-in Property Editor": zamiast subclass-ować editor, dorzucamy zwykły `ViewController`, który łapie wszystkie property editory daty i modyfikuje ich adapter w runtime.

### Krok 1: kontroler ustawiający caret mode i klasę CSS

```csharp
using DevExpress.Blazor;
using DevExpress.ExpressApp;
using DevExpress.ExpressApp.Blazor.Components.Models;
using DevExpress.ExpressApp.Editors;

public class GlobalDateEditorTweaksController : ViewController<DetailView>
{
    protected override void OnViewControlsCreated()
    {
        base.OnViewControlsCreated();
        foreach (var item in View.Items.OfType<PropertyEditor>())
        {
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

XAF rejestruje ten kontroler automatycznie. Na każdym `DetailView` iteruje po `PropertyEditor`-ach, sprawdza, czy pole jest typu `DateTime` lub `DateTime?`, i doczepia stałą klasę CSS do adaptera DevExpress. Bez subclass-owania, bez `[PropertyEditor]`, bez `[EditorAlias]` na business objectach.

#### Dlaczego nie ustawiamy tu `MaskCaretMode`

Pierwsza wersja tego kontrolera miała też `OnActivated` z trzema linijkami `DxDateEditMaskProperties.{DateTime,DateOnly,DateTimeOffset}.CaretMode = MaskCaretMode.Advancing`. Wyglądało to na globalną konfigurację DevExpressa — ustawienie raz przy aktywacji widoku, koniec tematu. Okazało się, że tylko pierwsza linijka się kompiluje. Pozostałe dwie produkują `CS0120: Dla niestatycznego pola, metody lub właściwości wymagane jest odwołanie do obiektu`.

Powód jest taki, że `DxDateEditMaskProperties` **nie jest** globalną static class w `DevExpress.Blazor`, jak by to sugerowała składnia. To property dziedziczona z `DateTimePropertyEditor` — `DateTime` jest zagnieżdżonym typem ze static `CaretMode`, ale `DateOnly` i `DateTimeOffset` to instance property na właścicielu. Bez dziedziczenia z `DateTimePropertyEditor` symbol nie ma do czego się rozwiązać. W praktyce oznacza to, że **caret mode da się ustawić tylko z wnętrza property editora**, czyli w wariancie pełnym. W minimalnej wersji zostaje przy domyślnym DevExpressowym `Static`. Jeśli ten kompromis jest do przyjęcia, kontroler powyżej wystarcza; jeśli `Advancing` jest wymagany, trzeba przeskoczyć na subclass `DateTimePropertyEditor` z sekcji „Edytor jako globalny domyślny editor".

### Krok 2: globalny listener `wheel`

W `_Host.cshtml` po `_framework/blazor.server.js`:

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

Trzy szczegóły, które już omówiliśmy wcześniej — `capture: true`, `passive: false`, `stopImmediatePropagation()` — pozostają takie same. Selektor celuje wyłącznie w naszą klasę, więc działa niezależnie od wersji DevExpress.

To jest cała wersja minimalna. Build + run i wszystkie pola daty w aplikacji mają zablokowany scroll.

### Czego ta wersja nie daje

- **Nie ma `MaskCaretMode.Advancing`.** Jak wytłumaczono w poprzednim akapicie, ustawienie caret mode wymaga dostępu do property edytora, której ViewController nie ma. Zostaje domyślny `Static`, czyli kursor stoi w sekcji maski aż przełączymy go Tabem lub strzałką. Dla pól `dd.MM.yyyy` to upierdliwe (`Tab` po dwóch znakach), więc jeśli to przeszkadza, trzeba przejść na wariant pełny.
- **Nie ma wyjątków per pole.** Jeśli jedno pole — np. data urodzenia, gdzie wygodniej cofnąć rok kółkiem — ma scrollować, musimy albo zmienić kod, albo wprowadzić wyjątek z innego kontrolera. W obu wariantach jest to twarda zmiana w kodzie, nie konfiguracja.
- **Nie ma wyjątków per widok.** Gdyby data urodzenia była scrollowalna w widoku rekrutacji, a zablokowana w HR, jeden kontroler już nie wystarczy.
- **Nie ma konfiguracji bez recompile.** Admin nie wpłynie na zachowanie inaczej niż przez nowy build i deploy.
- **`ListView` (grid inline edit) nie jest pokryty**, bo kontroler jest `ViewController<DetailView>`. Dla grida trzeba dorobić analogiczny albo zmienić bazę na samo `ViewController` i obsłużyć oba typy widoków.

Dla projektów typu „demo + jedna domena" to często wystarczy. Dla aplikacji, gdzie różne klasy biznesowe potrzebują różnych ustawień, gdzie admin ma móc zmienić zachowanie bez rebuilda, albo gdzie pojedyncze pola chcemy oznaczać deklaratywnie (atrybut na property zamiast „przeczytaj, co robi kontroler"), trzeba pójść krok dalej.

## Co dorzucić, żeby zarządzać tym z Model Editora

Wersja minimalna ma sztywno wpisane „wszystko zablokowane, caret mode Advancing". Żeby z tego zrobić system, w którym deweloper i admin mogą wpływać na zachowanie bez rebuilda, dorzucamy następujące elementy. Każdy z nich rozwiązuje jeden konkretny problem wersji minimalnej, więc nic nie stoi na przeszkodzie, żeby wprowadzać je iteracyjnie — niekoniecznie wszystkie naraz.

1. **Własna subclass `DateTimePropertyEditor` zamiast generycznego kontrolera** — dwie klasy: dla `DateTime` i `DateTime?`. Powód: property editor ma własne `Model` (`IModelMemberViewItem`), do którego XAF potrafi dorzucić nasze property widoczne w Model Editor. Generyczny `ViewController` nie ma „własnego Model" i nie zostanie pokazany w Model Editorze jako konfigurowalny.
2. **Atrybut `[DateEditMouseWheel(false)]`** na property w business objectcie. Powód: są pola, gdzie decyzja „scroll OK / scroll blokuje" należy do modelu domenowego, nie do xafml. Atrybut trzyma tę informację w kodzie razem z definicją property — review pull requesta od razu ją widzi.
3. **Interfejs `IModelMemberViewItemMouseWheel`** z nullable `BlockMouseWheel`. Powód: w Model Editor każdy `MemberViewItem` dostaje nowe property `BlockMouseWheel`. Pozwala wyłączyć blokadę dla pola w **konkretnym widoku** bez zmiany kodu — pole może być scrollowalne w jednym widoku, zablokowane w drugim.
4. **Interfejs `IModelOptionsDateEditMouseWheel`** z `BlockDateEditMouseWheelByDefault` i `DateEditMaskCaretMode`. Powód: globalna wartość domyślna dla całej aplikacji zapisana w `Model.xafml`. Admin/devops może to zmienić w trakcie deploy-u bez recompile.
5. **`ExtendModelInterfaces` w module Blazor**. Powód: bez tego XAF Model Editor nie pokaże nowych property z punktów 3 i 4 — interfejsy istnieją, ale nie są zaczepione do bazowych `IModelMemberViewItem` / `IModelOptions`.
6. **Konfigurator z kaskadą trzech poziomów** (atrybut → ViewItem → IModelOptions). Powód: trzymanie logiki decyzji „blokować czy nie" w jednym miejscu zamiast duplikowania w obu editorach. Przy okazji zapewnia jednoznaczną kolejność precedencji.
7. **Wykrywanie sekcji czasu z formatu (`EditMask` / `DisplayFormat`)** w konfiguratorze. Powód: pole z `DisplayFormat="dd.MM.yyyy HH:mm"` powinno mieć widoczną sekcję czasu w UI, a pole z `dd.MM.yyyy` — nie. Bez wykrywania trzeba by trzymać dwa różne typy editorów albo manualnie ustawiać `TimeSectionVisible` w każdym xafml-u.
8. **Dwie klasy CSS (`-blocked` i `-allowed`) zamiast jednej**. Powód: opt-out per pole działa tak, że pole „dozwolone" dostaje klasę `-allowed`. JS guard widząc tę klasę robi `return` **przed** sprawdzeniem `-blocked`. To prostszy mechanizm niż usuwanie klasy `-blocked`, bo działa też dla pól zagnieżdżonych.
9. **JS jako moduł ESM z idempotentnym `ensureRegistered()`, ładowany przez kontroler**. Powód: pozbywamy się hardcoded `<script>` w `_Host.cshtml` (kolejność ładowania bywa zawodna — wystarczy, że ktoś dorzuci kolejny `<script>` przed naszym i przestaje działać) i mamy gwarancję, że listener nie jest rejestrowany dwa razy nawet przy SignalR-reconnect.

Reszta artykułu rozwija każdy z tych punktów: sekcja **„Globalny przełącznik w Options"** opisuje punkty 3, 4 i 5; **„Edytor jako globalny domyślny editor"** rozwija punkt 1; **„Najważniejsza poprawka: maska decyduje o czasie"** to punkt 7; **„Klasy CSS: blokada i opt-out"** — punkty 8 i część 6; **„Kontroler ładujący guard"** — punkt 9.

## Dlaczego nie sam JavaScript

Najprostszy pomysł to zablokować `wheel` po klasach DevExpressa:

```javascript
document.addEventListener('wheel', function (e) {
    if (e.target.closest('.dxbl-dateedit, .dxbl-timeedit')) {
        e.preventDefault();
    }
}, { passive: false });
```

Takie podejście jest zawodne.

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

### Żywy przykład: `Employee.Birthday`

W `MainDemo.NET.EFCore`, którego używamy jako referencji, ta decyzja zapadła dla pola `Employee.Birthday`. Powód jest praktyczny: data urodzenia to często edycja typu „cofnij o kilkanaście lat" — wygodniej przewinąć rok kółkiem niż wpisywać go ręcznie. Pozostałe pola daty w aplikacji (`DemoTask.DueDate`, `DemoTask.StartDate`, `Employee.Anniversary`) zostają zablokowane, bo to typowo „dziś plus parę dni", scroll wtedy przeszkadza.

```csharp
// MainDemo.Module/BusinessObjects/Employee.cs
[DateEditMouseWheel(false)]
public virtual DateTime? Birthday { get; set; }
```

Editor podpina wtedy klasę `fleetman-dateedit-wheel-allowed` zamiast `-blocked` do tej konkretnej kontrolki. Globalny listener `wheel` widzi `.fleetman-dateedit-wheel-allowed`, robi `return` przed sprawdzeniem `-blocked`, i scroll przelatuje do DevExpressa normalnie. Reszta pól daty w widoku detail (`Anniversary` w tej samej klasie, daty w `Tasks` itp.) pozostaje zablokowana, bo nie mają tego atrybutu.

W devtools przeglądarki można szybko zweryfikować:

```javascript
document.querySelectorAll('.fleetman-dateedit-wheel-allowed').length
```

zwróci ≥ 1 na widoku z polem `Birthday`. Atrybut wybrałem zamiast ustawienia w Model Editorze, bo decyzja „data urodzenia jest scrollowalna" wynika z modelu domenowego (typ pola, sposób użycia), nie z kontekstu konkretnego widoku. Gdyby było odwrotnie — gdyby pole było scrollowalne w widoku rekrutera, a zablokowane w widoku HR — wybrałbym wariant z `BlockMouseWheel = False` per ViewItem.

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

Checklist jest rozbity na dwa warianty. Wariant minimalny pokazuje, ile naprawdę trzeba dotknąć, żeby zablokować scroll w całej aplikacji bez żadnej dodatkowej konfiguracji. Wariant pełny rozszerza go o sterowanie z Model Editora, atrybut na property i wykrywanie sekcji czasu z maski. W praktyce wybiera się jeden z nich — wybór zależy od tego, czy aplikacja potrzebuje wyjątków per pole i per widok, czy nie. Można też zacząć od minimalnego i przejść na pełny, kiedy pojawi się pierwsze pole, dla którego scroll ma działać (najczęstszy kandydat: data urodzenia).

### Wariant minimalny — wszystko na sztywno

Dla projektów, w których akceptujemy globalną blokadę bez wyjątków per pole i bez konfiguracji w Model Editorze. Dwa pliki, ~40 linii kodu razem.

1. **Dodaj `GlobalDateEditorTweaksController.cs`** w `MainDemo.Blazor.Server/Controllers/` (lub odpowiedniku w Twoim projekcie). Klasa dziedziczy po `ViewController<DetailView>`. W `OnViewControlsCreated` iteruj po `View.Items.OfType<PropertyEditor>()`, sprawdź typ przez `MemberInfo.MemberType` i dla `DateTime` / `DateTime?` cast-uj `Control` na `DxDateEditModel<T>`, doczepiając klasę CSS `fleetman-dateedit-wheel-blocked` do `CssClass` **i** `InputCssClass`. Pełen kod jest w sekcji „Wersja minimalna" na początku tego wpisu. XAF zarejestruje kontroler automatycznie — nie ma żadnego `AddTransient` ani podobnego wpisu. Uwaga: `MaskCaretMode` nie da się tu ustawić, bo `DxDateEditMaskProperties` jest property dziedziczoną z `DateTimePropertyEditor`, nie globalną static class — patrz akapit „Dlaczego nie ustawiamy tu `MaskCaretMode`" w sekcji „Wersja minimalna".
2. **Wklej blok `<script>`** w `Pages/_Host.cshtml` po linijce z `_framework/blazor.server.js`. Listener musi mieć trzy flagi: `capture: true` (zdarzenie łapane przed DevExpressem, w fazie capture), `passive: false` (żeby `preventDefault()` faktycznie zadziałał) oraz wywołanie `e.stopImmediatePropagation()` po `preventDefault()` (zatrzymuje inne listenery na tym samym elemencie). Selektor `.fleetman-dateedit-wheel-blocked` celuje wyłącznie w naszą klasę — nie zależy od żadnej wewnętrznej klasy DevExpressa.
3. **Build i smoke test.** Otwórz w przeglądarce dowolny detail view z polem daty, kliknij w `<input>`, przewiń kółkiem — wartość nie powinna się zmienić. W konsoli devtools potwierdź, że istnieją elementy z klasą:
   ```javascript
   document.querySelectorAll('.fleetman-dateedit-wheel-blocked').length
   ```
   Wartość ≥ 1 na widoku z polem daty oznacza, że editor doczepia klasę.

Czego ten wariant **nie** robi: nie ustawia `MaskCaretMode.Advancing` (zostaje domyślny `Static`), nie pozwala wyłączyć blokady dla wybranego pola, nie obsługuje grida (`ListView` z inline edit), nie zmienia maski w zależności od `EditMask`/`DisplayFormat` — wszystkie pola dostają zachowanie domyślne DevExpressa. Jeśli w toku użytkowania okaże się, że któraś z tych rzeczy przeszkadza, przejdź na wariant pełny.

### Wariant pełny — sterowany z Model Editora

Dla projektów, w których chcemy: opcji w Model Editor (globalne `Options.BlockDateEditMouseWheelByDefault`, per-ViewItem `BlockMouseWheel`), atrybutu deklaratywnego na property, format-świadomego pokazywania sekcji czasu i czystego JS-modułu ładowanego przez kontroler.

1. **Dodaj custom property editor dla `DateTime` i `DateTime?` z `isDefaultEditor: true`.** Dwie klasy (XAF property editory są typo-specyficzne, nullable to osobny typ): `CustomDateTimeEditor : DateTimePropertyEditor` i `CustomNullableDateTimeEditor : DateTimePropertyEditor`. Oba zarejestrowane przez `[PropertyEditor(typeof(DateTime|DateTime?), CustomEditorAliases.DateTimeEditor, true)]`. Trzeci parametr `true` oznacza, że editor staje się domyślnym dla danego typu w całej aplikacji — nie trzeba dorzucać `[EditorAlias]` na każdej property. W `OnControlCreated` cast-uj `Control` na `DxDateEditModel<T>` i deleguj do statycznego `Configurator.Configure(adapter, Model)`.
2. **Zarejestruj `IModelOptionsDateEditMouseWheel` i `IModelMemberViewItemMouseWheel` przez `ExtendModelInterfaces`** w `BlazorModule.cs`. Dwa wpisy: `extenders.Add<IModelOptions, IModelOptionsDateEditMouseWheel>()` i `extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>()`. Bez tych rejestracji interfejsy istnieją w kodzie, ale Model Editor ich nie zobaczy — pierwsze property w `Application > Options` ani `BlockMouseWheel` w `MemberViewItem` nie pojawi się jako konfigurowalne.
3. **Ustaw w głównym `Model.xafml`: `BlockDateEditMouseWheelByDefault="True"` i `DateEditMaskCaretMode="Advancing"`.** Te atrybuty dodaj do elementu `<Options ...>`. Można je zostawić puste — wtedy zadziała `[DefaultValue]` z interfejsu (`True` i `Advancing`), ale jawne ustawienie w xafml-u jest czytelniejsze dla każdego, kto otworzy plik. Operator/admin może zmienić wartości w trakcie deploy-u bez recompile.
4. **Dodaj `[DateEditMouseWheel(false)]` jako kodowy opt-out dla pojedynczego pola.** Atrybut leży w warstwie modułowej (poza projektem Blazor), więc business objecty mogą go używać bez referencji do Blazor.Server. Żywy przykład: w `MainDemo.NET.EFCore` jest tak oznaczone pole `Employee.Birthday`, bo data urodzenia to typowe „cofnij o lata", gdzie scroll jest wygodniejszy niż wpisywanie. Pozostałe pola (`Anniversary`, `DemoTask.DueDate`, `DemoTask.StartDate`) zostają w domyślnej blokadzie. Atrybut wygrywa nad `Model.xafml` — jeśli ktoś jednocześnie wpisze przeciwną wartość w Model Editorze, atrybut zostaje pierwszy w kolejności decyzji.
5. **Ładuj moduł JS przez kontroler XAF i blokuj `wheel` w fazie `capture`, ale najpierw honoruj klasę opt-out.** `DateEditMouseWheelGuardController` dziedziczy po `ViewController` (bez parametru typu — działa na każdym widoku). W `OnActivated` pobierz `IJSRuntime` przez `Application?.ServiceProvider?.GetService<IJSRuntime>()` — **nie** przez konstruktor z `[ActivatorUtilitiesConstructor]`, bo XAF często wybiera bezparametrowy konstruktor i wstrzyknięte pole zostaje `null`, przez co guard cicho nie startuje. W `OnViewControlsCreated` zrób `_ = RegisterWheelGuard()` (fire-and-forget, nie `async void`). Metoda `RegisterWheelGuard` zwraca `Task`, woła `jsRuntime.InvokeAsync<IJSObjectReference>("import", "./js/fleetman-date-edit-wheel-guard.js")`, potem `module.InvokeVoidAsync("ensureRegistered")`, na końcu `module.DisposeAsync()`. Całość owinięta w `try/catch` — pierwsze wywołanie może trafić w moment, gdy moduł nie jest jeszcze osiągalny przez `import`, kolejne ustabilizują listener przez idempotentne `ensureRegistered`.
6. **Nie ustawiaj jednej maski globalnie. Czytaj `EditMask` i `DisplayFormat`.** Najczęstsza pułapka pierwszej iteracji — wpisanie `adapter.Mask = "dd.MM.yyyy HH:mm"` globalnie zmienia semantykę wszystkich pól datowych. Zamiast tego w konfiguratorze normalizuj `model.EditMask` i `model.DisplayFormat` (usuwając zewnętrzny `{0:...}` z `DisplayFormat`), ustawiaj `adapter.Mask = editMask` jeśli niepuste, `adapter.Format = adapter.DisplayFormat = displayFormat` jeśli niepuste.
7. **Pokazuj sekcję czasu tylko wtedy, gdy maska zawiera czas.** Parser w `IncludesTimeSection(format)` powinien wyrzucić literały w apostrofach, cudzysłowach i escapowane backslashem, a potem sprawdzić, czy w pozostałych znakach jest jeden z tokenów `H h s t f F K z` lub samodzielne `m` w masce dłuższej niż 1 znak. Standardowe formaty .NET-owe `f F g G o O r R s t T u U` traktuj jako mające czas. W konfiguratorze: `adapter.TimeSectionVisible = hasTime`; jeśli `hasTime`, dorzuć `adapter.TimeSectionScrollPickerFormat = "H m"`.
8. **Sprawdź pola z maskami `d`, `g`, `dd.MM.yyyy`, `dd.MM.yyyy HH:mm` i `HH:mm`.** To pięć przypadków, na których łatwo wykryć regresję:
   - `d` → tylko data, sekcja czasu ukryta
   - `dd.MM.yyyy` → tylko data, sekcja czasu ukryta
   - `g` → data + czas, sekcja czasu widoczna
   - `dd.MM.yyyy HH:mm` → data + czas, sekcja czasu widoczna
   - `HH:mm` → tylko czas, sekcja czasu widoczna
   Plus `{0:g}` jako `DisplayFormat` — po normalizacji powinno być traktowane jak `g`.

### Weryfikacja po wdrożeniu

Po zakończonym builodzie warto przejść siedem testów ręcznych, żeby potwierdzić, że pattern działa od końca do końca:

1. **Build i uruchom aplikację** w trybie Debug. Brak błędów kompilacji to oczywiste minimum, ale `TreatWarningsAsErrors=true` w niektórych projektach wyłapuje też nieużywane `using` po refaktorze.
2. **Otwórz Model Editor.** W `Application > Options` powinny być widoczne dwa nowe property z sekcji `Behavior`: `BlockDateEditMouseWheelByDefault` (default `True`) i `DateEditMaskCaretMode` (default `Advancing`). Jeśli ich nie ma — krok 2 z wariantu pełnego (`ExtendModelInterfaces`) został pominięty.
3. **Otwórz dowolny detail view z polem daty** w przeglądarce. Kliknij w input daty, przewiń kółkiem — wartość nie powinna się zmienić, caret powinien przeskakiwać między sekcjami po wpisaniu pełnej liczby znaków (np. `28` skoczyć na miesiąc).
4. **Otwórz dropdown daty.** Kalendarz w popupie powinien działać normalnie — selektor JS celuje tylko w `.*-wheel-blocked`, nie w wnętrze popupu.
5. **F12 → Elements → znajdź input daty.** Sprawdź, czy ma klasę `fleetman-dateedit-wheel-blocked` (lub jak nazwałeś ją w swojej aplikacji). Jeśli klasy nie ma — editor nie dostał się do tej kontrolki, sprawdź `[PropertyEditor]` z `isDefaultEditor: true`.
6. **Wyłącz blokadę dla wybranego pola** w Model Editorze (`BlockMouseWheel = False` na konkretnym `MemberViewItem`) lub przez atrybut na property. Po reloadzie input tego pola powinien dostać klasę `fleetman-dateedit-wheel-allowed`, scroll powinien znowu zmieniać wartość, a reszta pól daty na tym samym widoku — zostać zablokowana.
7. **Sprawdź konsolę przeglądarki** pod kątem błędów po pierwszym wejściu na widok z datą. Brak komunikatów typu „Could not import module ./js/..." potwierdza, że kontroler `DateEditMouseWheelGuardController` zadziałał. Jeśli widzisz błąd — najpewniej moduł JS nie został umieszczony w `wwwroot/js/`, albo nazwa pliku jest inna niż w `InvokeAsync<IJSObjectReference>("import", "./js/...")`.

To jest mała zmiana w kodzie, ale duża zmiana w jakości pracy operatora: przewijanie formularza nie zmienia danych, a edytor dalej pozwala wpisywać dokładnie taki zakres informacji, jaki wynika z modelu.
