---
layout: post
title: "Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba"
series: "Dostosowanie demówki XAF Blazor do własnych potrzeb"
series_part: 3
---

> **Część 3 serii: Dostosowanie demówki XAF Blazor do własnych potrzeb**
>
> Bierzemy publiczne `MainDemo.NET.EFCore` od DevExpressa i przerabiamy je krok po kroku tak, żeby wyglądało i działało jak własna aplikacja, nie jak demówka.
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

Lepszy wzorzec jest prosty: custom editor dodaje własną klasę CSS do swojego roota, a JavaScript blokuje scroll tylko pod tą klasą.

```javascript
(function () {
    document.addEventListener('wheel', function (e) {
        var target = e.target;
        if (!target || typeof target.closest !== 'function') {
            return;
        }

        var editableDateControl = target.closest('.fleetman-dateedit-wheel-blocked');
        if (editableDateControl) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
})();
```

Wymagane są trzy szczegóły:

- `capture: true`, żeby złapać zdarzenie zanim zrobi to komponent.
- `passive: false`, bo inaczej przeglądarka może zignorować `preventDefault()`.
- własna klasa CSS dodawana przez editor, a nie selektor po klasach DevExpressa.

## Modelowy przełącznik BlockMouseWheel

Żeby zachowanie było konfigurowalne w XAF, dodaję rozszerzenie modelu:

```csharp
public static class CustomEditorAliases
{
    public const string DateTimeEditor = "CustomDateTimeEditor";
    public const string MouseWheelBlockerCssClass = "fleetman-dateedit-wheel-blocked";
}

public interface IModelMemberViewItemMouseWheel : IModelMemberViewItem
{
    [Category("Behavior")]
    [Description("Gdy ustawione na True, przewijanie kolkiem myszy wewnatrz edytora daty nie zmienia wartosci.")]
    [DefaultValue(true)]
    bool BlockMouseWheel { get; set; }
}
```

Interfejs trzeba zarejestrować w module aplikacji Blazor:

```csharp
public override void ExtendModelInterfaces(ModelInterfaceExtenders extenders)
{
    base.ExtendModelInterfaces(extenders);
    extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
}
```

Od tego momentu w Model Editorze każde pole w `DetailView` może mieć własne `BlockMouseWheel`. Domyślnie wartość jest `true`, więc aplikacja zachowuje się bezpiecznie bez dodatkowej konfiguracji.

Opt-out dla jednego pola:

```text
Application Model
└── Views
    └── SomeObject_DetailView
        └── Items
            └── SomeDate
                BlockMouseWheel = False
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
        DxDateEditMaskProperties.DateTime.CaretMode = MaskCaretMode.Advancing;
        DxDateEditMaskProperties.DateOnly.CaretMode = MaskCaretMode.Advancing;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = MaskCaretMode.Advancing;
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
        DxDateEditMaskProperties.DateTime.CaretMode = MaskCaretMode.Advancing;
        DxDateEditMaskProperties.DateOnly.CaretMode = MaskCaretMode.Advancing;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = MaskCaretMode.Advancing;
    }
}
```

Trzeci parametr `[PropertyEditor(..., true)]` oznacza, że editor jest domyślny dla danego typu. Nie trzeba już dopisywać `[EditorAlias]` do każdej właściwości.

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
- `BlockMouseWheel = False` → scroll działa tylko na tym konkretnym polu.

## Dodanie klasy CSS tylko wtedy, gdy trzeba

Blokada scrolla jest dodatkiem do edytora, a nie globalnym hackiem na wszystkie kontrolki DevExpressa.

```csharp
private static void ApplyMouseWheelBlocker<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model)
{
    if (model is IModelMemberViewItemMouseWheel { BlockMouseWheel: false })
    {
        return;
    }

    adapter.CssClass = string.IsNullOrWhiteSpace(adapter.CssClass)
        ? CustomEditorAliases.MouseWheelBlockerCssClass
        : $"{adapter.CssClass} {CustomEditorAliases.MouseWheelBlockerCssClass}";
}
```

To rozwiązuje dwie rzeczy naraz:

- JavaScript nie dotyka edytorów, które nie są naszym custom editorem.
- Model Editor może wyłączyć blokadę dla pojedynczego `ViewItem`.

## Co było brakującą informacją w pierwszej wersji

