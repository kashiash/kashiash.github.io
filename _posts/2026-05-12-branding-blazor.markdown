---
layout: post
title: "Branding w Blazorze: logo, splash screen i motywy"
---

Najłatwiej zepsuć branding w Blazorze w bardzo elegancki sposób. Niby wszystko działa, aplikacja się uruchamia, logo „jest”, a i tak człowiek od razu widzi, że coś tu się rozjechało. Jedno logo na starcie, drugie po zalogowaniu, trzecie w loaderze. Do tego po prawej jakieś motywy z innej bajki.

Przerabiałem to ostatnio na żywym organizmie i właśnie dlatego to zapisuję. Nie jako wielką teorię, tylko jako rzecz, do której da się wrócić za miesiąc bez przeklinania.

## Gdzie ten branding naprawdę siedzi

Na pierwszy rzut oka człowiek myśli: „podmienię SVG i po sprawie”. Nie. W praktyce zwykle są co najmniej trzy miejsca:

- pełne logo przed spinnerem,
- obrazek w splash screenie,
- logo w headerze po wejściu do aplikacji.

A czasem jeszcze dochodzi czwarty element, czyli układ motywów po prawej stronie. To nie jest logo, jasne. Ale jeśli masz nowoczesny branding, a Theme Switcher wygląda jak relikt po pięciu refaktoryzacjach, to cały efekt siada.

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
