# kashiash.github.io — instrukcja dla AI

## Zasady bezwzględne

**Przed każdą edycją plików w tym repozytorium:**
```
git pull origin main
```
Bez tego możesz nadpisać zmiany wprowadzone przez inną sesję.

## Struktura strony

- `index.html` — strona główna, **dwukolumnowy układ** (lewa: sticky intro 280px, prawa: lista wpisów). Nie zamieniaj na stary layout z hero/manifestem.
- `xaf.html` — podstrona XAF, statyczny HTML
- `_posts/` — posty Jekyll (.markdown)
- `assets/images/` — obrazki do postów
- `update_posts.py` — skrypt do aktualizacji front matter postów; **nie modyfikuje index.html**

## Dodawanie nowego wpisu do index.html

Nowy post dodaj jako `<article class="post-item">` na początku listy w `<main class="posts-col">`, zachowując format:

```html
<article class="post-item">
  <div class="post-date">RRRR-MM-DD</div>
  <div class="post-body">
    <span class="post-kicker">Kategoria</span>
    <h3 class="post-title">Tytuł</h3>
    <p class="post-desc">Jedno zdanie opisu.</p>
    <a class="post-link" href="/link/do/wpisu.html">Czytaj wpis →</a>
  </div>
</article>
```

## Email i kontakt

Jedyny adres email: **kashiash@gmail.com** — wszędzie spójny.

## Czego nie ruszać

- Nie zmieniaj układu strony głównej bez wyraźnej prośby.
- Nie dodawaj sekcji hero, manifest, kafelki kategorii — zostały celowo usunięte.
- Nie commituj bez `git pull` na początku.
