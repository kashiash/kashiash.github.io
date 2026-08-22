---
layout: post
title: "Gantt sterowany rozmową: model proponuje, człowiek zatwierdza"
description: "Wykres Gantta w Syncfusion Blazor, sterowany poleceniami po polsku. Wzorzec propozycja-podgląd-zatwierdzenie, drabina modeli z eskalacją i trzy pułapki SfGantt, które nie rzucają wyjątku."
date: 2026-08-22
categories: blazor syncfusion ai
---

![Ekran: czat u góry, wykres Gantta pod spodem](/assets/images/gantt-rozmowa-uklad.png)

> Pełna wersja — wszystkie prompty co do słowa, komplet zrzutów i tabele testów — jest na osobnej stronie: [Gantt sterowany rozmową, opis pełny](/gantt-ai.html).

Chciałem sprawdzić, czy da się pisać do harmonogramu robót po polsku. „Przesuń wylewkę o trzy dni", „dodaj próbę szczelności po przewiertach" — i żeby wykres sam się przestawił. Da się. Tylko nie tak, jak podpowiada pierwsza myśl.

Pierwsza myśl to podłączyć modelowi tool calling i pozwolić mu wołać `AddTask`, `UpdateTask`, `ShiftTask`. Odradzam. Harmonogram budowy to nie notatnik — polecenie „przesuń wszystko o tydzień" dotyka kilkudziesięciu pozycji naraz, a cofnięcia nie ma. Model, który sam wykonuje operacje, jest o jedną halucynację od zaorania planu robót.

Zbudowałem to inaczej: **model nie pisze po Gantcie, tylko proponuje**.

## Cztery etapy, jeden punkt zatrzymania

Polecenie idzie do modelu razem z kompaktowym zrzutem harmonogramu. Model zwraca JSON z listą operacji. Kod sprawdza tę listę wobec aktualnych danych, zamienia na opis po polsku i pokazuje jako propozycję. Dopiero kliknięcie **Zastosuj** rusza dane.

Trzy pierwsze etapy to automat. Czwarty to człowiek. Granica leży dokładnie tam, gdzie zaczyna się nieodwracalność.

Schemat komend trzymam prosty:

```json
{
  "komentarz": "jedno zdanie po polsku",
  "komendy": [
    {"akcja": "dodaj", "nazwa": "Próba szczelności", "dni": 1, "rodzic": 8, "poprzednik": "14FS"},
    {"akcja": "przesun", "id": 7, "dni": 3},
    {"akcja": "zmien", "id": 7, "postep": 40},
    {"akcja": "usun", "id": 11},
    {"akcja": "kamien", "id": 12}
  ]
}
```

Świadomie nie użyłem natywnego tool callingu. JSON w trybie `response_format: json_object` jest przenośny między dostawcami, łatwo go zwalidować i — co ważniejsze — łatwo go **odrzucić w całości**, gdy coś nie gra. Przy tool callingu każde wywołanie żyje własnym życiem.

Podgląd liczę zawsze wobec prawdziwych danych, nie wobec tego, co model napisał w komentarzu:

```csharp
case "zmien":
    if (task is null) { result.Add(new(k, "zmiana", $"nie ma zadania {k.Id}")); break; }
    var czesci = new List<string>();
    if (k.Nazwa is not null) czesci.Add($"nazwa → „{k.Nazwa}”");
    if (k.Dni is not null) czesci.Add($"czas {task.Duration} → {k.Dni} dni");
    if (k.Postep is not null) czesci.Add($"postęp {task.Progress}% → {k.Postep}%");
    result.Add(czesci.Count == 0
        ? new(k, $"zmień „{task.Name}”", "nie podano żadnego pola do zmiany")
        : new(k, $"„{task.Name}”: {string.Join(", ", czesci)}", null));
    break;
```

Użytkownik czyta „Przewierty przez ściany: czas 2 → 4 dni", a nie „ok, zmieniłem". Różnica jest zasadnicza: pierwsze da się sprawdzić wzrokiem.

## Drabina modeli, czyli po co eskalacja

Domyślnie odpowiada najtańszy model z rodziny. Wyżej pytanie idzie tylko wtedy, gdy trzeba. Klient dostaje walidator jako parametr:

