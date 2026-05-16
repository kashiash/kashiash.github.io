import os

mapping = {
    "2022-10-09-Daty w Swift.markdown": ("Daty w Swift: Walka z budzikiem", "swift-dates.png"),
    "2022-10-10-Pobierz lokalizacje na podstawie adresy.markdown": ("Lokalizacja po adresie: Detektyw i satelita", "location-address.png"),
    "2022-11-01 Ciekawe strony dotyczące Swiift i programowania na IOS.markdown": ("Ciekawe strony iOS: Skrzynia skarbów", "interesting-links.png"),
    "2026-04-05-mat-deprecated-devexpress-localization-tool.markdown": ("Koniec MAT: Nagrobek i robot", "end-of-mat.png"),
    "2026-05-12-branding-blazor.markdown": ("Branding w Blazorze: Malowanie łodzi", "branding-blazor.png"),
    "2026-05-12-obsluga-jezykow-blazor.markdown": ("Języki w Blazorze: Wieża Babel", "languages-blazor.png"),
    "2026-05-12-seria-dostosowanie-demowki-xaf-blazor.markdown": ("Seria XAF Blazor: Plan budowy", "xaf-series-index.png"),
    "2026-05-12-xaf-blazor-date-editor-mouse-wheel.markdown": ("DateEditor: Blokada scrolla", "date-editor-lock.png"),
    "2026-05-12-xaf-ef-core-postgresql-multitenant.markdown": ("PostgreSQL Multi-tenant: Słonie w kamienicy", "postgresql-multitenant.png"),
    "2026-05-12-xaf-ef-core-postgresql-testy.markdown": ("Testowanie PostgreSQL: Programista w kitlu", "postgresql-testing.png"),
    "2026-05-15-domkniecie-polskiej-lokalizacji-xaf.markdown": ("Polska lokalizacja: Gumka i ołówek", "polish-localization.png"),
    "2026-05-15-dynamiczne-reguly-wygladu-xaf-z-bazy.markdown": ("Dynamiczny wygląd: Magiczna różdżka", "dynamic-appearance.png"),
    "2026-05-15-obsluga-skanow-i-podgladu-pdf-w-xaf-blazor.markdown": ("PDF i skany: Góra papierów", "pdf-preview.png"),
}

posts_dir = "_posts"

for filename, (alt, img) in mapping.items():
    filepath = os.path.join(posts_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if f"![{alt}]" in content:
        print(f"Image already exists in {filename}")
        continue
        
    # Find the end of front matter (second ---)
    parts = content.split('---', 2)
    if len(parts) >= 3:
        new_content = f"---{parts[1]}---\n\n![{alt}](/assets/images/{img})\n\n{parts[2].lstrip()}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filename}")
    else:
        print(f"Could not find front matter in {filename}")
