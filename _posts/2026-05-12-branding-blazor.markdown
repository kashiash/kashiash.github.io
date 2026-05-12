---
layout: post
title: "Branding w Blazorze: logo, splash screen i motywy"
---

Jeśli aplikacja Blazor ma wyglądać spójnie, to samo podmienienie logo w headerze zwykle nie wystarcza. W praktyce branding siedzi w kilku miejscach naraz: w preloaderze przed startem aplikacji, w splash screenie, w nagłówku i czasem jeszcze w konfiguracji motywów.

Dopóki nie zbierzesz tego w jednym miejscu, każda kolejna zmiana kończy się poprawianiem "jeszcze jednego obrazka", którego nikt wcześniej nie zauważył.

## 1. Najpierw ustal, które elementy naprawdę składają się na branding

W typowej aplikacji Blazor masz co najmniej trzy warstwy:

1. pełne logo przed spinnerem,
2. splash screen / loader w środku ekranu,
3. logo w headerze po załadowaniu aplikacji.

Jeśli masz też przełącznik motywów po prawej stronie, to on również wpływa na odbiór brandingu, nawet jeśli nie jest "logo".

## 2. Zbierz assety do jednego katalogu

Najwygodniej trzymać branding w jednym miejscu, np.:

```text
wwwroot/images/
```

W praktyce dobrze rozdzielić role plików:

- `Logo.svg` - header,
- `FullLogo.svg` - ekran przed spinnerem,
- `SplashScreen.svg` - środek loadera.

To upraszcza kolejne zmiany. Zamiast zgadywać, który SVG za co odpowiada, masz prosty podział odpowiedzialności.

## 3. Zmień teksty i markup w `_Host.cshtml`

To jest zwykle pierwsze miejsce, które trzeba sprawdzić.

Przykład:

```cshtml
<title>DataDrive</title>
...
<div id="preApplicationLoadingPanel" class="pre-loading-panel">
    <div class="pre-loading-image" role="img" aria-label="DataDrive"></div>
</div>
<component type="typeof(SplashScreen)" render-mode="Static" param-Caption='""' param-ImagePath='"images/SplashScreen.svg"' />
```

Tutaj zwykle zmieniasz:

- nazwę zakładki,
- `aria-label`,
- obrazek splasha,
- caption splasha,
- ewentualne komunikaty fallbackowe.

Jeśli branding ma być spójny, to te teksty nie mogą zostać stare po podmianie SVG.

## 4. Podłącz pełne logo i logo headera w CSS

Drugi punkt obowiązkowy to `site.css`.

Przykład:

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

To są dwa różne miejsca i dwa różne efekty wizualne. Jeśli zmienisz tylko header, preload nadal może pokazywać stare logo.

## 5. Dostosuj sam splash screen, nie tylko obrazek

Jeżeli loader wygląda źle po podmianie grafiki, problem często nie jest w samym pliku, tylko w CSS.

Przykładowe miejsce:

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

Jeżeli nowe logo ma inne proporcje niż stare, to właśnie tutaj robi się korekty rozmiaru i marginesów.

## 6. Jeśli branding obejmuje motywy, trzymaj to w konfiguracji

Jeżeli po prawej stronie masz przełącznik stylów, to najlepiej nie zaszywać go w kodzie, tylko w konfiguracji.

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

To pozwala zmieniać listę motywów bez ruszania samego hosta aplikacji.

## 7. Najbezpieczniejszy workflow zmiany brandingu

Jeśli chcesz zrobić to porządnie, a nie "na szybko", kolejność powinna być taka:

1. przygotuj nowe SVG,
2. ustal, który plik odpowiada za header, preload i splash,
3. podmień assety,
4. popraw `_Host.cshtml`,
5. popraw `site.css`,
6. sprawdź konfigurację motywów,
7. przebuduj aplikację,
8. przejrzyj preload, splash i header osobno.

Właśnie rozdzielenie tych trzech ekranów oszczędza później dużo nerwów.

## 8. Prompt dla agenta AI

Jeżeli chcesz zlecić taką zmianę agentowi AI, to minimalny prompt może wyglądać tak:

```text
Zmień branding w aplikacji Blazor.

Zakres:
1. Podmień logo w headerze.
2. Podmień pełne logo przed spinnerem.
3. Podmień splash screen.
4. Zmień teksty brandingowe w _Host.cshtml.
5. Jeśli trzeba, zaktualizuj ThemeSwitcher w appsettings.json.
6. Przebuduj aplikację i podaj listę zmienionych plików.

Sprawdź dokładnie:
- Pages/_Host.cshtml
- wwwroot/css/site.css
- wwwroot/images/
- appsettings.json
```

Taki prompt jest wystarczająco krótki, ale nadal mówi agentowi, gdzie szukać i czego nie pominąć.

## 9. Najczęstsze błędy

Najczęściej powtarzają się te same problemy:

1. podmiana tylko jednego SVG,
2. zostawienie starego `<title>` albo starego `aria-label`,
3. brak przebudowy po zmianie static assets,
4. poprawienie headera bez poprawienia preloadu,
5. zmiana obrazka bez dopasowania CSS.

Jeśli branding ma wyglądać profesjonalnie, to trzeba potraktować go jak małą zmianę techniczną, a nie jak wrzutkę jednego pliku graficznego.
