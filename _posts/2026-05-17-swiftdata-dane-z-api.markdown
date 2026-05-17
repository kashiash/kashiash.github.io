---
layout: post
title: "SwiftData: zapis danych z API — wzorzec DTO, upsert i @ModelActor"
date: 2026-05-17
categories: swift ios swiftdata
---

![Dane z serwera lądują w lokalnej bazie SwiftData](/assets/images/swiftdata-api.png)

Budujesz listę z danymi z API. Chcesz, żeby działała offline. Pierwsze podejście: `@Model` z `Codable`, `modelContext.insert` w `.task`. Działa — do momentu, gdy dochodzi paginacja i insert pięćdziesięciu rekordów freezuje UI. Dochodzi refresh — masz duplikaty, bo SwiftData nie ma wbudowanego upsert. Dochodzi wyszukiwanie — chcesz osobnej kolekcji w tej samej bazie, bez mieszania wyników.

Wszystko rozwiązują dwie struktury i jeden aktor: DTO do dekodowania, `@Model` do persystencji i `@ModelActor` do upsert poza głównym wątkiem. Bez zewnętrznych bibliotek. Działa tak samo przy 20 rekordach i przy 500.

## Dwie struktury zamiast jednej

Nie dekoduję JSON bezpośrednio do `@Model`. Trzymam dwie osobne struktury.

**DTO** — struct, `Decodable`, `Sendable`. Żyje przez jeden request, potem znika.

**@Model** — klasa SwiftData. Trwa w bazie między sesjami, ma własne pola cache (`sortIndex`, `updatedAt`, `localThumbnailPath`).

```swift
struct ProductDTO: Identifiable, Decodable, Sendable {
    let id: Int
    let title: String
    let description: String
    let category: String
    let price: Double
    let thumbnail: String
}

@Model
final class CachedProduct {
    @Attribute(.unique) var remoteID: Int
    var title: String
    var category: String
    var price: Double
    var thumbnail: String
    var localThumbnailPath: String?
    var sortIndex: Int
    var updatedAt: Date

    init(from dto: ProductDTO, sortIndex: Int) {
        self.remoteID = dto.id
        self.title = dto.title
        self.category = dto.category
        self.price = dto.price
        self.thumbnail = dto.thumbnail
        self.sortIndex = sortIndex
        self.updatedAt = Date()
    }
}
```

Decyzje warte zapamiętania:

- **`@Attribute(.unique)` na `remoteID`** zapobiega duplikatom przy ponownym fetchu. SwiftData rzuci błąd przy konflikcie zamiast cicho wstawić duplikat.
- **`sortIndex` zamiast sortowania po `remoteID`**. Kolejność stron z API nie zawsze pokrywa się z rosnącym ID. `sortIndex = pageOffset + indexInPage` zachowuje oryginalną kolejność serwera.
- **`localThumbnailPath` jako `String?`**, nie `Data?`**. Obrazki zapisuję na dysk osobno, tu trzymam tylko ścieżkę. `@Attribute(.externalStorage)` jest alternatywą — opisałem ją w [poprzednim wpisie](/2026/05/16/swiftdata-store-large-files-pl.html).

## @ModelActor — upsert poza głównym wątkiem

`modelContext` z `@MainActor` blokuje UI przy setkach insertów. Wydzielam osobny aktor z własnym kontekstem.

```swift
@ModelActor
actor ProductCacheStore {
    private let queryKey: String

    init(modelContainer: ModelContainer, queryKey: String = "products.default") {
        let context = ModelContext(modelContainer)
        self.modelExecutor = DefaultSerialModelExecutor(modelContext: context)
        self.modelContainer = modelContainer
        self.queryKey = queryKey
    }

    func upsertProducts(_ dtos: [ProductDTO], startingAt offset: Int) throws {
        let ids = dtos.map(\.id)

        // Jeden batch fetch zamiast N osobnych zapytań
        let descriptor = FetchDescriptor<CachedProduct>(
            predicate: #Predicate { ids.contains($0.remoteID) }
        )
        let existing = try modelContext.fetch(descriptor)
        let byID = Dictionary(uniqueKeysWithValues: existing.map { ($0.remoteID, $0) })

        let now = Date()
        for (index, dto) in dtos.enumerated() {
            if let cached = byID[dto.id] {
                cached.title = dto.title
                cached.price = dto.price
                cached.sortIndex = offset + index
                cached.updatedAt = now
            } else {
                modelContext.insert(CachedProduct(from: dto, sortIndex: offset + index))
            }
        }
        try modelContext.save()
    }

    func fetchProducts(limit: Int, offset: Int) throws -> [CachedProduct] {
        var descriptor = FetchDescriptor<CachedProduct>(
            sortBy: [SortDescriptor(\.sortIndex)]
        )
        descriptor.fetchLimit = limit
        descriptor.fetchOffset = offset
        return try modelContext.fetch(descriptor)
    }
}
```

Decyzje warte zapamiętania:

- **Jeden `FetchDescriptor` z `ids.contains`** zamiast N osobnych zapytań po `remoteID`. Dla 50 rekordów to różnica między 50 a 1 tripen do SQLite.
- **`DefaultSerialModelExecutor`** dostaje `ModelContext` stworzony w inicjalizatorze aktora. Nie używam `modelContext` przekazanego z zewnątrz — `@ModelActor` sam pilnuje wątku.
- **`queryKey`** pozwala trzymać kilka niezależnych kolekcji w jednym kontenerze. Przy wyszukiwaniu lub filtrowaniu tworzę nowy `ProductCacheStore` z innym kluczem, stara kolekcja nie koliduje.

## Podpięcie w widoku

```swift
struct ProductsListView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var store: ProductCacheStore?

    var body: some View {
        Group {
            if let store {
                ProductsListContent(store: store)
            } else {
                ProgressView()
            }
        }
        .task {
            guard store == nil else { return }
            store = ProductCacheStore(modelContainer: modelContext.container)
        }
    }
}
```

`ProductCacheStore` nie jest `@StateObject` ani `@Observable` — to aktor. Tworzę go raz w `.task` i przekazuję dalej. `modelContext.container` daje dostęp do `ModelContainer` bez wstrzykiwania go osobno.

## Pułapki

**`@Attribute(.unique)` nie robi upsert za ciebie.** Jeśli wstawisz drugi rekord z tym samym `remoteID`, SwiftData rzuci błąd w `save()`. Musisz sam sprawdzić, czy rekord istnieje — stąd batch fetch w `upsertProducts`.

**`modelContext.save()` w aktorze jest synchroniczne.** `@ModelActor` sprawia, że cały aktor działa na jednym wątku — ale nie blokuje `@MainActor`. To właśnie o to chodzi.

**`#Predicate` nie akceptuje zmiennych lokalnych domknięcia.** `ids.contains($0.remoteID)` działa, bo `ids` to `[Int]` — typ obsługiwany przez SwiftData predykaty. Nie możesz tam przekazać własnego struct lub klasy.

## Co dalej

Ten wzorzec to podstawa dla paginacji. Przy infinite scroll `upsertProducts` jest wywoływany ze stronicowanym `offset`, a `queryKey` rozdziela kolekcje przy różnych zapytaniach. Opisuję to w następnym wpisie o infinite scroll z warm-up cache w tle.