```csharp
public async Task<Result> AskAsync(
    string systemPrompt,
    string userPrompt,
    Func<string, string?>? accept = null,   // null = dobra odpowiedź, tekst = powód eskalacji
    bool jsonMode = false,
    CancellationToken ct = default)
{
    string? lastReason = null;

    for (var step = 0; step < Ladder.Count; step++)
    {
        var model = Ladder[step];
        string text;

        try { text = await CallAsync(model, systemPrompt, userPrompt, jsonMode, ct); }
        catch (EscalateException ex) { lastReason = ex.Message; continue; }

        var rejection = accept?.Invoke(text);
        if (rejection is null) return new Result(text, model, step, lastReason, true);

        lastReason = rejection;
    }

    return new Result($"Żaden model nie dał użytecznej odpowiedzi. Ostatni powód: {lastReason}",
        Ladder[^1], Ladder.Count - 1, lastReason, false);
}
```

Oczywiste wyzwalacze to 429 i piątki — każdy model ma osobną pulę przepustowości, więc wyżej może się udać od razu. Do tego niepoprawny JSON i nieznana akcja.

Czwarty wyzwalacz kosztował mnie najwięcej myślenia i jest najważniejszy: **model odwołał się do zadania, którego nie ma**.

W pierwszej wersji walidator dostawał tylko surowy tekst odpowiedzi. Sprawdzał składnię i przepuszczał wszystko, co było poprawnym JSON-em. Efekt: model wymyślał numer zadania 47, walidacja przechodziła, eskalacja się nie odpalała, a użytkownik widział „pominięte: nie ma zadania 47". Najczęstszy błąd małego modelu był jednocześnie jedynym, który nie eskalował.

Poprawka jest banalna i cała siedzi w sygnaturze — walidator musi widzieć dane:

```csharp
public static string? Validate(string raw, IReadOnlyCollection<GanttTask> tasks)
{
    var plan = Parse(raw);
    if (plan is null) return "odpowiedź nie jest obiektem JSON";

    var znaneId = tasks.Select(t => t.Id).ToHashSet();

    foreach (var k in plan.Komendy)
    {
        if (!ZnaneAkcje.Contains(k.Akcja)) return $"nieznana akcja '{k.Akcja}'";
        if (k.Id is { } id && !znaneId.Contains(id)) return $"zadanie {id} nie istnieje";
        if (k.Rodzic is { } r && !znaneId.Contains(r)) return $"zadanie nadrzędne {r} nie istnieje";
    }
    return null;
}
```

Wniosek szerszy niż ten POC: **walidator, który nie widzi stanu aplikacji, przepuszcza dokładnie te błędy, dla których go napisałeś.**

## Trzy pułapki SfGantt, które nie rzucają wyjątku

Tu zaczyna się część, dla której warto było to zbudować. Wszystkie trzy błędy były ciche — bez wyjątku, bez wpisu w logu serwera, bez błędu w konsoli przeglądarki. Dokumentacja prowadzi wprost do dwóch pierwszych.

### Znikające zadanie

Mutujesz kolekcję i wołasz `RefreshAsync()`. Działa. Dopóki nowe zadanie nie zależy od zadania, które też dodałeś w tej samej sesji.

Dodałem „Przewierty przez ściany" z zależnością `9FS` — pojawiło się. Potem „Próbę szczelności" z zależnością `14FS`, gdzie 14 to były właśnie przewierty. Licznik pokazał 15 pozycji w kolekcji. Wykres narysował 14 wierszy. Zadanie po prostu nie istniało na ekranie.

`RefreshAsync()` dobudowuje wiersze do istniejącego drzewa. Rekord, którego poprzednik sam był dobudowany, wypada poza drzewo.

### Niewidoczna zmiana

Przeszedłem na `AddRecordAsync()` — oficjalną metodę dodawania. Zadanie się pojawiło. Za to przestały działać zmiany.

Poleciłem wydłużyć przewierty o 2 dni. Panel podglądu pokazał poprawne „czas 2 → 4 dni". Kliknąłem Zastosuj. Wykres dalej rysował 2 dni.

