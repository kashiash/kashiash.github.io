---
layout: post
title: "Seria: Dostosowanie demówki XAF Blazor do własnych potrzeb"
series: "Dostosowanie demówki XAF Blazor do własnych potrzeb"
series_part: 0
---

DevExpress udostępnia publicznie sample `MainDemo.NET.EFCore` — kompletną aplikację XAF Blazor + EF Core + WinForms + Web API. Świetny punkt startu, ale **to jest demówka**. Wygląda jak demówka, ma brand DevExpressa, używa anglojęzycznych nazw pól, ma domyślne zachowania kontrolek, które w prawdziwym projekcie są wrogie operatorom.

Wziąłem to repo i przerobiłem na coś, co realnie wygląda i działa jak własna aplikacja. Konkretne zmiany, konkretne pliki, konkretne pułapki. Wszystko publiczne w [`MainDemoEFCoreCustomization`](https://github.com/kashiash/MainDemoEFCoreCustomization) — można obejrzeć diff albo wziąć i powtórzyć u siebie.

Ta strona jest **indeksem serii**. Każdy kolejny etap to osobny artykuł.

## Etapy

### 1. [Obsługa języków: polski, angielski, niemiecki]({% post_url 2026-05-12-obsluga-jezykow-blazor %})

Wielojęzyczność z fallbackiem na `en-US` (świadomie, nie z lenistwa — z powodu raportów CSV). `RequestLocalizationOptions`, `Model.DesignedDiffs.Localization.pl.xafml`, lokalizacja DevExpress reportów przez JSON-y w `wwwroot/js/localization/`. Plus konkretny powód, dla którego `pl-PL` jako domyślny się tu nie sprawdza.

### 2. [Branding: logo, splash screen i motywy]({% post_url 2026-05-12-branding-blazor %})

Trzy SVG (header, pre-loader, splash), nie jeden. `_Host.cshtml` poprawiony razem z `aria-label` i `og:title`. `site.css` z customowym `#applicationLoadingPanel .loading-floated-circle` (conic-gradient łuk). Theme switcher na `Office White`. Plus update opisujący powtórne przejście tego samego patterna w innym repo — pokazuje, że to się trzyma jako checklista.

### 3. [Custom DateEditor z parametrem modelowym do blokady kółka myszy]({% post_url 2026-05-12-xaf-blazor-date-editor-mouse-wheel %})

DevExpress `DxDateEdit` ma defaultowo zachowanie, w którym scroll kółka myszy zmienia wartość daty. Operator przewija formularz w dół, mija datę, w bazie ląduje krzywa data pacjenta. Custom property editor XAF (`DateEditor` + `DateEditorNullable`), z opt-outem w Model Editor XAF-a przez własny `IModelMemberViewItemMouseWheel`. Plus JS w fazie `capture` (musiało chodzić DevExpressowi przed pazurami), marker CSS i kilka pułapek, których nie widać z pierwszego rzutu oka.

## Co łączy te trzy zmiany

Każda z nich:

- jest **opt-in** (`isDefaultEditor: false`, `[EditorAlias(...)]`, wybór języka per użytkownik) — nie burzymy demówki dla osób, które chcą zostać przy oryginale,
- siedzi w **konfiguracji aplikacji + jednym custom-pliku**, nie w masowych przeróbkach modelu,
- ma **dokumentację w samym repo** (`docs/*.md`), nie tylko na blogu — bo blog jest publiczny, ale repo zostaje przy projekcie.

## Co planuję jeszcze dodać do serii

To są kolejne tematy, które realnie wracają w projektach XAF Blazor i które warto przerobić publicznie:

- **Sekcja login/logon**: logon parameters, last logon user, custom validation komunikatów — bo standardowy logon ma kilka miejsc, w których "to jest demo" rzuca się w oczy.
- **Customizacja Nawigacji** — ikony, grupowanie, ukrywanie zbędnych pozycji z modułów referencyjnych XAF-a.
- **Customizacja list view** — defaultowe sortowanie, frozen columns, layout per użytkownik vs per rola.
- **Audit Trail w UI** — pokazanie historii zmian rekordu w sposób, który nie wymaga otwierania osobnego widoku.
- **Wymiana standardowych powiadomień XAF** na coś, co nie wygląda jak alert sprzed 15 lat.

Każdy nowy artykuł dorzucę do tego indeksu i do strony głównej.
