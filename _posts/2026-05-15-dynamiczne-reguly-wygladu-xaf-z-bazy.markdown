---
layout: post
title: "Dynamiczne reguły wyglądu z bazy w XAF: encja, cache i AppearanceController"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 5
---

![Dynamiczny wygląd: Magiczna różdżka](/assets/images/dynamic-appearance.png)

Sam `[Appearance]` w klasie biznesowej wystarcza wtedy, gdy reguła ma być stała. Gdy administrator ma zmieniać wygląd bez rekompilacji, reguły muszą stać się danymi.

Taki wariant dodałem do `MainDemo.NET.EFCore`. To rozszerzenie standardowego `ConditionalAppearance` z XAF. Reguły siedzą w bazie jako `DynamicAppearanceRule`, są ładowane do cache `DynamicAppearanceRuleStorage`, a kontroler `DynamicAppearanceRuleViewController` dokłada je do `AppearanceController` przez `CollectAppearanceRules`.

W praktyce wzorzec składa się z siedmiu kroków:

1. włączasz `ConditionalAppearanceModule` w module i hostach,
2. dodajesz encję implementującą `IAppearanceRuleProperties`,
3. dopisujesz `DbSet` do `DbContext`,
4. tworzysz storage z metodami `Initialize`, `Put`, `Remove` i `GetRules`,
5. podpinasz kontroler do `AppearanceController.CollectAppearanceRules`,
6. inicjalizujesz cache przy starcie aplikacji,
7. seedujesz pierwszą regułę albo wystawiasz ekran administracyjny.

Najważniejsze jest jednak to, żeby nie kończyć na samym opisie. Poniżej jest pełny kod z repo.

### `DynamicAppearanceRule.cs`

```csharp
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Drawing;
using DevExpress.ExpressApp;
using DevExpress.ExpressApp.ConditionalAppearance;
using DevExpress.ExpressApp.Editors;
using DevExpress.Persistent.Base;
using DevExpress.Persistent.BaseImpl.EF;
using MainDemo.Module.Storages;

namespace MainDemo.Module.BusinessObjects;

[DefaultClassOptions]
[DefaultProperty(nameof(Name))]
[ImageName("BO_Condition")]
public class DynamicAppearanceRule : BaseObject, IAppearanceRuleProperties {
    private const string DefaultCriteria = "True";
    private const string DefaultTargetItems = "*";
    private const string DefaultContext = "Any";
    private const string DefaultAppearanceItemType = "ViewItem";

    [StringLength(256)]
    public virtual string Name { get; set; }

    [Browsable(false)]
    [StringLength(512)]
    public virtual string ObjectTypeFullName { get; set; }

    [Browsable(false)]
    [StringLength(256)]
    public virtual string ObjectTypeName { get; set; }

    [NotMapped]
    [ImmediatePostData]
    public virtual Type DataType {
        get => string.IsNullOrWhiteSpace(ObjectTypeFullName) ? null : Type.GetType(ObjectTypeFullName);
        set {
            ObjectTypeFullName = value?.AssemblyQualifiedName;
            ObjectTypeName = value?.Name;
        }
    }

    [Column(TypeName = "nvarchar(max)")]
    public virtual string Criteria {
        get;
        set;
    } = DefaultCriteria;

    [StringLength(512)]
    public virtual string TargetItems {
        get;
        set;
    } = DefaultTargetItems;

    [StringLength(128)]
    public virtual string Context {
        get;
        set;
    } = DefaultContext;

    [StringLength(128)]
    public virtual string AppearanceItemType {
        get;
        set;
    } = DefaultAppearanceItemType;

    [StringLength(256)]
    public virtual string ViewId { get; set; }

    public virtual int Priority { get; set; }

    public virtual ViewItemVisibility? Visibility { get; set; }

    public virtual bool? Enabled { get; set; }

    [StringLength(64)]
    [Browsable(false)]
    public virtual string FontColorCss { get; set; }

    [StringLength(64)]
    [Browsable(false)]
    public virtual string BackColorCss { get; set; }

    [StringLength(128)]
    public virtual string CssClass { get; set; }

    [StringLength(128)]
    public virtual string Method { get; set; }

    public virtual DevExpress.Drawing.DXFontStyle? FontStyle { get; set; }

    [NotMapped]
    [Browsable(false)]
    public Type DeclaringType => DataType;

    [NotMapped]
    public Color? FontColor {
        get => ParseColor(FontColorCss);
        set => FontColorCss = ToCssColor(value);
    }

    [NotMapped]
    public Color? BackColor {
        get => ParseColor(BackColorCss);
        set => BackColorCss = ToCssColor(value);
    }

    public override void OnSaving() {
        base.OnSaving();
        var objectSpace = ((IObjectSpaceLink)this).ObjectSpace;
        if(objectSpace != null && objectSpace.IsDeletedObject(this)) {
            DynamicAppearanceRuleStorage.Remove(this);
        }
        else {
            DynamicAppearanceRuleStorage.Put(this);
        }
    }

    public bool Matches(Type objectType, string viewId) {
        if(objectType == null) {
            return false;
        }
        var currentTypeName = NormalizeTypeName(objectType.Name);
        if(!string.Equals(ObjectTypeName, currentTypeName, StringComparison.Ordinal)) {
            return false;
        }
        return string.IsNullOrWhiteSpace(ViewId) || string.Equals(ViewId, viewId, StringComparison.Ordinal);
    }

    internal static string NormalizeTypeName(string typeName) {
        const string proxySuffix = "Proxy";
        if(string.IsNullOrWhiteSpace(typeName)) {
            return typeName;
        }
        return typeName.EndsWith(proxySuffix, StringComparison.Ordinal)
            ? typeName[..^proxySuffix.Length]
            : typeName;
    }

    private static Color? ParseColor(string cssColor) {
        if(string.IsNullOrWhiteSpace(cssColor)) {
            return null;
        }
        try {
            return ColorTranslator.FromHtml(cssColor);
        }
        catch {
            return null;
        }
    }

    private static string ToCssColor(Color? color) {
        if(color == null) {
            return null;
        }
        return ColorTranslator.ToHtml(color.Value);
    }
}
```