Powód: `AddRecordAsync()` trzyma **własną kopię rekordu**. Moja kolekcja i drzewo komponentu rozjechały się na tym jednym obiekcie. Podgląd czytał z kolekcji, więc pokazywał prawdę o danych — tyle że wykres rysował coś innego.

To najgorszy wariant z możliwych: interfejs potwierdza zmianę, której nie widać.

### Co ostatecznie zadziałało

`@key` na komponencie, podbijany po każdej zatwierdzonej zmianie:

```razor
<SfGantt @key="RenderKey" DataSource="@Tasks" TValue="GanttTask" ...>
```

```csharp
private void ApplyPending()
{
    if (Pending is null) return;

    GanttPlanner.Apply(Pending, Tasks);
    Pending = null;

    // Kolekcja jest jedynym źródłem prawdy, więc Gantt musi zbudować drzewo od nowa.
    RenderKey++;
}
```

Komponent odtwarza się i buduje drzewo od zera z kolekcji. Kolekcja zostaje jedynym źródłem prawdy, rozjazd znika.

Cena jest realna: drzewo się zwija, przewijanie wraca na początek. Przy kilkunastu zadaniach nie przeszkadza. Przy kilkuset będzie widać i wtedy właściwą drogą jest `SfDataManager` z własnym adaptorem — CRUD przez `InsertAsync`, `UpdateAsync` i `RemoveAsync`, komponent sam wie, co przerysować. Nie potrzebowałem tego w POC, ale w produkcji bym tak zrobił.

## Trzecia pułapka: przesuwanie tego, co trzyma zależność

Ta nie ma nic wspólnego z odświeżaniem. Ta jest o tym, że rozumiałem Gantta źle.

Poleciłem przesunąć wylewkę posadzki o 3 dni. Panel pokazał „25.08 → 28.08". Zastosuj. Pasek nie drgnął.

Wylewka ma zależność `6FS`. Przy `EnablePredecessorValidation="true"` Gantt liczy termin z poprzednika i natychmiast cofa każdą datę, która się z tym kłóci. Ustawianie `StartDate` na takim zadaniu jest bezcelowe — komponent to nadpisze, zanim zdążysz mrugnąć.

Sprawdziłem hipotezę drugim testem: przesunięcie prac przygotowawczych, które nie mają poprzednika, zadziałało od razu i pociągnęło całą kaskadę.

Jedyna dźwignia, która naprawdę przesuwa zadanie z zależnością, to przesunięcie wpisane **w samą zależność**: `6FS` → `6FS+3`. Więc planer rozpoznaje to sam:

```csharp
case "przesun":
    // Zadanie z zależnością ma termin narzucony przez poprzednika: zmiana daty
    // startu zostanie natychmiast cofnięta przez walidację zależności.
    if (!string.IsNullOrWhiteSpace(task.Predecessor))
    {
        var link = ParseLink(task.Predecessor);
        if (link is null)
        {
            result.Add(new(k, $"przesuń „{task.Name}”",
                $"zależność „{task.Predecessor}” ma postać, której nie umiem bezpiecznie zmienić"));
            break;
        }

        var docelowy = link.Value with { Offset = link.Value.Offset + k.Dni.Value };
        result.Add(new(k, $"przesuń „{task.Name}” o {ile} dni {kier} — zależność {link.Value} → {docelowy}", null));
        break;
    }

    // Bez zależności przesuwamy datę, razem z zadaniami podrzędnymi.
    var nowy = task.StartDate.AddDays(k.Dni.Value);
    result.Add(new(k, $"przesuń „{task.Name}” o {ile} dni {kier}: {task.StartDate:dd.MM} → {nowy:dd.MM}", null));
    break;
```

Zwróć uwagę, że użytkownik widzi w podglądzie **prawdę o mechanizmie**: „zależność 6FS → 6FS+3", a nie zmyśloną datę. Jeśli operacja polega na czym innym, niż się wydaje, podgląd ma o tym mówić.

![Panel propozycji: zależność 6FS → 6FS+3](/assets/images/gantt-rozmowa-propozycja.png)

*Propozycja przed zatwierdzeniem. Panel mówi wprost, co się zmieni — zależność, nie data.*

