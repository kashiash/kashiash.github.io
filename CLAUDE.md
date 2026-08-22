# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Zasady bezwzględne

**Przed każdą edycją plików w tym repozytorium:**
```
git pull origin main
```
Bez tego możesz nadpisać zmiany wprowadzone przez inną sesję.

## Uruchamianie lokalnie

```bash
bundle exec jekyll serve        # serwer dev na http://localhost:4000
bundle exec jekyll build        # jednorazowy build do _site/
```

Strona jest hostowana na GitHub Pages — push do `main` wdraża automatycznie.

## Architektura

Hybryda: `index.html` i `xaf.html` to ręcznie utrzymywane pliki statyczne (poza Jekyll). Posty w `_posts/` są przetwarzane przez Jekyll i generowane do `_site/`.

- `index.html` — strona główna, **dwukolumnowy układ** (sticky intro 280px | lista wpisów). CSS inline w `<head>`. Nie zamieniaj na stary layout z hero/manifestem.
- `xaf.html` — podstrona XAF, statyczny HTML poza Jekyll
- `_posts/` — posty Jekyll (.markdown), `permalink: /:year/:month/:day/:title.html`
- `assets/images/` — miniatury do wpisów; dwa warianty na wpis: `*-list.png` (miniatura w `index.html`) i wersja bez sufiksu (obrazek nagłówkowy wewnątrz posta)
- `_includes/head.html` — dodatkowe tagi `<head>` wstrzykiwane przez motyw minima
- `update_posts.py` — skrypt jednorazowy do wstawiania miniatur do front matter postów; **nie modyfikuje `index.html`**

## Dodawanie nowego wpisu

### 1. Plik posta `_posts/`

Front matter:
```markdown
---
layout: post
title: "Tytuł"
date: RRRR-MM-DD
categories: kategoria1 kategoria2
---

![Alt text](/assets/images/nazwa-wpisu.png)

Treść...
```

### 2. Wpis w `index.html`

Dodaj jako **pierwszy** `<article class="post-item">` w `<main class="posts-col">`:

```html
<article class="post-item">
  <div class="post-date">RRRR-MM-DD</div>
  <div class="post-body">
    <span class="post-kicker">Kategoria</span>
    <h3 class="post-title">Tytuł</h3>
    <p class="post-desc">Jedno zdanie opisu.</p>
    <a class="post-link" href="/RRRR/MM/DD/slug-wpisu.html">Czytaj wpis →</a>
  </div>
  <img src="/assets/images/nazwa-wpisu-list.png" alt="Opis obrazka" class="post-thumb" loading="lazy">
</article>
```

Miniatura (`post-thumb`) to osobny plik `*-list.png` — różny od obrazka nagłówkowego wewnątrz posta.

## Zasady tworzenia grafik (Styl "Doodle 4 Kredki")

Aby utrzymać spójną, minimalistyczną tożsamość wizualną bloga podczas generowania nowych obrazków w AI (np. Midjourney, DALL-E, Imagen), trzymaj się następujących zasad w promptach:

### 1. Baza Stylistyczna (dodaj to do każdego promptu)
> *A hand-drawn minimalist ink doodle on slightly yellowed paper. High contrast, expressive black ink lines, very sketchy and simple. The drawing is mostly black ink, with sparse, messy color accents (scribbled red, blue, yellow, and green crayon). Humorous, minimalist style.*

**Kluczowe detale:** Unikaj cieniowania 3D i pełnego wypełnienia kolorem. Kolor ma przypominać niechlujne maźnięcia czterema podstawowymi kredkami, a całość ma wyglądać jak szybki szkic w notatniku.

### 2. Dwa typy obrazków
**A. Główny obrazek wewnątrz posta (`assets/images/nazwa-wpisu.png`)**
*   **Zawiera postać programisty.** W prompcie użyj stałego opisu: *A programmer character (stocky, curly hair, glasses, wearing a hoodie).*
*   Programista najczęściej wchodzi w komiczną interakcję z fizyczną reprezentacją problemu technicznego.

**B. Miniatura wpisu na listę (`assets/images/nazwa-wpisu-list.png`)**
*   **BEZ LUDZI.** W prompcie dodaj absolutny zakaz: *No humans or characters.*
*   Używaj pomysłowych metafor obiektowych: *Zamiast logo "PostgreSQL" zrób wielką szufladę na akta przedzieloną drutem kolczastym (multi-tenant)* albo *zamiast "Date Editor" zrób zablokowany drewnianym kołkiem kołowrotek*. Szukaj analogii w fizycznym świecie.

## Zasady pisania treści

**Wszystko, co ląduje na tym blogu, przechodzi przez `prosta-polszczyzna` i `humanizer-pl`** — post Jekylla tak samo jak statyczna strona `*.html`. Pipeline z `pisz-wpis` nie kończy się na `_posts/`; strony pisane od ręki wychodzą bełkotliwe.

Czego unikać, bo już się zdarzyło:

- **Slogan zamiast informacji.** „Nic nie dzieje się samo" nie mówi nic. Powiedz, co konkretnie się dzieje i kto to robi.
- **Antropomorfizacja.** System niczego nie „zamierza" ani nie „chce". System pokazuje, czeka, zapisuje.
- **Trzy zdania o jednym.** Jeśli drugie i trzecie zdanie parafrazują pierwsze, zostaje pierwsze.
- **Retoryczne rozbiegi.** „Tu zaczyna się część, dla której warto było to zbudować" — wytnij, przejdź do rzeczy.
- **Ramki wokół tez.** „Wniosek szerszy niż ten POC:" — sama teza wystarczy.
- **Morały na koniec sekcji.** „Rzecz, którą zabieram dalej…" — jeśli teza jest dobra, obroni się bez oprawy.
- **Podpisy powtarzające tabelę.** Podpis pod zrzutem ma dodawać, nie streszczać to, co jest obok.

**Twierdzenie w materiale demo musi mieć pokrycie w zrzucie.** Jeśli tekst mówi „system pokazuje listę i czeka", to na stronie ma być zrzut tej listy. Inaczej to obietnica bez dowodu.

Nazywaj odbiorcę **użytkownikiem**, nie „człowiekiem" — „człowiek" w opozycji do maszyny brzmi pretensjonalnie.

## Czego nie ruszać

- Nie zmieniaj układu strony głównej bez wyraźnej prośby.
- Nie dodawaj sekcji hero, manifest, kafelki kategorii — zostały celowo usunięte.
- Nie commituj bez `git pull` na początku.

## Email i kontakt

Jedyny adres email: **kashiash@gmail.com** — wszędzie spójny.