Pierwsza wersja opisu była dobra jako demonstracja mechanizmu, ale brakowało w niej trzech informacji potrzebnych do produkcyjnego wdrożenia:

1. **Czy editor ma być globalny, czy opt-in.** W realnej aplikacji lepszy okazał się wariant globalny, bo problem scrolla dotyczy każdego pola daty.
2. **Jak nie zepsuć pól bez godziny.** Globalny editor nie może narzucić `dd.MM.yyyy HH:mm`. Musi uszanować maskę z modelu.
3. **Że blokada scrolla jest zachowaniem editora, nie ogólną regułą JS dla DevExpressa.** Dlatego selektor JS celuje tylko we własną klasę CSS.

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
5. Dodaj rozszerzenie modelu IModelMemberViewItemMouseWheel z bool BlockMouseWheel, Category("Behavior"), DefaultValue(true) i opisem dla Model Editora.
6. Zarejestruj rozszerzenie modelu w module Blazor przez ExtendModelInterfaces:
   extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
7. Domyślnie blokuj scroll myszą wewnątrz edytora daty.
8. Jeśli w Model Editorze dla konkretnego ViewItem ustawiono BlockMouseWheel = False, nie dodawaj klasy CSS blokującej scroll dla tego pola.
9. Blokada scrolla ma działać tylko dla tego custom editora, a nie globalnie dla wszystkich kontrolek DevExpressa.
10. Dodaj własną klasę CSS, np. "myapp-dateedit-wheel-blocked", do adapter.CssClass edytora, gdy BlockMouseWheel nie jest false.
11. Dodaj listener JavaScript dla zdarzenia wheel w fazie capture:
    - { capture: true, passive: false }
    - sprawdź target.closest('.myapp-dateedit-wheel-blocked')
    - wywołaj e.preventDefault()
    - wywołaj e.stopImmediatePropagation()
12. Nie używaj selektorów po wewnętrznych klasach DevExpress typu dxbl-* jako podstawy działania.

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
1. Ustaw MaskCaretMode.Advancing dla:
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
4. Sprawdź, że scroll nad polem z domyślnym BlockMouseWheel nie zmienia wartości.
5. Sprawdź, że po ustawieniu BlockMouseWheel = False dla pojedynczego ViewItem klasa CSS nie jest dodawana i scroll nie jest blokowany przez nasz listener.

Ograniczenia:
1. Nie zmieniaj semantyki istniejących pól datowych.
2. Nie przenoś wszystkich pól na datę z godziną.
3. Nie opieraj rozwiązania na klasach CSS DevExpressa.
4. Nie wyłączaj scrolla globalnie w całej aplikacji.
5. Nie rób osobnego opt-in przez [EditorAlias], chyba że repo ma wyraźny wymóg przeciwny. Domyślnie editor ma być globalny.

Na końcu podaj:
1. listę zmienionych plików,
2. wynik builda,
3. krótką instrukcję, gdzie w Model Editorze wyłączyć BlockMouseWheel dla pojedynczego pola.
```

W praktyce najważniejsze zdanie w tym promptcie to: **"Nie ustawiaj globalnie jednej maski typu `dd.MM.yyyy HH:mm`."** Bez tego agent bardzo łatwo zrobi rozwiązanie, które wygląda poprawnie w jednym polu, ale po wdrożeniu zmieni zachowanie całej aplikacji.

## Checklist wdrożeniowy

1. Dodaj custom property editor dla `DateTime` i `DateTime?` z `isDefaultEditor: true`.
2. Zarejestruj `IModelMemberViewItemMouseWheel` przez `ExtendModelInterfaces`.
3. W JS blokuj `wheel` tylko pod własną klasą CSS, w fazie `capture`.
4. Nie ustawiaj jednej maski globalnie. Czytaj `EditMask` i `DisplayFormat`.
5. Pokazuj sekcję czasu tylko wtedy, gdy maska zawiera czas.
6. Sprawdź pola z maskami `d`, `g`, `dd.MM.yyyy`, `dd.MM.yyyy HH:mm` i `HH:mm`.

To jest mała zmiana w kodzie, ale duża zmiana w jakości pracy operatora: przewijanie formularza nie zmienia danych, a edytor dalej pozwala wpisywać dokładnie taki zakres informacji, jaki wynika z modelu.
