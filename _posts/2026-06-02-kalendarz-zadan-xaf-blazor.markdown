---
layout: post
title: "Kalendarz zadań w XAF Blazor — przez interfejs IEvent"
---

> **TL;DR**
> - Chcesz pokazać zadania jako kalendarz? Dodaj encji interfejs `IEvent` — XAF użyje `SchedulerListEditor`.
> - `IEvent` zmienia domyślny edytor **wszystkich** list tego typu na scheduler. Tabele przypnij jawnie do `DxGridListEditor`.
> - Daty: na czystym projekcie nazwij pola `StartOn`/`EndOn` wprost; przy istniejącej encji zmapuj je na swoje. W PostgreSQL ustaw `DateTimeKind.Unspecified`.
> - Kolory — `IEvent.Label`/`Status`. Grupowanie po pracowniku — `ResourceClass`. Serie — interfejs `IRecurrentEvent`. Przypomnienia — interfejs `ISupportNotifications`.
> - Koszt: jedna encja z trzema interfejsami, jeden kontroler, kilka linii modelu, cztery migracje.

Jeżeli chcesz, żeby użytkownik widział zadania nie tylko jako tabelę, ale też jako kalendarz — z przeciąganiem terminów, kolorami i przypomnieniami — nie musisz pisać własnego komponentu. W XAF wystarczy, że dodasz encji zadania interfejs `IEvent`. Wtedy XAF użyje gotowego `SchedulerListEditor` w stylu Outlooka.

Kod pochodzi z działającej aplikacji: XAF Blazor, EF Core, PostgreSQL, DevExpress v26.1.

## Punkt wyjścia

Mamy encję `EmployeeTask`. Ma już wszystko, czego potrzebuje kalendarz:

```csharp
public class EmployeeTask : OutlookInspiredBaseObject {
    public virtual string Subject { get; set; }
    public virtual DateTime? StartDate { get; set; }
    public virtual DateTime? DueDate { get; set; }
    public virtual EmployeeTaskStatus Status { get; set; }
    public virtual EmployeeTaskPriority Priority { get; set; }
    public virtual Employee AssignedEmployee { get; set; }
    public virtual ObservableCollection<Employee> AssignedEmployees { get; set; } = new();
    public virtual bool Reminder { get; set; }
    public virtual DateTime? ReminderDateTime { get; set; }
}
```

Użytkownik widzi tylko listę. Nie widzi, kiedy co wypada w miesiącu. Chcemy pokazać **ten sam** rekord również na kalendarzu, bez dublowania encji.

## Dlaczego `IEvent`, a nie własny komponent

