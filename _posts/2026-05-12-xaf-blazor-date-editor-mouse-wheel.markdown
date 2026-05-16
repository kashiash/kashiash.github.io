---
layout: post
title: "Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 3
---

![DateEditor: Blokada scrolla](/assets/images/date-editor-lock.png)

> **Część 3 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})
> 3. **Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba** — ten wpis

Ten wpis pokazuje dokładnie, jak działa nasz globalny editor daty w `MainDemo.Blazor.Server`.

## Co robi ta zmiana

Editor robi cztery rzeczy:

1. przejmuje wszystkie pola `DateTime` i `DateTime?`,
2. blokuje zmianę wartości przez kółko myszy,
3. pozwala wyłączyć tę blokadę dla wybranego pola,
4. czyta maskę i format z modelu XAF.

## Atrybut dla pojedynczego pola

```csharp
namespace MainDemo.Module.Editors;

[AttributeUsage(AttributeTargets.Property)]
public sealed class DateEditMouseWheelAttribute(bool blockMouseWheel) : Attribute {
    public bool BlockMouseWheel { get; } = blockMouseWheel;
}
```

## Alias editora

```csharp
namespace MainDemo.Module.Editors;

public static class EditorAliases {
    public const string MainDemoDateTimeEditor = "MainDemoDateTimeEditor";
    public const string DocumentPreviewPropertyEditor = "DocumentPreviewPropertyEditor";
    public const string DocumentUploadAreaPropertyEditor = "DocumentUploadAreaPropertyEditor";
    public const string ResumeUploadAreaPropertyEditor = "ResumeUploadAreaPropertyEditor";
}
```

## Editor dla `DateTime`

```csharp
using DevExpress.Blazor;
using DevExpress.ExpressApp.Blazor.Components.Models;
using DevExpress.ExpressApp.Blazor.Editors;
using DevExpress.ExpressApp.Blazor.Editors.Adapters;
using DevExpress.ExpressApp.Editors;
using DevExpress.ExpressApp.Model;
using EditorAliases = MainDemo.Module.Editors.EditorAliases;

namespace MainDemo.Blazor.Server.Editors.Date;

[PropertyEditor(typeof(DateTime), EditorAliases.MainDemoDateTimeEditor, true)]
public class MainDemoDateTimeEditor(Type objectType, IModelMemberViewItem model)
    : DateTimePropertyEditor(objectType, model) {
    protected override void OnControlCreated() {
        base.OnControlCreated();
        if (Control is DxDateEditModel<DateTime> adapter) {
            ConfigureMaskCaretMode();
            MainDemoDateTimeEditorConfigurator.Configure(adapter, Model);
        }
    }

    void ConfigureMaskCaretMode() {
        MaskCaretMode caretMode = MainDemoDateTimeEditorConfigurator.GetMaskCaretMode(Model);
        DxDateEditMaskProperties.DateTime.CaretMode = caretMode;
        DxDateEditMaskProperties.DateOnly.CaretMode = caretMode;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = caretMode;
    }
}
```

## Editor dla `DateTime?`

```csharp
using DevExpress.Blazor;
using DevExpress.ExpressApp.Blazor.Components.Models;
using DevExpress.ExpressApp.Blazor.Editors;
using DevExpress.ExpressApp.Blazor.Editors.Adapters;
using DevExpress.ExpressApp.Editors;
using DevExpress.ExpressApp.Model;
using EditorAliases = MainDemo.Module.Editors.EditorAliases;

namespace MainDemo.Blazor.Server.Editors.Date;

[PropertyEditor(typeof(DateTime?), EditorAliases.MainDemoDateTimeEditor, true)]
public class MainDemoNullableDateTimeEditor(Type objectType, IModelMemberViewItem model)
    : DateTimePropertyEditor(objectType, model) {
    protected override void OnControlCreated() {
        base.OnControlCreated();
        if (Control is DxDateEditModel<DateTime?> adapter) {
            ConfigureMaskCaretMode();
            MainDemoDateTimeEditorConfigurator.Configure(adapter, Model);
        }
    }

    void ConfigureMaskCaretMode() {
        MaskCaretMode caretMode = MainDemoDateTimeEditorConfigurator.GetMaskCaretMode(Model);
        DxDateEditMaskProperties.DateTime.CaretMode = caretMode;
        DxDateEditMaskProperties.DateOnly.CaretMode = caretMode;
        DxDateEditMaskProperties.DateTimeOffset.CaretMode = caretMode;
    }
}
```

