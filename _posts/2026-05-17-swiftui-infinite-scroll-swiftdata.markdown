---
layout: post
title: "SwiftUI: nieskończona lista z cache offline"
date: 2026-05-17
categories: swift ios swiftui swiftdata
---

![Lista produktów scrolluje się bez końca, wskaźnik synchronizacji w tle](/assets/images/infinite-scroll-cache.png)

Budujesz listę z API. Każda strona to 20 elementów. Użytkownik scrolluje — czas na kolejną.

Pierwsze podejście: `onAppear` na ostatnim elemencie. Gdy element pojawi się na ekranie, startujesz fetch. Problem: `onAppear` działa tylko wtedy, gdy SwiftUI wyrenderuje ten element. Gdy scrollujesz szybko, SwiftUI może go nie wyrenderować ponownie — task się nie odpali. Albo odpali, ale system anuluje go w połowie, bo element zniknie z ekranu zanim dane wrócą.

Dochodzi `AsyncImage`. SwiftUI nie zna wymiarów obrazka, dopóki go nie pobierze. Rezerwuje minimalną przestrzeń, a gdy obrazek wróci z sieci — komórka rośnie, lista skacze.

Dochodzi brak sieci. Nie ma danych z API — pokazujesz pusty ekran, choć poprzednia sesja miała dane.

Trzy problemy, trzy rozwiązania.

`onScrollGeometryChange` (iOS 18+) śledzi offset całego scroll view — nie poszczególnych komórek. Odpala się raz, gdy offset zbliży się do końca zawartości. Nie zależy od tego, które komórki SwiftUI aktualnie renderuje.

Enum `LoadingState` zastępuje osobne flagi `Bool`. Nie możesz mieć jednocześnie `loading = true` i `refreshing = true` — enum gwarantuje jeden aktywny stan w danej chwili.

SwiftData jako cache przechowuje dane między sesjami. Przy starcie pokazujesz to, co masz w bazie — zanim sieć odpowie. Przy braku sieci lista nadal działa.

DTO → `@Model` i `@ModelActor` opisałem w [poprzednim wpisie](/2026/05/17/swiftdata-dane-z-api.html).

---

## Kiedy ładować więcej — NearBottomTrigger

`onScrollGeometryChange` (iOS 18+) śledzi geometrię scroll view — nie poszczególne komórki. Wyzwala akcję raz, gdy offset zbliży się do końca zawartości.

```swift
struct NearBottomTrigger: ViewModifier {
    let triggerDistance: CGFloat
    let action: () -> Void

    func body(content: Content) -> some View {
        content.onScrollGeometryChange(for: Bool.self) { geometry in
            guard geometry.contentSize.height > 0 else { return false }
            let maxOffset = geometry.contentSize.height - geometry.containerSize.height
            return geometry.contentOffset.y > maxOffset - triggerDistance
        } action: { oldValue, newValue in
            if newValue && !oldValue {
                action()
            }
        }
    }
}

extension View {
    func onNearBottom(
        triggerDistance: CGFloat = 600,
        perform action: @escaping () -> Void
    ) -> some View {
        modifier(NearBottomTrigger(triggerDistance: triggerDistance, action: action))
    }
}
```

`triggerDistance: 600` — wynik pomiaru w Instruments. Przy 300pt i szybkim scrollowaniu lista migała — dane nie zdążały przyjść przed jej końcem.

W widoku wystarczy jedna linia:

```swift
List(viewModel.products) { product in
    ProductRow(product: product)
}
.onNearBottom(triggerDistance: 600) {
    Task { await viewModel.fetchMore() }
}
```

---

## Stany ładowania — enum zamiast flag

Zamiast osobnych `isLoading: Bool`, `isRefreshing: Bool` i `errorMessage: String?` — jeden enum. Każdy stan wyklucza pozostałe. Nie możesz jednocześnie ładować i mieć błąd.

```swift
enum LoadingState: Equatable {
    case initial
    case loading
    case showingCachedData
    case refreshing
    case loadingMore
    case loaded
    case offline(String)
    case initialLoadError(String)
    case loadMoreError(String)

    var canLoadMore: Bool {
        switch self {
        case .initial, .loading, .refreshing, .loadingMore:
            false
        case .showingCachedData, .loaded, .offline, .initialLoadError, .loadMoreError:
            true
        }
    }

    var isUserInitiatedLoading: Bool {
        switch self {
        case .loading, .refreshing, .loadingMore: true
        default: false
        }
    }
}
```

`canLoadMore` to jedyna wartość, którą sprawdzam przed `fetchMore()`. Bez osobnych flag. Stan nie może być niespójny.