![Wykres po zatwierdzeniu: wylewka na 28.08, w kolumnie zależności 6FS+3 days](/assets/images/gantt-rozmowa-po-zastosowaniu.png)

*Po zatwierdzeniu. Wylewka stoi na 28.08, w kolumnie zależności widnieje `6FS+3 days`.*

Sam zapis zależności ma więcej wariantów, niż widać na pierwszy rzut oka. Parser dostał osobny zestaw przypadków:

| Wejście | Wynik | Dlaczego |
|---|---|---|
| `6fs` | `6FS` | wielkość liter bez znaczenia |
| `6FS+2d` | `6FS+2` | Syncfusion dopuszcza jednostkę po liczbie |
| `3FF+10` | `3FF+10` | typ inny niż FS też działa |
| `6FS,7FS` | `null` | wielu poprzedników — nie zgadujemy, do którego dopisać |
| `6XX` | `null` | nieznany typ zależności |

Gdy parser zwróci `null`, zmiana ląduje na liście jako pominięta, z podanym powodem. Nie ruszam zapisu, którego nie rozumiem — to jedyna uczciwa reakcja.

Operacja jest symetryczna: „cofnij o 3 dni" sprowadza `6FS+3` z powrotem do `6FS`, a data wraca tam, gdzie była. Sprawdzone w obie strony.

## Co z tego wyszło

Sekwencja czterech poleceń pod rząd, każde zatwierdzone ręcznie:

1. „Dodaj zadanie Montaż bramy segmentowej, 2 dni, start 26.08" → nowe zadanie bez zależności.
2. „Dodaj pod Instalacjami Przewierty przez ściany, 2 dni, po montażu opraw" → zadanie z `9FS`.
3. „Dodaj pod Instalacjami Próbę szczelności, 1 dzień, po przewiertach" → zadanie z `14FS`.
4. „Wydłuż przewierty o 2 dni" → przewierty 2 → 4 dni, próba szczelności sama przesuwa się o 2 dni, grupa nadrzędna rośnie z 7 na 9 dni.

![Krok 2: zadanie „Przewierty przez ściany" wpięte pod Instalacje z zależnością 9FS](/assets/images/gantt-rozmowa-krok2.png)

*Krok 2. Nowe zadanie wchodzi w środek łańcucha instalacji, z zależnością `9FS`.*

![Krok 3: zadanie „Próba szczelności" z zależnością 14FS](/assets/images/gantt-rozmowa-krok3.png)

*Krok 3. Próba szczelności zależy od przewiertów, czyli od zadania dodanego chwilę wcześniej. To dokładnie ten przypadek, który w pierwszej wersji ginął.*

![Krok 4: po wydłużeniu przewiertów kaskada przesuwa próbę szczelności i rozciąga grupę](/assets/images/gantt-rozmowa-krok4.png)

*Krok 4. Wydłużenie przewiertów o 2 dni. Próba szczelności przeskakuje na 3.09, grupa Instalacje rośnie z 7 na 9 dni — o żadnym z nich polecenie nie wspominało.*

Ostatni krok jest tym, po co to wszystko. Polecenie nie wspomniało ani o próbie szczelności, ani o grupie nadrzędnej. Gantt policzył kaskadę sam, bo dostał poprawne dane — a dostał je, bo człowiek popatrzył na listę zmian i kliknął.

Najtańszy model z rodziny obsłużył wszystkie polecenia. Ani razu nie trzeba było eskalować. Co nie znaczy, że drabina jest zbędna — znaczy tylko, że na dwunastu zadaniach zadanie jest łatwe. Przy stu pozycjach i poleceniach w rodzaju „przesuń wszystko po odbiorze instalacji" spodziewam się innych wyników.

Rzecz, którą zabieram dalej: **czas poszedł nie na model, tylko na komponent**. Prompt działał od pierwszego podejścia. Trzy dni zeszły na zrozumienie, kiedy `SfGantt` rysuje to, co ma w kolekcji, a kiedy coś zupełnie innego. Jeśli budujesz podobną rzecz, planuj budżet odwrotnie, niż podpowiada intuicja.
