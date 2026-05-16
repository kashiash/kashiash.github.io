---
layout: post
title: "Branding w Blazorze: logo, splash screen i motywy"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 2
---

![Branding w Blazorze: Malowanie łodzi](/assets/images/branding-blazor.png)

> **Część 2 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> Nie tworzymy aplikacji od zera — postawienie projektu XAF Blazor + EF Core jest krok po kroku opisane w [oficjalnej dokumentacji DevExpress](https://docs.devexpress.com/eXpressAppFramework/) i to jest miejsce, w którym każdy może (i powinien) zacząć. My ciągniemy ten temat dalej: bierzemy publiczny projekt referencyjny `MainDemo.NET.EFCore` i pokazujemy, co dochodzi w nim po stronie realnego wdrożenia.
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. **Branding: logo, splash screen i motywy** — ten wpis
> 3. [Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

Branding w Blazorze najczęściej psuje się w trzech miejscach: na starcie, po zalogowaniu i w loaderze. Aplikacja działa, ale użytkownik od razu widzi niespójność.

Opisuję to tak, żeby dało się do tego wrócić i wdrożyć to drugi raz bez zgadywania.

## Gdzie ten branding naprawdę siedzi

Na pierwszy rzut oka wygląda to prosto: podmiana SVG. W tym układzie zwykle są co najmniej trzy miejsca:

- pełne logo przed spinnerem,
- obrazek w splash screenie,
- logo w headerze po wejściu do aplikacji.

Czasem dochodzi jeszcze czwarty element: układ motywów po prawej stronie. To nie jest logo, ale wpływa na odbiór całego ekranu.

## Najpierw porządek w plikach, potem reszta

Ja wolę mieć to rozdzielone brutalnie prosto:

```text
wwwroot/images/
  Logo.svg
  FullLogo.svg
  SplashScreen.svg
```

I koniec filozofii.

- `Logo.svg` - to, co siedzi w headerze,
- `FullLogo.svg` - szeroki znak przed spinnerem,
- `SplashScreen.svg` - środek właściwego loadera.

Jak nie rozdzielisz tych ról, to później agent AI albo drugi programista podmieni „logo”, ale nie to logo, które trzeba.

## Pierwsze miejsce do sprawdzenia: `_Host.cshtml`

W moim przypadku to właśnie tam siedziały teksty, które po zmianie assetów natychmiast zdradzały stary branding.

Przykładowy fragment:

```cshtml
<title>DataDrive</title>
...
<div id="preApplicationLoadingPanel" class="pre-loading-panel">
    <div class="pre-loading-image" role="img" aria-label="DataDrive"></div>
</div>
<component type="typeof(SplashScreen)" render-mode="Static" param-Caption='""' param-ImagePath='"images/SplashScreen.svg"' />
```

I teraz ważna rzecz: tu nie zmieniasz tylko jednego napisu.

Trzeba przejrzeć:

- `<title>`,
- `aria-label`,
- `param-Caption`,
- teksty fallbackowe, jeśli masz jakiś komunikat dla IE albo starej przeglądarki.

To są drobiazgi, ale właśnie one najczęściej zostają stare. I potem użytkownik widzi nowe logo, ale karta nadal ma starą nazwę.

## CSS robi połowę roboty

Drugi punkt zapalny to `site.css`.

U mnie wygląda to tak:

```css
.pre-loading-image {
    width: min(72vw, 760px);
    height: min(24vw, 220px);
    background: transparent url('../images/FullLogo.svg') center center / contain no-repeat;
}

.header-logo {
    -webkit-mask: url('../images/Logo.svg');
    mask: url('../images/Logo.svg');
    width: 210px;
    height: 24px;
}
```

To są dwa różne światy:

- preload bierze `FullLogo.svg`,
- header bierze `Logo.svg`.

Jeśli podmienisz tylko header, pierwsza plansza dalej pokaże stare logo i cały „profesjonalizm” kończy się po pierwszej sekundzie ładowania.

## Loader też potrafi zrobić wstyd

Samo wskazanie `SplashScreen.svg` to nie wszystko. Jeżeli nowy asset ma inne proporcje niż stary, to rozmiary loadera potrafią go zmasakrować.

Na przykład:

```css
#applicationLoadingPanel .loading {
    width: 360px;
    height: 360px;
}

#applicationLoadingPanel .loading-image {
    width: 180px;
    height: 180px;
    object-fit: contain;
}
```

Brzmi niewinnie, ale jeśli wrzucisz tam bardzo szerokie logo zamiast zwartego znaku, od razu zaczyna się przycinanie albo śmieszne puste marginesy.

To jest właśnie moment, w którym człowiek mówi „obrazek jest dobry”, a problem siedzi w CSS.

## Motywy też są częścią odbioru

Jeżeli po prawej masz wybór stylów, to warto to potraktować jako część brandingu, a nie osobny temat.

Nie pchałbym tego do kodu, jeśli można zostawić w konfiguracji.

Przykład:

```json
"ThemeSwitcher": {
  "DefaultItemName": "Office White",
  "ShowSizeModeSwitcher": true,
  "Groups": [
    {
      "IsFluent": true,
      "Caption": "DevExpress Fluent"
    },
    {
      "Caption": "DevExpress Classic"
    }
  ]
}
```

To jest dużo wygodniejsze niż późniejsze grzebanie w hostach i komponentach tylko po to, żeby uporządkować listę motywów.

## Jak ja bym to robił drugi raz

Nie od assetów. Najpierw zrobiłbym krótką listę:

1. co jest headerem,
2. co jest preloadem,
3. co jest splashem,
4. jakie teksty mają się pojawić,
5. czy motywy też wchodzą w zakres.

Dopiero potem podmiana plików.

Kolejność praktyczna:

1. wrzuć nowe SVG,
2. popraw `_Host.cshtml`,
3. popraw `site.css`,
4. sprawdź `appsettings.json`,
5. przebuduj aplikację,
6. obejrzyj trzy ekrany osobno: preload, splash, header.

To brzmi banalnie, ale właśnie pominięcie jednego z tych kroków robi później cały bałagan.

## Prompt dla agenta AI, który ma to zrobić bez marudzenia

Jeśli miałbym to zlecić Codexowi albo Claude, dałbym mu coś takiego:

```text
Zmień branding w aplikacji Blazor.

Zrób to end-to-end:
1. Podmień logo w headerze.
2. Podmień pełne logo przed spinnerem.
3. Podmień splash screen.
4. Zmień teksty brandingowe w _Host.cshtml.
5. Jeśli trzeba, uporządkuj ThemeSwitcher w appsettings.json.
6. Przebuduj aplikację i sprawdź trzy stany: preload, splash, header.

Sprawdź dokładnie:
- Pages/_Host.cshtml
- wwwroot/css/site.css
- wwwroot/images/
- appsettings.json

Na końcu wypisz zmienione pliki i opisz efekt.
```

Krótko, ale bez zostawiania agentowi pola do zgadywania.

## Błędy, które wracają jak bumerang

Najczęściej widzę to:

- ktoś podmienia tylko `SplashScreen.svg`,
- ktoś zostawia stare `title`,
- ktoś zmienia pliki, ale nie robi rebuilda,
- ktoś poprawia header, a preload zostaje z poprzedniej epoki.

I potem zaczyna się tłumaczenie, że „przecież logo już podmienione”.

Tak, tylko nie wszędzie.

Branding w takich aplikacjach nie jest wielką architekturą. To bardziej kwestia dyscypliny. Ale właśnie przez to łatwo go potraktować byle jak. A wtedy całość wygląda byle jak już od pierwszej sekundy.

## Update 2026-05-12: ten sam pattern w MainDemo

Ten sam zestaw zmian przeszedłem drugi raz, tym razem w [`MainDemoEFCoreCustomization`](https://github.com/kashiash/MainDemoEFCoreCustomization) (publiczny fork XAF Main Demo na EF Core). Robiłem to dosłownie z myślą o tym, czy ten artykuł trzyma się w praktyce, jak się go bierze do innego repo.

Punkt startu w MainDemo był uboższy niż w DataDrive: były tylko `Logo.svg` i `SplashScreen.svg`, pre-loadera nie było wcale, tytuł karty to `XAF Blazor Demo`, theme switcher na `DevExpress Fluent`.

Co się sprawdziło dokładnie tak, jak opisane wyżej:

- **Trzy assety, nie jeden.** Jeszcze raz okazało się, że dopóki nie mamy osobnego `FullLogo` (u mnie `fleet-management-software.svg`), pre-loader albo nie istnieje, albo użyje czegoś, co miało być headerem.
- **`<title>`, `og:title`, `param-Caption`, `aria-label` razem.** Zmieniłem tylko `<title>` i jakkolwiek logo się ładnie wyświetla, czytnik ekranu nadal czyta starą markę.
- **`body { margin: 0 }` przy `position: fixed; inset: 0`.** Łatwo pominąć — pre-loading-panel wyglądał poprawnie na pierwszy rzut oka, ale przy szerszym viewporcie widać 8 px ramki z Bootstrapa.
- **`z-index: 100002` nad `#blazor-error-ui` (`100001`).** Drobiazg, ale jeśli aplikacja umrze podczas startu, błąd nie powinien wskoczyć nad pre-loaderem.

Co dodało się jako konkretna pułapka tylko tego repo:

- **Build pada na MSB3026/MSB3027 jeśli aplikacja jest aktualnie uruchomiona.** Kompilator C# leci czysto, dopiero copy-step `MainDemo.Module.dll` do `MainDemo.Blazor.Server\bin\` próbuje 10 razy i pada. Wniosek: jeśli oceniasz branding w trakcie sesji, najpierw zatrzymaj proces, dopiero potem rebuild.
- **MainDemo ma własną warstwę modelu po polsku** (`Model.DesignedDiffs.Localization.pl.xafml`). Branding nie ruszał XAFML, ale gdyby ktoś chciał zmienić też nazwę aplikacji w nawigacji, trzeba pamiętać, że ten plik istnieje.
- **`MainDemoBlazorApplication.ApplicationName = "MainDemo"`** zostało celowo bez zmian — to identyfikator aplikacji w `ModelDifference`, nie napis na ekranie. Zmiana zerwałaby ciągłość modelu w istniejącej bazie.

Pełny zapis zmiany w MainDemo (z fragmentami przed/po, listą plików i tym, czego *nie* ruszałem i dlaczego) leży w repo w [`docs/branding-w-main-demo-blazor.md`](https://github.com/kashiash/MainDemoEFCoreCustomization/blob/main/docs/branding-w-main-demo-blazor.md). To samo wzięte z innej strony.

Wniosek operacyjny: lista kontrolna z tego artykułu — assety → `_Host.cshtml` → `site.css` → `appsettings.json` → rebuild → trzy ekrany do obejrzenia — przeszła drugi raz bez modyfikacji. Jak coś wraca dwa razy z tym samym sukcesem, to przestaje być przypadek i można już z tego zrobić checklistę.