## Konfigurator

```csharp
using DevExpress.Blazor;
using DevExpress.ExpressApp.Blazor.Components.Models;
using DevExpress.ExpressApp.Model;
using MainDemo.Module.Editors;

namespace MainDemo.Blazor.Server.Editors.Date;

internal static class MainDemoDateTimeEditorConfigurator {
    static readonly HashSet<char> TimeFormatTokens = new() { 'H', 'h', 's', 't', 'f', 'F', 'K', 'z' };
    static readonly HashSet<string> DateTimeStandardFormats = new(StringComparer.Ordinal) {
        "f", "F", "g", "G", "o", "O", "r", "R", "s", "t", "T", "u", "U"
    };

    public static MaskCaretMode GetMaskCaretMode(IModelMemberViewItem model) {
        if (model?.Application?.Options is IModelOptionsDateEditMouseWheel options) {
            return options.DateEditMaskCaretMode;
        }
        return MaskCaretMode.Advancing;
    }

    public static void Configure<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model) {
        string editMask = NormalizeModelFormat(model?.EditMask);
        string displayFormat = NormalizeModelFormat(model?.DisplayFormat);

        if (!string.IsNullOrWhiteSpace(displayFormat)) {
            adapter.Format = displayFormat;
            adapter.DisplayFormat = displayFormat;
        }

        if (!string.IsNullOrWhiteSpace(editMask)) {
            adapter.Mask = editMask;
        }

        string effectiveFormat = editMask ?? displayFormat;
        bool hasTime = IncludesTimeSection(effectiveFormat);
        adapter.TimeSectionVisible = hasTime;
        if (hasTime) {
            adapter.TimeSectionScrollPickerFormat = "H m";
        }

        ApplyMouseWheelBehavior(adapter, model);
    }

    static void ApplyMouseWheelBehavior<T>(DxDateEditModel<T> adapter, IModelMemberViewItem model) {
        bool shouldBlock = ShouldBlockMouseWheel(model);
        AppendCssClass(adapter, shouldBlock
            ? DateEditorCssAliases.MouseWheelBlocked
            : DateEditorCssAliases.MouseWheelAllowed);
    }

    static bool ShouldBlockMouseWheel(IModelMemberViewItem model) {
        if (model == null) return true;

        var attribute = model.ModelMember?.MemberInfo?.FindAttribute<DateEditMouseWheelAttribute>();
        if (attribute != null) {
            return attribute.BlockMouseWheel;
        }

        if (model is IModelMemberViewItemMouseWheel { BlockMouseWheel: bool viewItemValue }) {
            return viewItemValue;
        }

        if (model.Application?.Options is IModelOptionsDateEditMouseWheel options) {
            return options.BlockDateEditMouseWheelByDefault;
        }

        return true;
    }

    static void AppendCssClass<T>(DxDateEditModel<T> adapter, string cssClass) {
        adapter.CssClass = string.IsNullOrWhiteSpace(adapter.CssClass)
            ? cssClass
            : adapter.CssClass + " " + cssClass;
        adapter.InputCssClass = string.IsNullOrWhiteSpace(adapter.InputCssClass)
            ? cssClass
            : adapter.InputCssClass + " " + cssClass;
    }
}
```

## Interfejs globalnych opcji

```csharp
using System.ComponentModel;
using DevExpress.Blazor;

namespace MainDemo.Blazor.Server.Editors.Date;

public interface IModelOptionsDateEditMouseWheel {
    [Category("Behavior")]
    [Description("Globalne ustawienie domyślne. Gdy True, przewijanie kółkiem myszy wewnątrz edytorów daty nie zmienia wartości pola.")]
    [DefaultValue(true)]
    bool BlockDateEditMouseWheelByDefault { get; set; }

    [Category("Behavior")]
    [Description("Globalny tryb przesuwania kursora w maskach edytorów daty. Advancing oznacza, że kursor sam przeskakuje do następnej sekcji po wpisaniu maksymalnej liczby znaków.")]
    [DefaultValue(MaskCaretMode.Advancing)]
    MaskCaretMode DateEditMaskCaretMode { get; set; }
}
```