### `DynamicAppearanceRuleStorage.cs`

```csharp
using DevExpress.ExpressApp.ConditionalAppearance;
using MainDemo.Module.BusinessObjects;

namespace MainDemo.Module.Storages;

public static class DynamicAppearanceRuleStorage {
    private static readonly Lock SyncRoot = new();
    private static List<DynamicAppearanceRule> rules = new();

    public static void Initialize(IEnumerable<DynamicAppearanceRule> sourceRules) {
        lock(SyncRoot) {
            rules = sourceRules
                .Where(rule => rule != null)
                .ToList();
        }
    }

    public static IReadOnlyList<DynamicAppearanceRule> GetRules() {
        lock(SyncRoot) {
            return rules.ToList();
        }
    }

    public static IReadOnlyList<IAppearanceRuleProperties> GetRules(Type objectType, string viewId) {
        lock(SyncRoot) {
            return rules
                .Where(rule => rule.Matches(objectType, viewId))
                .Cast<IAppearanceRuleProperties>()
                .ToList();
        }
    }

    public static void Put(DynamicAppearanceRule rule) {
        if(rule == null) {
            return;
        }
        lock(SyncRoot) {
            var index = rules.FindIndex(existing => existing.ID == rule.ID);
            if(index >= 0) {
                rules[index] = rule;
            }
            else {
                rules.Add(rule);
            }
        }
    }

    public static void Remove(DynamicAppearanceRule rule) {
        if(rule == null) {
            return;
        }
        lock(SyncRoot) {
            rules.RemoveAll(existing => existing.ID == rule.ID);
        }
    }
}
```

### `DynamicAppearanceRuleViewController.cs`

```csharp
using DevExpress.ExpressApp;
using DevExpress.ExpressApp.ConditionalAppearance;
using DevExpress.ExpressApp.SystemModule;
using MainDemo.Module.Storages;

namespace MainDemo.Module.Controllers;

public class DynamicAppearanceRuleViewController : ObjectViewController<ObjectView, object> {
    private AppearanceController appearanceController;

    protected override void OnActivated() {
        base.OnActivated();
        appearanceController = Frame.GetController<AppearanceController>();
        if(appearanceController == null) {
            return;
        }
        appearanceController.ResetRulesCache();
        appearanceController.CollectAppearanceRules += AppearanceController_CollectAppearanceRules;
        appearanceController.Refresh();
    }

    protected override void OnDeactivated() {
        if(appearanceController != null) {
            appearanceController.CollectAppearanceRules -= AppearanceController_CollectAppearanceRules;
            appearanceController = null;
        }
        base.OnDeactivated();
    }

    private void AppearanceController_CollectAppearanceRules(object sender, CollectAppearanceRulesEventArgs e) {
        if(View?.ObjectTypeInfo?.Type == null) {
            return;
        }
        foreach(var rule in DynamicAppearanceRuleStorage.GetRules(View.ObjectTypeInfo.Type, View.Id)) {
            e.AppearanceRules.Add(rule);
        }
    }
}
```