---

## ViewModel — jak płyną dane

```swift
@MainActor
@Observable
final class ProductsViewModel {
    private(set) var products: [Product] = []
    private(set) var loadingState: LoadingState = .initial
    private(set) var warmUpSyncState: WarmUpSyncState = .idle

    private var total: Int?
    private let limit = 20
    private let service: any ProductServiceProtocol
    private let cacheStore: ProductCacheStore
    private var warmUpTask: Task<Void, Never>?
}
```

### fetchInitial

```swift
func fetchInitial() async {
    guard products.isEmpty else { return }
    loadingState = .loading

    // 1. Pokaż dane z cache — użytkownik widzi coś od razu
    if let cached = try? await cacheStore.fetchCachedProducts(limit: limit, offset: 0),
       !cached.isEmpty {
        products = cached
        loadingState = .showingCachedData
    }

    // 2. Pobierz świeże dane z API
    do {
        let response = try await service.fetchProducts(limit: limit, skip: 0)
        try? await cacheStore.upsertProducts(response.products, total: response.total, startingAt: 0)
        total = response.total
        products = (try? await cacheStore.fetchCachedProducts(
            limit: max(limit, products.count), offset: 0
        )) ?? response.products
        loadingState = .loaded
        await hydrateThumbnails(for: response.products)
        startWarmUpSync()
    } catch {
        loadingState = products.isEmpty
            ? .initialLoadError(error.localizedDescription)
            : .offline(error.localizedDescription)
    }
}
```

Gdy sieć padnie po kroku 1 — użytkownik widzi dane z poprzedniej sesji. Stan `.offline` informuje o braku sieci, ale lista działa.

### fetchMore

```swift
func fetchMore() async {
    guard loadingState.canLoadMore else { return }
    guard products.count < (total ?? Int.max) else { return }

    pauseWarmUpSync()
    loadingState = .loadingMore
    let offset = products.count

    // Najpierw spróbuj z cache — oszczędzasz request sieciowy
    if let cached = try? await cacheStore.fetchCachedProducts(limit: limit, offset: offset),
       !cached.isEmpty {
        appendUnique(cached)
        loadingState = .loaded
        await hydrateThumbnails(for: cached)
        startWarmUpSync()
        return
    }

    // Cache puste — pobierz z API
    do {
        let response = try await service.fetchProducts(limit: limit, skip: offset)
        try? await cacheStore.upsertProducts(response.products, total: response.total, startingAt: offset)
        total = response.total
        appendUnique(response.products)
        loadingState = .loaded
        await hydrateThumbnails(for: response.products)
        startWarmUpSync()
    } catch {
        loadingState = .loadMoreError(error.localizedDescription)
        startWarmUpSync()
    }
}
```

`appendUnique` usuwa duplikaty — na wypadek race condition między `fetchMore` a warm-up sync:

```swift
private func appendUnique(_ newProducts: [Product]) {
    let existingIDs = Set(products.map(\.id))
    products.append(contentsOf: newProducts.filter { !existingIDs.contains($0.id) })
}
```

---

## Miniatury bez blokowania UI

Miniatury pobieramy asynchronicznie — po tym jak zapiszemy metadane produktu do cache. Maksymalnie 4 równolegle, żeby nie przeciążyć sieci.

```swift
private func hydrateThumbnails(for products: [Product]) async {
    let toDownload = products.filter { $0.localThumbnailPath == nil }
    guard !toDownload.isEmpty else { return }

    await withTaskGroup(of: Void.self) { group in
        for (i, product) in toDownload.enumerated() {
            if i >= 4 { _ = await group.next() }   // max 4 równolegle
            group.addTask {
                guard let path = try? await self.thumbnailService.downloadThumbnail(
                    from: product.thumbnail, remoteID: product.id
                ) else { return }
                try? await self.cacheStore.cacheThumbnailPath(path, remoteID: product.id)
            }
        }
    }
    await refreshProductsFromCache()
}
```

`ProductThumbnailService` zapisuje plik do `Caches/thumbnails/<id>.jpg` i zwraca ścieżkę. `ProductImageView` sprawdza ją najpierw — gdy plik jest na dysku, nie sięga do sieci:

