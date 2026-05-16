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

Najważniejsze jest jednak to, żeby nie kończyć na samym opisie. Jeśli ktoś ma to wdrożyć u siebie, musi widzieć konkretne klasy i minimalne fragmenty kodu do skopiowania.

W tym wariancie rdzeń mechanizmu tworzą trzy klasy:

1. `DynamicAppearanceRule` jako encja reguły i implementacja `IAppearanceRuleProperties`,
2. `DynamicAppearanceRuleStorage` jako procesowy cache reguł,
3. `DynamicAppearanceRuleViewController` jako punkt podpięcia do `AppearanceController`.

Minimalny przykład encji wygląda tak:

```csharp
[DefaultClassOptions]
[DefaultProperty(nameof(Name))]
[ImageName("BO_Condition")]
public class DynamicAppearanceRule : BaseObject, IAppearanceRuleProperties {
    [StringLength(256)]
    public virtual string Name { get; set; }

    [StringLength(512)]
    public virtual string ObjectTypeFullName { get; set; }

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

    public virtual string Criteria { get; set; } = "True";
    public virtual string TargetItems { get; set; } = "*";
    public virtual string Context { get; set; } = "Any";
    public virtual string AppearanceItemType { get; set; } = "ViewItem";
    public virtual string ViewId { get; set; }
    public virtual int Priority { get; set; }
}
```

W MainDemo ta klasa ma jeszcze pola dla kolorów, `CssClass`, `Method`, `FontStyle`, `Visibility` i `Enabled`, ale fragment powyżej pokazuje najkrótszy sensowny szkielet.

Ważny jest też zapis do cache przy `OnSaving()`:

```csharp
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
```

Storage może być bardzo prosty:

```csharp
public static class DynamicAppearanceRuleStorage {
    private static readonly Lock SyncRoot = new();
    private static List<DynamicAppearanceRule> rules = new();

    public static void Initialize(IEnumerable<DynamicAppearanceRule> sourceRules) {
        lock(SyncRoot) {
            rules = sourceRules.Where(rule => rule != null).ToList();
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
}
```

A kontroler integrujący z XAF wygląda tak:

```csharp
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

    private void AppearanceController_CollectAppearanceRules(object sender, CollectAppearanceRulesEventArgs e) {
        foreach(var rule in DynamicAppearanceRuleStorage.GetRules(View.ObjectTypeInfo.Type, View.Id)) {
            e.AppearanceRules.Add(rule);
        }
    }
}
```

To jest moment, w którym reguły z bazy zaczynają realnie działać w UI. Sama encja w bazie i sam storage jeszcze niczego nie wyświetlą.

W MainDemo seedowana reguła podświetla zadania po terminie. Działa bez zmian zarówno w podejściu „demo”, jak i jako gotowy punkt wyjścia do osobnego projektu XAF. Najważniejsze jest to, że nie trzeba kopiować całej architektury HIS jeden do jednego. Wystarczy potraktować `IAppearanceRuleProperties` jako kontrakt wejściowy do `AppearanceController` i dołożyć tylko brakującą warstwę danych oraz cache.

Pełna instrukcja z plikami, kolejnością wdrożenia i komendami uruchomieniowymi jest w repo:

[Dynamiczne reguły wyglądu z bazy w XAF Blazor i WinForms](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/CS/docs/dynamiczne-reguly-wygladu-xaf-z-bazy.md)
