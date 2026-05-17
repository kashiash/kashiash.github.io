---
layout: post
title: "SwiftData: zapis danych z API do lokalnej bazy"
date: 2026-05-17
categories: swift ios swiftdata
---

![Dane z serwera lądują w lokalnej bazie SwiftData](/assets/images/swiftdata-api.png)

Otwierasz aplikację. Dane się ładują. Otwierasz znowu — te same dane się ładują od nowa. A przecież nic się nie zmieniło.

Zapisz odpowiedź API w SwiftData — i czytaj z lokalnej bazy. Bez sieci.

---

## Czego potrzebujesz

- Xcode 15+, iOS 17+
- Podstawy SwiftUI: `@State`, `.task`
- Dowolne API zwracające JSON — tu użyję [jsonplaceholder.typicode.com](https://jsonplaceholder.typicode.com)

---

## Wzorzec DTO → @Model

Nie wrzucaj odpowiedzi API bezpośrednio do SwiftData. Podziel dane na dwie struktury.

**DTO** (Data Transfer Object) — struct do dekodowania JSON. Żyje przez jeden request.

**@Model** — klasa SwiftData. Trwa w bazie między sesjami.

```swift
// DTO — tylko do dekodowania JSON
struct PhotoDTO: Identifiable, Codable {
    let albumId: Int
    let id: Int
    let title: String
    let url: String
    let thumbnailUrl: String
}

// @Model — trwa między uruchomieniami
@Model
final class Photo {
    @Attribute(.unique) var remoteID: Int
    var albumId: Int
    var title: String
    var url: String
    var thumbnailUrl: String

    init(from dto: PhotoDTO) {
        self.remoteID = dto.id
        self.albumId = dto.albumId
        self.title = dto.title
        self.url = dto.url
        self.thumbnailUrl = dto.thumbnailUrl
    }
}
```

`@Attribute(.unique)` na `remoteID` zapobiega duplikatom. Gdy rekord już istnieje — SwiftData go zaktualizuje zamiast wstawić nowy.

---

## Serwis sieciowy

Prosty aktor. Pobiera dane z API:

```swift
actor PhotoService {
    func fetchPhotos() async throws -> [PhotoDTO] {
        guard let url = URL(string: "https://jsonplaceholder.typicode.com/albums/1/photos") else {
            throw URLError(.badURL)
        }
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let http = response as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode([PhotoDTO].self, from: data)
    }
}
```

---

## Zapis do SwiftData

W widoku masz `modelContext` przez `@Environment`. Używasz go do wstawiania danych. `@Query` czyta je z bazy automatycznie.

```swift
struct PhotoListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Photo.remoteID) private var photos: [Photo]

    var body: some View {
        List(photos) { photo in
            VStack(alignment: .leading) {
                Text(photo.title)
                AsyncImage(url: URL(string: photo.thumbnailUrl)) { image in
                    image.resizable().scaledToFit().frame(height: 60)
                } placeholder: {
                    Color.gray.opacity(0.2).frame(height: 60)
                }
            }
        }
        .overlay {
            if photos.isEmpty { ProgressView() }
        }
        .task {
            guard photos.isEmpty else { return }
            await loadPhotos()
        }
        .refreshable {
            await loadPhotos()
        }
    }

    private func loadPhotos() async {
        do {
            let dtos = try await PhotoService().fetchPhotos()
            for dto in dtos {
                modelContext.insert(Photo(from: dto))
            }
        } catch {
            print("Błąd: \(error)")
        }
    }
}
```

`.task` uruchamia się raz — gdy `photos` jest puste. Gdy następnym razem otworzysz aplikację, `@Query` odczyta dane z bazy. Sieć nie jest potrzebna.

`.refreshable` daje użytkownikowi ręczne odświeżenie.

---

## Podpięcie kontenera w App

```swift
@main
struct PhotoApp: App {
    var body: some Scene {
        WindowGroup {
            PhotoListView()
        }
        .modelContainer(for: Photo.self)
    }
}
```

Jedna linia. SwiftData sam tworzy bazę i pilnuje schematu.

---

## Kiedy użyć @ModelActor

Powyższy wzorzec działa, gdy operacje na bazie są proste i krótkie. Gdy upsert obejmuje setki rekordów, `modelContext` z `@MainActor` zablokuje UI.

Wtedy wydziel osobny aktor z własnym kontekstem:

```swift
@ModelActor
actor PhotoStore {
    func upsert(_ dtos: [PhotoDTO]) throws {
        let ids = dtos.map(\.id)
        let existing = try fetchExisting(ids: ids)
        let byID = Dictionary(uniqueKeysWithValues: existing.map { ($0.remoteID, $0) })

        for dto in dtos {
            if let photo = byID[dto.id] {
                photo.title = dto.title          // aktualizuj istniejący
            } else {
                modelContext.insert(Photo(from: dto))  // wstaw nowy
            }
        }
        try modelContext.save()
    }

    private func fetchExisting(ids: [Int]) throws -> [Photo] {
        let descriptor = FetchDescriptor<Photo>(
            predicate: #Predicate { ids.contains($0.remoteID) }
        )
        return try modelContext.fetch(descriptor)
    }
}
```

`@ModelActor` tworzy aktor z własnym `ModelExecutor`. Operacje na bazie nie blokują głównego wątku. Wzorzec sprawdza się szczególnie przy paginacji i gdy pobierasz duże zbiory danych.

---

## Co dalej

- **Duże pliki (zdjęcia, wideo)** — użyj `@Attribute(.externalStorage)` dla `Data?`. Opisałem to w [poprzednim wpisie](/2026/05/16/swiftdata-store-large-files-pl.html).
- **Paginacja i infinite scroll** — `@ModelActor` + `sortIndex` + warm-up w tle. O tym w następnym wpisie.