Mechanizm nazywa się **List Editor**. To kontrolka, którą XAF dobiera do każdego widoku listy — domyślnie tabela `DxGridListEditor`. [Moduł Scheduler](https://docs.devexpress.com/eXpressAppFramework/112811/event-planning-and-notifications/scheduler-module) dorzuca własny List Editor — [`SchedulerListEditor`](https://docs.devexpress.com/eXpressAppFramework/DevExpress.ExpressApp.Scheduler.Blazor.Editors.SchedulerListEditor) — i przypisuje go klasom z interfejsem `DevExpress.Persistent.Base.General.IEvent`. Dlatego encja z `IEvent` od razu pokazuje się jako kalendarz, a Ty nie budujesz własnego.

Dokumentacja: [List Editors](https://docs.devexpress.com/eXpressAppFramework/113189/ui-construction/list-editors), [Scheduler Module](https://docs.devexpress.com/eXpressAppFramework/112811/event-planning-and-notifications/scheduler-module).

Implementacja `IEvent` daje gotowe:

- widoki dzień / tydzień / miesiąc / oś czasu,
- przeciąganie i rozciąganie kafelków,
- popup edycji wydarzenia,
- cykliczność i zasoby (tory).

Rozważałem dwie inne drogi i obie odrzuciłem:

1. **Własny `DxScheduler` w komponencie Razor.** Więcej kodu, ręczne wiązanie danych, utrata integracji z modelem aplikacji XAF.
2. **Osobna encja „Wydarzenie".** Dublowanie danych i ciągły rozjazd między zadaniem a wydarzeniem.

## Krok 1 — dodaj `IEvent` do istniejącej encji

`IEvent` wymaga pól: `Subject`, `Description`, `StartOn`, `EndOn`, `AllDay`, `Location`, `Label`, `Status`, `Type`, `ResourceId`. Część już mamy, a resztę dodajemy.

Mamy dwie kwestie do rozwiązania — i tu widać różnicę między czystym startem a istniejącą encją.

### Daty

Na czystym projekcie nazwij pola wprost `StartOn`/`EndOn`. My mamy już `StartDate`/`DueDate`, więc zamiast tworzyć nowe kolumny, mapujemy jedno na drugie jawną implementacją interfejsu:

```csharp
// StartOn/EndOn nie dublują kolumn — mapują na StartDate/DueDate.
DateTime IEvent.StartOn {
    get => StartDate ?? DueDate ?? DateTime.Today;
    set => StartDate = DateTime.SpecifyKind(value, DateTimeKind.Unspecified);
}
DateTime IEvent.EndOn {
    get => DueDate ?? (StartDate ?? DateTime.Today).AddHours(1);
    set => DueDate = DateTime.SpecifyKind(value, DateTimeKind.Unspecified);
}
```

PostgreSQL z kolumną `timestamp without time zone` odrzuci datę w UTC — dlatego wymuszamy `DateTimeKind.Unspecified`. To częsty błąd przy Npgsql.

### Kolizja nazwy `Status`

`IEvent.Status` jest typu `int`. U nas `Status` to enum `EmployeeTaskStatus`. Dwóch właściwości o tej samej nazwie mieć nie można.

Na czystym projekcie wystarczy nazwać własne pole inaczej (np. `State`). My zostawiamy enum `Status`, więc `IEvent.Status` implementujemy jawnie, a wartość trzymamy w osobnej kolumnie:

```csharp
public virtual int EventStatus { get; set; }
public virtual int EventLabel { get; set; }

int IEvent.Status { get => EventStatus; set => EventStatus = value; }
int IEvent.Label { get => EventLabel; set => EventLabel = value; }
```

Nowe kolumny (`AllDay`, `Location`, `Type`, `EventLabel`, `EventStatus`) dodajemy migracją:

```bash
dotnet ef migrations add EmployeeTask_IEvent_Calendar
```

To uruchamia kalendarz. Ma jednak skutek uboczny dla pozostałych list.

## Pułapka: `IEvent` zmienia edytor wszystkich list tego typu

Gdy encja dostaje interfejs `IEvent`, domyślny edytor **wszystkich** jej list zmienia się na scheduler. Nie jednej — wszystkich.

Lista „Zadania", lista zadań w karcie klienta, lista w karcie pracownika — każda z nich staje się kalendarzem. Zwykle chcesz to tylko na jednym, wybranym widoku.

Każdą listę, która ma zostać tabelą, przypnij jawnie do `DxGridListEditor`. Schedulerem zostaje jeden, osobny widok.

Robisz to w **Edytorze modelu** ([Model Editor](https://docs.devexpress.com/eXpressAppFramework/112582/ui-construction/application-model-ui-settings-storage/model-editor)) — otwórz plik `Model.xafml` w projekcie platformy (np. `DataDrive.Blazor.Server/Model.xafml`). Edytor modelu ma strukturę drzewa. Rozwiń węzeł **Views** — masz tam wszystkie widoki. Znajdź każdy widok listy zadań (`*_ListView`), zaznacz go i ustaw właściwość **EditorType** na `DxGridListEditor`. Na widoku kalendarza zostaw `SchedulerListEditor`.

Edytor zapisuje te zmiany jako wpisy w `Model.xafml`:

```xml
<!-- tabele zadań — jawnie grid -->
<ListView Id="EmployeeTask_ListView" EditorTypeName="DevExpress.ExpressApp.Blazor.Editors.DxGridListEditor" />
<ListView Id="Customer_Tasks_ListView" EditorTypeName="DevExpress.ExpressApp.Blazor.Editors.DxGridListEditor" />
<ListView Id="Employee_AssignedTasks_ListView" EditorTypeName="DevExpress.ExpressApp.Blazor.Editors.DxGridListEditor" />

<!-- jedyny kalendarz -->
<ListView Id="EmployeeTask_Calendar_ListView"
          EditorTypeName="DevExpress.ExpressApp.Scheduler.Blazor.Editors.SchedulerListEditor"
          SchedulerViewType="Month" />
```

Skąd wiesz, które listy przypiąć? Każda kolekcja typu `EmployeeTask` ma swój widok: `Customer.Tasks` → `Customer_Tasks_ListView`, `Employee.AssignedTasks` → `Employee_AssignedTasks_ListView` i tak dalej. Przejrzyj je wszystkie.

## Krok 2 — przełącznik „Lista / Kalendarz"

W jednym węźle „Zadania" użytkownik przełącza widok. Służy do tego moduł View Variants.

Najpierw klonujemy widok listy na widok kalendarza, na przykład atrybutem `[CloneView]`:

```csharp
[CloneView(CloneViewType.ListView, "EmployeeTask_Calendar_ListView")]
public class EmployeeTask : OutlookInspiredBaseObject, IEvent { /* ... */ }
```

Potem w modelu dodajemy warianty. XAF doda akcję zmiany widoku na pasku:

```xml
<ListView Id="EmployeeTask_ListView" Criteria="Type In (0, 1)">
  <Variants Current="EmployeeTask_ListView">
    <Variant Id="EmployeeTask_ListView" Caption="Lista" ViewID="EmployeeTask_ListView" />
    <Variant Id="EmployeeTask_Calendar_ListView" Caption="Kalendarz" ViewID="EmployeeTask_Calendar_ListView" />
  </Variants>
</ListView>
```

Efekt: ten sam rekord, dwa widoki. Jeden klik przełącza listę na kalendarz.

## Krok 3 — kolory wg priorytetu

Kolory pomagają odróżnić zadania na pierwszy rzut oka. Kolor kafelka biorą `IEvent.Label` i `IEvent.Status`. Mapujemy je z priorytetu i statusu zadania. Logikę trzymamy w encji, nie w kontrolerze:

```csharp
// Wołane w OnSaving/SyncStatusAndCompletion.
void ApplyCalendarColors() {
    EventLabel = (int)Priority;                                    // kolor wg priorytetu
    EventStatus = Status == EmployeeTaskStatus.Completed ? 0 : 2;  // Completed=Free, reszta=Busy
}
```

Zadanie pilne dostaje inny kolor niż zwykłe. Ukończone wygląda lżej.

## Krok 4 — grupowanie zadań po pracowniku

Scheduler pokazuje osobny tor dla każdego pracownika, gdy ustawisz `ResourceClass`:

```xml
<ListView Id="EmployeeTask_Calendar_ListView"
          EditorTypeName="DevExpress.ExpressApp.Scheduler.Blazor.Editors.SchedulerListEditor"
          SchedulerViewType="Month"
          ResourceClass="DataDrive.Module.BusinessObjects.Employee" />
```

Po stronie encji `IEvent.ResourceId` to XML z identyfikatorami pracowników. Gdy użytkownik przeciągnie kafelek na inny tor, scheduler ustawia `ResourceId`, a my odbudowujemy z niego przypisanie:

```csharp
void UpdateResources() {
    while (AssignedEmployees.Count > 0)
        AssignedEmployees.RemoveAt(AssignedEmployees.Count - 1);
    if (string.IsNullOrEmpty(ResourceId)) return;

    var nodes = SafeXml.CreateDocument(ResourceId).DocumentElement!.ChildNodes;
    for (var i = 0; i < nodes.Count; i++) {
        var key = new AppointmentResourceIdXmlLoader(nodes[i]).ObjectFromXml();
        var employee = ObjectSpace.GetObjectByKey(typeof(Employee), key);
        if (employee != null) AssignedEmployees.Add((Employee)employee);
    }
    AssignedEmployee = AssignedEmployees.FirstOrDefault();
}
```

Do danych sięgamy przez `IObjectSpace` (`ObjectSpace.GetObjectByKey`), nie przez `DbContext`. To reguła w XAF — dzięki niej działają zdarzenia i walidacja.

## Krok 5 — cykliczność

Zadanie może się powtarzać. Dochodzi drugi interfejs, `IRecurrentEvent`. Wymaga wzorca powtarzania (`RecurrenceInfoXml`) i odwołania do wzorca serii (`RecurrencePattern`):

```csharp
public class EmployeeTask : OutlookInspiredBaseObject, IEvent, IRecurrentEvent {
    public virtual string RecurrenceInfoXml { get; set; }
    public virtual EmployeeTask RecurrencePattern { get; set; }
    public virtual Guid? RecurrencePatternId { get; set; }

    IRecurrentEvent IRecurrentEvent.RecurrencePattern {
        get => RecurrencePattern;
        set => RecurrencePattern = (EmployeeTask)value;
    }
}
```

Edytor zadań cyklicznych pojawia się w popupie wydarzenia. Ma dwa haczyki.

**Haczyk pierwszy: edycja jednego wystąpienia.** Gdy zmienisz jeden termin z serii, scheduler tworzy **nowy** obiekt (wyjątek) i kopiuje do niego tylko pola z `IEvent`. Pola własne — wykonawca, klient, priorytet — przepadają. Przenosimy je w kontrolerze:

```csharp
public class EmployeeTaskRecurrenceController : ViewController<ListView> {
    private SchedulerListEditorBase _scheduler;

    public EmployeeTaskRecurrenceController() => TargetObjectType = typeof(EmployeeTask);

    protected override void OnActivated() {
        base.OnActivated();
        _scheduler = View.Editor as SchedulerListEditorBase; // null dla gridów
        if (_scheduler != null) _scheduler.ExceptionEventCreated += OnExceptionEventCreated;
    }

    protected override void OnDeactivated() {
        if (_scheduler != null) _scheduler.ExceptionEventCreated -= OnExceptionEventCreated;
        _scheduler = null;
        base.OnDeactivated();
    }

    void OnExceptionEventCreated(object sender, ExceptionEventCreatedEventArgs e) {
        if (e.PatternEvent is EmployeeTask pattern && e.ExceptionEvent is EmployeeTask exception) {
            exception.AssignedEmployee = pattern.AssignedEmployee;
            exception.Customer = pattern.Customer;
            exception.Priority = pattern.Priority;
            exception.Category = pattern.Category;
        }
    }
}
```

Zdarzenie odpinamy w `OnDeactivated`, tam gdzie je podpięliśmy — inaczej grozi wyciek pamięci.

**Haczyk drugi: śmieci na liście.** Surowe wystąpienia serii pojawiłyby się w tabeli zadań. Filtrujemy je na widoku listy: `Criteria="Type In (0, 1)"` pokazuje tylko zwykłe zadania i wzorce serii.

## Krok 6 — przypomnienia

Trzeci interfejs, `ISupportNotifications`, spina kalendarz z alertami XAF. Nie dodajemy nowego pola na datę — `AlarmTime` napełniamy z istniejącego `ReminderDateTime`:

```csharp
public virtual bool IsPostponed { get; set; }

private DateTime? alarmTime;
// AlarmTime to publiczna, mapowana kolumna (nie jawna implementacja interfejsu — patrz pułapka niżej).
public virtual DateTime? AlarmTime {
    get => alarmTime;
    set => alarmTime = value.HasValue
        ? DateTime.SpecifyKind(value.Value, DateTimeKind.Unspecified)
        : null;
}
public string NotificationMessage => Subject;
public object UniqueId => ID;
```

Synchronizację robimy w `OnSaving`:

```csharp
void SyncNotificationAlarm() {
    AlarmTime = Reminder && ReminderDateTime.HasValue ? ReminderDateTime : null;
    if (AlarmTime == null) IsPostponed = false;
}
```

**Pułapka.** Trafiłem na nią na istniejącej, działającej aplikacji — w trakcie przejścia z DevExpress 25.2 na 26.1. Pierwsza wersja używała jawnej implementacji `ISupportNotifications.AlarmTime`. Aplikacja zwróciła `Member 'EmployeeTask.AlarmTime' not found`, a baza błąd `42703`. `NotificationsModule` filtruje rekordy po **publicznym** członku modelu, więc `AlarmTime` musi być zwykłą, mapowaną właściwością. Różnica względem `Status`: tam jawna implementacja działa, tu wywala aplikację.

`NotificationsModule` pokaże popup o właściwej porze. Jedno zastrzeżenie z dokumentacji: typy z podklasami są pomijane. `EmployeeTask` podklas nie ma, więc rejestruje się automatycznie.

## Efekt końcowy

Jeden rekord zadania ma teraz dwa widoki. Kalendarz miesięczny, kolory wg priorytetu, grupowanie po pracowniku, serie cykliczne i przypomnienia.

Kodu jest niewiele: jedna encja z trzema interfejsami, jeden kontroler, kilka linii w modelu i cztery migracje. Resztę zapewnia `SchedulerListEditor` od DevExpress.

## Na co uważać (ściąga)

- `IEvent` zmienia domyślny edytor wszystkich list tego typu → tabele przypnij do `DxGridListEditor`.
- Na greenfieldzie nazwij pola pod interfejs (`StartOn`, `Status` jako int), zamiast mapować.
- W PostgreSQL ustaw `DateTimeKind.Unspecified`.
- `ISupportNotifications.AlarmTime` musi być publicznym polem modelu, nie jawną implementacją interfejsu.
- Edycja wystąpienia serii gubi pola własne → przenoś je w `ExceptionEventCreated`.
- Do danych sięgaj przez `IObjectSpace`, logikę trzymaj w encji.

A Ty jak robisz kalendarze w XAF — natywnym schedulerem czy własnym komponentem? Napisz w komentarzu.