### `Updater.cs`

```csharp
private void EnsureDynamicAppearanceRules() {
    if(ObjectSpace.FirstOrDefault<DynamicAppearanceRule>(rule => rule.Name == "Highlight overdue tasks") != null) {
        return;
    }

    var rule = ObjectSpace.CreateObject<DynamicAppearanceRule>();
    rule.Name = "Highlight overdue tasks";
    rule.DataType = typeof(DemoTask);
    rule.Criteria = "Status != ##Enum#MainDemo.Module.BusinessObjects.TaskStatus,Completed# && DueDate < LocalDateTimeToday()";
    rule.TargetItems = "Subject;DueDate;AssignedTo";
    rule.Context = "Any";
    rule.AppearanceItemType = nameof(ViewItem);
    rule.Priority = 10;
    rule.FontColor = Color.Firebrick;
    rule.BackColor = Color.MistyRose;
    rule.CssClass = "overdue-task";
}
```

### `DynamicAppearanceRuleTests.cs`

```csharp
using DevExpress.ExpressApp;
using MainDemo.Module.BusinessObjects;
using MainDemo.Module.Storages;
using MainDemo.WebAPI.TestInfrastructure;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace MainDemo.WebAPI.Tests;

public class DynamicAppearanceRuleTests : BaseWebApiTest {
    public DynamicAppearanceRuleTests(SharedTestHostHolder fixture) : base(fixture) { }

    [Fact]
    public void Seeded_dynamic_appearance_rule_exists_in_database() {
        using var scope = fixture.Host.Services.GetRequiredService<IServiceScopeFactory>().CreateScope();
        scope.ServiceProvider.Authenticate("Sam");
        using var objectSpace = scope.ServiceProvider
            .GetRequiredService<IObjectSpaceFactory>()
            .CreateObjectSpace<DynamicAppearanceRule>();

        var rule = objectSpace.FirstOrDefault<DynamicAppearanceRule>(x => x.Name == "Highlight overdue tasks");

        Assert.NotNull(rule);
        Assert.Equal(typeof(DemoTask), rule.DataType);
        Assert.Equal("Subject;DueDate;AssignedTo", rule.TargetItems);
        Assert.Equal("Any", rule.Context);
        Assert.Equal("ViewItem", rule.AppearanceItemType);
        Assert.Equal(System.Drawing.Color.Firebrick, rule.FontColor);
    }

    [Fact]
    public void Storage_returns_rules_only_for_matching_type() {
        using var scope = fixture.Host.Services.GetRequiredService<IServiceScopeFactory>().CreateScope();
        scope.ServiceProvider.Authenticate("Sam");
        using var objectSpace = scope.ServiceProvider
            .GetRequiredService<IObjectSpaceFactory>()
            .CreateObjectSpace<DynamicAppearanceRule>();
        DynamicAppearanceRuleStorage.Initialize(objectSpace.GetObjects<DynamicAppearanceRule>());

        var taskRules = DynamicAppearanceRuleStorage.GetRules(typeof(DemoTask), "AnyView");
        Assert.Contains(taskRules, rule => rule.DeclaringType == typeof(DemoTask));

        var employeeRules = DynamicAppearanceRuleStorage.GetRules(typeof(Employee), "AnyView");
        Assert.DoesNotContain(employeeRules, rule => rule.DeclaringType == typeof(DemoTask));
    }
}
```

W MainDemo seedowana reguła podświetla zadania po terminie. Działa bez zmian zarówno w podejściu „demo”, jak i jako gotowy punkt wyjścia do osobnego projektu XAF. Najważniejsze jest to, że nie trzeba kopiować całej architektury HIS jeden do jednego. Wystarczy potraktować `IAppearanceRuleProperties` jako kontrakt wejściowy do `AppearanceController` i dołożyć tylko brakującą warstwę danych oraz cache.

Pełna instrukcja z plikami, kolejnością wdrożenia i komendami uruchomieniowymi jest w repo:

[Dynamiczne reguły wyglądu z bazy w XAF Blazor i WinForms](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/dynamiczne-reguly-wygladu-xaf-z-bazy.md)