```swift
struct ProductImageView: View {
    let product: Product

    var body: some View {
        if let image = localImage {
            image.resizable().aspectRatio(contentMode: .fit)
        } else {
            AsyncImage(url: URL(string: product.thumbnail)) { phase in
                switch phase {
                case .empty:        placeholder
                case .success(let image): image.resizable().aspectRatio(contentMode: .fit)
                case .failure:      placeholder
                @unknown default:   placeholder
                }
            }
        }
    }

    private var localImage: Image? {
        guard let path = product.localThumbnailPath,
              let uiImage = UIImage(contentsOfFile: path) else { return nil }
        return Image(uiImage: uiImage)
    }

    private var placeholder: some View {
        Rectangle().fill(.gray.opacity(0.18))
    }
}
```

---

## Stabilne komórki — stały frame

`AsyncImage` bez wymiarów zmienia wysokość komórki, gdy obrazek wróci z sieci. Lista skacze.

Jeden stały `frame` obejmuje wszystkie fazy — placeholder, sukces i błąd. Lista wie od razu, ile miejsca zarezerwować.

```swift
ProductImageView(product: product)
    .frame(width: 100, height: 100)
    .clipShape(.rect(cornerRadius: 12))
```

---

## Warm-up sync w tle

Gdy pierwsza strona wróci z API, startuję `Task`, który cicho pobiera kolejne strony — aż do limitu 500 produktów. Między requestami czeka 500ms, żeby nie przeciążyć serwera.

```swift
private func warmUpCache() async {
    warmUpSyncState = .syncing
    while !Task.isCancelled {
        let cachedCount = (try? await cacheStore.cachedCount()) ?? 0
        let knownTotal = (try? await cacheStore.metadataTotal()) ?? total
        if let knownTotal, cachedCount >= min(knownTotal, maxOfflineCacheItems) {
            warmUpSyncState = .completed; return
        }
        if loadingState.isUserInitiatedLoading {
            warmUpSyncState = .paused; return
        }
        let budget = min(backgroundLimit, maxOfflineCacheItems - cachedCount)
        guard budget > 0 else { warmUpSyncState = .completed; return }

        do {
            let response = try await service.fetchProducts(limit: budget, skip: cachedCount)
            try await cacheStore.upsertProducts(response.products, total: response.total, startingAt: cachedCount)
            await hydrateThumbnails(for: response.products, refreshVisibleProducts: false)
            try? await Task.sleep(for: .milliseconds(500))
        } catch {
            warmUpSyncState = Task.isCancelled ? .paused : .failed(error.localizedDescription)
            return
        }
    }
    warmUpSyncState = .paused
}
```

`fetchMore()` na wejściu wywołuje `pauseWarmUpSync()`. Gdy skończy, wywołuje `startWarmUpSync()`. Gdy użytkownik scrolluje — sync odpuszcza. Gdy zatrzymuje się — wznawia.

Stan sync widzisz w toolbarze:

```swift
case .syncing:
    HStack(spacing: 4) {
        ProgressView().controlSize(.small)
        Text("Sync...").font(.caption2).foregroundStyle(.secondary)
    }
case .completed:
    Image(systemName: "checkmark.icloud.fill").foregroundStyle(.green)
case .failed:
    Image(systemName: "exclamationmark.icloud.fill").foregroundStyle(.red)
```

---

## UI — overlaye dla stanów

Dwa overlaye: jeden centralny, jeden dolny.

```swift
// Centralny — gdy lista jest pusta
switch viewModel.loadingState {
case .initial, .loading:
    ProgressView().controlSize(.extraLarge)
case .initialLoadError(let message):
    ContentUnavailableView(
        "Nie udało się załadować",
        systemImage: "exclamationmark.triangle",
        description: Text(message)
    )
default:
    EmptyView()
}

// Dolny — gdy lista już pokazuje dane
switch viewModel.loadingState {
case .refreshing:
    statusPill("Odświeżam dane", systemImage: "arrow.clockwise.circle.fill")
case .loadingMore:
    ProgressView().controlSize(.small)
        .frame(maxWidth: .infinity).background(.thinMaterial)
case .offline:
    statusPill("Dane offline", systemImage: "wifi.slash")
case .loadMoreError(let message):
    Text(message).font(.caption).foregroundStyle(.white)
        .padding(.horizontal, 12).padding(.vertical, 8)
        .background(.red, in: Capsule())
default:
    EmptyView()
}
```

`ContentUnavailableView` pokazuj tylko gdy lista jest całkowicie pusta. Gdy masz dane z cache — stan `.offline` to subtelna informacja na dole.

---

## Źródła

- Karin Prater — [How to Build an Infinite Scroll List Without Sacrificing Performance](https://www.youtube.com/watch?v=DInY18u8i2M)
- Chase — [How to use SwiftData to store large files from an API call](https://medium.com/@chase_66332/how-to-use-swiftdata-to-store-large-files-from-an-api-call-8914b3046f88)
