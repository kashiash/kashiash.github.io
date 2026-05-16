---
layout: post
title: "Branding w Blazorze: logo, splash screen i motywy"
series: "XAF Blazor: od aplikacji referencyjnej do gotowego produktu"
series_part: 2
---

![Branding w Blazorze: Malowanie łodzi](/assets/images/branding-blazor.png)

> **Część 2 serii: [XAF Blazor: od aplikacji referencyjnej do gotowego produktu]({% post_url 2026-05-12-seria-dostosowanie-demowki-xaf-blazor %})**
>
> 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})
> 2. **Branding: logo, splash screen i motywy** — ten wpis
> 3. [Globalny DateEditor w XAF Blazor: blokada scrolla, polskie maski i czas tylko tam, gdzie trzeba]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

Ten wpis pokazuje dokładnie, co zmieniłem w `MainDemo.Blazor.Server`, żeby podmienić branding na DataDrive.

## Zakres zmiany

Zmiana objęła:

1. assety SVG w `wwwroot/images`,
2. host `_Host.cshtml`,
3. style w `site.css`,
4. domyślny motyw w `appsettings.json`.

## Pliki graficzne

Do `CS/MainDemo.Blazor.Server/wwwroot/images/` trafiły:

```text
Logo.svg
SplashScreen.svg
fleet-management-software.svg
```

## `_Host.cshtml`

To jest dokładna zawartość po zmianie:

```cshtml
@page "/"
@namespace MainDemo.Blazor.Server
@addTagHelper *, Microsoft.AspNetCore.Mvc.TagHelpers
@using DevExpress.ExpressApp.Blazor.Components

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta property="og:title" content="DataDrive" />
    <title>DataDrive</title>
    <base href="~/" />
    <component type="typeof(BootstrapThemeLink)" render-mode="Static" />
</head>
<body>
    <div id="preApplicationLoadingPanel" class="pre-loading-panel">
        <div class="pre-loading-image" role="img" aria-label="Fleet Management Software"></div>
    </div>
    <component type="typeof(SplashScreen)" render-mode="Static" param-Caption='"Fleet Management Software"' param-ImagePath='"images/SplashScreen.svg"' />

    <link href="_content/DevExpress.ExpressApp.Blazor/styles.css" asp-append-version="true" rel="stylesheet" />
    <link href="css/site.css" rel="stylesheet" />

    <app class="d-none">
        <component type="typeof(App)" render-mode="Server" />
    </app>

    <component type="typeof(AlertsHandler)" render-mode="Server" />

    <div id="blazor-error-ui" data-nosnippet>
        <component type="typeof(BlazorError)" render-mode="Static" />
    </div>

    <script>
        window.setTimeout(function() {
            var preLoadingPanel = document.getElementById('preApplicationLoadingPanel');
            if (!preLoadingPanel) {
                return;
            }

            preLoadingPanel.classList.add('pre-loading-hide');
            window.setTimeout(function() {
                preLoadingPanel.remove();
            }, 250);
        }, 1400);
    </script>
    <script src="_framework/blazor.server.js"></script>
    <script src="js/file-download.js"></script>
    <script src="js/scripts.js"></script>
</body>
</html>
```

Najważniejsze zmiany:

1. `<title>` i `og:title` zmieniły się na `DataDrive`,
2. doszedł `preApplicationLoadingPanel`,
3. `SplashScreen` dostał `param-Caption='"Fleet Management Software"'`,
4. doszedł skrypt, który wygasza i usuwa preloader.

## `site.css`

To jest dokładny blok stylów, który robi branding:

```css
html, body {
    height: 100%;
}

body {
    margin: 0;
}

app {
    display: block;
    height: 100%;
}

.pre-loading-panel {
    position: fixed;
    inset: 0;
    z-index: 100002;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--dxds-color-surface-neutral-default-rest, var(--bs-body-bg, #fff));
    opacity: 1;
    transition: opacity 0.25s ease;
}

.pre-loading-hide {
    opacity: 0;
    pointer-events: none;
}

.pre-loading-image {
    width: min(72vw, 760px);
    height: min(24vw, 220px);
    background: transparent url('../images/fleet-management-software.svg') center center / contain no-repeat;
}

.header-logo {
    flex-shrink: 0;
    background-color: currentColor;
    -webkit-mask: url('../images/Logo.svg');
    mask: url('../images/Logo.svg');
    -webkit-mask-position: center;
    mask-position: center;
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    width: 210px;
    height: 24px;
}

#applicationLoadingPanel .loading {
    width: 360px;
    height: 360px;
}

#applicationLoadingPanel .loading-image-wrapper {
    width: 220px;
    height: 220px;
    min-width: 220px;
    min-height: 220px;
    background-color: transparent !important;
    border-radius: 50%;
}

#applicationLoadingPanel .loading-image {
    width: 180px;
    height: 180px;
    object-fit: contain;
}

#applicationLoadingPanel .loading-border {
    width: 220px !important;
    height: 220px !important;
    min-width: 220px !important;
    min-height: 220px !important;
    border-width: 8px !important;
    border-radius: 50% !important;
    box-sizing: border-box;
}

#applicationLoadingPanel .loading-floated-circle {
    width: 220px !important;
    height: 220px !important;
    min-width: 220px !important;
    min-height: 220px !important;
    border: none !important;
    border-radius: 50% !important;
    box-sizing: border-box;
    background: conic-gradient(
        from 0deg,
        transparent 0deg 300deg,
        var(--dxds-color-border-primary-default-rest, var(--bs-primary)) 300deg 360deg
    ) !important;
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 8px)) !important;
    mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 8px)) !important;
}

#applicationLoadingPanel .loading-caption {
    display: none !important;
}
```

## `appsettings.json`

Branding zahaczył też o domyślny motyw:

```json
"ThemeSwitcher": {
  "DefaultItemName": "Office White",
  "ShowSizeModeSwitcher": true
}
```

Najważniejsza zmiana:

```json
"DefaultItemName": "Office White"
```

## Co sprawdzić w przeglądarce

1. karta ma tytuł `DataDrive`,
2. na starcie widać `fleet-management-software.svg`,
3. splash używa `SplashScreen.svg`,
4. w nagłówku jest `Logo.svg`,
5. domyślny motyw to `Office White`.

## Zmienione pliki

```text
CS/MainDemo.Blazor.Server/wwwroot/images/Logo.svg
CS/MainDemo.Blazor.Server/wwwroot/images/SplashScreen.svg
CS/MainDemo.Blazor.Server/wwwroot/images/fleet-management-software.svg
CS/MainDemo.Blazor.Server/Pages/_Host.cshtml
CS/MainDemo.Blazor.Server/wwwroot/css/site.css
CS/MainDemo.Blazor.Server/appsettings.json
```
