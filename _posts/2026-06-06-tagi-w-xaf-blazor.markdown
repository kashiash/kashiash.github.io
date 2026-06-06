---
layout: post
title: "Tagi w XAF Blazor — ręczne, regułowe i automatyczne"
---

Jeżeli chcesz, żeby użytkownik oznaczał rekordy etykietami i filtrował po nich listy, musisz dorobić kilka rzeczy. Część etykiet ma się nadawać sama, według warunku. Razem to encja tagu, relacja wiele-do-wielu, kontroler akcji i silnik reguł. Standardowy XAF nie daje tego z pudełka. Dalej pokazuję działający komplet na EF Core i PostgreSQL.

## Po co to użytkownikowi

Wyobraź sobie trzy sytuacje z floty. Handlowiec chce widzieć klientów „VIP". Księgowa filtruje faktury oznaczone jako „sporne". Serwisant szuka pojazdów „do serwisu".

Tag to wspólny mechanizm na wszystkie te przypadki. Jedna etykieta wisi na wielu rekordach, jeden rekord ma wiele etykiet. Do tego dochodzi automat: reguła „faktura przeterminowana → tag Przeterminowana" nadaje etykietę bez kliknięcia.

## Encja tagu i wspólny interfejs

Tag trzyma nazwę, opcjonalne ostrzeżenie i zawężenie do typu obiektu. Ostrzeżenie to krótki tekst, który trafia na oznaczony rekord (np. „Wymagane pełnomocnictwo").

```csharp
public class Tag : AuditBaseObject {
    public virtual string Name { get; set; }
    public virtual string Warning { get; set; }      // tekst dopinany do rekordu
    public virtual bool Global { get; set; }          // dostępny dla każdego typu
    public virtual string ObjectTypeName { get; set; } // albo zawężony do typu
    // kolekcje zwrotne: Customers, Vehicles, FinancialDocuments
}
```

Encje, które chcesz tagować, dostają wspólny interfejs. To on pozwala napisać jeden kontroler i jeden automat dla wszystkich typów naraz.

```csharp
public interface ITaggable {
    IList<Tag> Tags { get; set; }
    string TagWarning { get; set; }
}
```

U mnie interfejs noszą `Customer`, `Vehicle` i `FinancialDocument`. Ten ostatni to baza hierarchii faktur, więc tag obejmuje wszystkie podklasy.

## Relacja wiele-do-wielu przez jawną encję łączącą

Tag i rekord łączy trzecia tabela. Zapisuje pojedyncze pary „ten klient ma ten tag". W EF Core masz dwie drogi: niejawną i jawną.

Wybierz jawną — własną klasę z pojedynczym kluczem Guid. Przy niejawnej relacji (sama kolekcja `Tags` plus `HasMany().WithMany()`) `dotnet ef migrations` bywa zawodne i wymaga ręcznej poprawki nazw kolumn. XAF też woli pojedynczy klucz, nie złożony.

```csharp
public class CustomerTag : OutlookInspiredBaseObject {
    public virtual Customer Customer { get; set; }
    public virtual Tag Tag { get; set; }
}
```

Relację konfigurujesz w `OnModelCreating`:

```csharp
modelBuilder.Entity<Customer>()
    .HasMany(c => c.Tags)
    .WithMany(t => t.Customers)
    .UsingEntity<CustomerTag>(
        right => right.HasOne(ct => ct.Tag).WithMany().OnDelete(DeleteBehavior.Cascade),
        left  => left.HasOne(ct => ct.Customer).WithMany().OnDelete(DeleteBehavior.Cascade));
```

Cena: jedna encja łącząca na każdy tagowalny typ. W zamian masz stabilne migracje.

## Ręczne tagowanie — jeden kontroler na wszystkie typy

Dzięki interfejsowi `ITaggable` piszesz kontroler raz. Działa na liście dowolnej tagowalnej encji.

```csharp
public class TaggableListViewController : ObjectViewController<ListView, ITaggable> {
    // akcje: Dodaj tag, Filtruj po tagu, Usuń tag (PopupWindowShowAction)
}
```

Akcja „Dodaj tag" otwiera popup z listą tagów. Lista pokazuje tylko tagi danego typu albo globalne:

```csharp
listView.CollectionSource.Criteria[FilterKey] =
    CriteriaOperator.Parse("Archival = False And (Global = True Or ObjectTypeName = ?)", targetTypeName);
```

Po wyborze tag ląduje na zaznaczonych rekordach, a jego ostrzeżenie dopina się do pola `TagWarning`. Filtr listy używa składni kolekcyjnej XAF:

```csharp
View.CollectionSource.Criteria[FilterKey] = CriteriaOperator.Parse("Tags[ID = ?]", tag.ID);
```

## Automat — reguła, rdzeń i worker

Automat ma trzy części. Reguła mówi „co i komu", rdzeń ją wykonuje, worker odpala rdzeń cyklicznie.

Reguła to zwykła encja. Warunek wpisujesz w edytorze kryteriów XAF:

```csharp
public class AutoTagRule : BaseObject {
    public Type DataType { get; set; }        // np. Vehicle
    public virtual string Criteria { get; set; } // np. Contains(RegistrationNo, 'SERWIS')
    public virtual Tag Tag { get; set; }
    public virtual bool Active { get; set; } = true;
}
```

Rdzeń jest celowo oddzielony od UI i od tła. Bierze `IObjectSpace`, przechodzi aktywne reguły, nakłada tagi i zwraca liczbę nowych. Nie woła `CommitChanges` — robi to wywołujący:

```csharp
public int Apply(IObjectSpace objectSpace) {
    var newlyTagged = 0;
    foreach (var rule in GetActiveRules(objectSpace)) {
        var candidates = objectSpace.GetObjects(rule.DataType, CriteriaOperator.Parse(rule.Criteria));
        var tag = objectSpace.GetObject(rule.Tag);
        foreach (var candidate in candidates) {
            if (candidate is not ITaggable taggable || taggable.Tags.Contains(tag)) continue;
            taggable.Tags.Add(tag);
            ApplyWarning(taggable, tag);
            newlyTagged++;
        }
    }
    return newlyTagged;
}
```

Taki podział się opłaca. Rdzeń przetestujesz na prawdziwej bazie bez UI i bez wątku w tle. Test sprawdza dwie rzeczy: nadanie po warunku i brak duplikatu przy drugim przebiegu.

Worker tylko owija rdzeń. Dziedziczy po bazie, która przechodzi po bazach wszystkich najemców (multi-tenant):

```csharp
protected override Task ProcessTenantAsync(IServiceProvider s, IObjectSpace os, Tenant t, CancellationToken ct) {
    var applied = new AutoTagApplier().Apply(os);
    if (applied > 0) os.CommitChanges();
    return Task.CompletedTask;
}
```

## Kolor bez nowego kodu

Kolorowanie wiersza po tagu zrób regułą wyglądu, nie nowym mechanizmem. Jeśli masz już silnik reguł wyglądu z kryterium XAF, podaj mu warunek:

```
Tags[Name = 'Pilne']
```

Wiersz z tagiem „Pilne" dostaje kolor. Bez dodatkowej linii kodu w encji.

## Pułapki, na które wpadłem

**Host `InMemory` wykładał worker.** Domyślny host ma connection string `"InMemory"`. Baza workera podawała ten napis wprost do `new NpgsqlConnection(...)` i dostawała `Format of the initialization string ... index 0`. Dodaj guard: gdy host to `InMemory`, pomiń tick z ostrzeżeniem zamiast crashu.

**Kolizja `Required`.** `DevExpress.ExpressApp.Model` ma własny `RequiredAttribute`. W encji z `[Required]` z DataAnnotations nie importuj tego namespace — kwalifikuj `ModelDefault` pełną nazwą.

**Nazwy kolumn FK w migracji.** Po `dotnet ef migrations add` sprawdź, czy klucze obce to `CustomerID`/`TagID`, a nie `CustomersID`. Przy niejawnej relacji nazwy bywają błędne.

**`DateTime.Kind`.** Globalna konwencja wymusza `timestamp without time zone`. Daty ustawiaj jako `Unspecified`, nigdy `DateTime.UtcNow`.

## Podsumowanie

Tagi to cztery klocki: encja tagu, jawna encja łącząca, kontroler akcji i silnik reguł. Interfejs `ITaggable` spina je tak, że kontroler i automat działają na każdym tagowalnym typie. Rdzeń automatu trzymaj poza UI i tłem — wtedy go przetestujesz. Kolor oddaj istniejącemu silnikowi wyglądu.