## Interfejs opcji pola w widoku

```csharp
using System.ComponentModel;
using DevExpress.ExpressApp.Model;

namespace MainDemo.Blazor.Server.Editors.Date;

public interface IModelMemberViewItemMouseWheel : IModelMemberViewItem {
    [Category("Behavior")]
    [Description("Opcjonalne ustawienie dla konkretnego pola. Null oznacza: użyj wartości z Options.BlockDateEditMouseWheelByDefault.")]
    bool? BlockMouseWheel { get; set; }
}
```

## Stałe klas CSS

```csharp
namespace MainDemo.Blazor.Server.Editors.Date;

public static class DateEditorCssAliases {
    public const string MouseWheelBlocked = "maindemo-dateedit-wheel-blocked";
    public const string MouseWheelAllowed = "maindemo-dateedit-wheel-allowed";
}
```

## Kontroler ładujący JS

```csharp
using DevExpress.ExpressApp;
using DevExpress.Persistent.Base;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.JSInterop;

namespace MainDemo.Blazor.Server.Editors.Date;

public class DateEditMouseWheelGuardController : ViewController {
    IJSRuntime jsRuntime;

    protected override void OnActivated() {
        base.OnActivated();
        jsRuntime = Application?.ServiceProvider?.GetService<IJSRuntime>();
    }

    protected override void OnViewControlsCreated() {
        base.OnViewControlsCreated();
        _ = RegisterWheelGuard();
    }

    async Task RegisterWheelGuard() {
        if (jsRuntime == null) {
            return;
        }
        try {
            var module = await jsRuntime.InvokeAsync<IJSObjectReference>(
                "import",
                "./js/maindemo-date-edit-wheel-guard.js");
            await module.InvokeVoidAsync("ensureRegistered");
            await module.DisposeAsync();
        }
        catch (JSException ex) {
            Tracing.Tracer.LogError(ex);
        }
    }
}
```

## Moduł JavaScript

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

        if (target.closest('.maindemo-dateedit-wheel-allowed')) {
            return;
        }

        if (target.closest('.maindemo-dateedit-wheel-blocked')) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    }, { capture: true, passive: false });
}
```

## Rejestracja w module Blazor

```csharp
public override void ExtendModelInterfaces(ModelInterfaceExtenders extenders) {
    base.ExtendModelInterfaces(extenders);
    extenders.Add<IModelOptions, IModelOptionsDateEditMouseWheel>();
    extenders.Add<IModelMemberViewItem, IModelMemberViewItemMouseWheel>();
}
```

## Wyjątek na polu `Employee.Birthday`

```csharp
[DateEditMouseWheel(false)]
public virtual DateTime? Birthday { get; set; }
```

## Kolejność decyzji

Blokada kółka jest wyliczana w tej kolejności:

1. atrybut na właściwości,
2. ustawienie `BlockMouseWheel` w modelu widoku,
3. ustawienie globalne `BlockDateEditMouseWheelByDefault`.

## Zmienione pliki

```text
CS/MainDemo.Module/Editors/DateEditMouseWheelAttribute.cs
CS/MainDemo.Module/Editors/EditorAliases.cs
CS/MainDemo.Blazor.Server/Editors/Date/MainDemoDateTimeEditor.cs
CS/MainDemo.Blazor.Server/Editors/Date/MainDemoNullableDateTimeEditor.cs
CS/MainDemo.Blazor.Server/Editors/Date/MainDemoDateTimeEditorConfigurator.cs
CS/MainDemo.Blazor.Server/Editors/Date/IModelOptionsDateEditMouseWheel.cs
CS/MainDemo.Blazor.Server/Editors/Date/IModelMemberViewItemMouseWheel.cs
CS/MainDemo.Blazor.Server/Editors/Date/DateEditorCssAliases.cs
CS/MainDemo.Blazor.Server/Editors/Date/DateEditMouseWheelGuardController.cs
CS/MainDemo.Blazor.Server/wwwroot/js/maindemo-date-edit-wheel-guard.js
CS/MainDemo.Blazor.Server/BlazorModule.cs
CS/MainDemo.Module/BusinessObjects/Employee.cs
```
