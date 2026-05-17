---
layout: post
title: "Użycie SwiftData do przechowywania dużych plików z wywołania API"
date: 2026-05-16
categories: swift ios
---

![SwiftData i duże pliki: Wieloryb w walizce](/assets/images/swiftdata-large-files.png)

Jeżeli chcesz, żeby użytkownik twojej aplikacji iOS oglądał zdjęcia, słuchał podcastów albo otwierał wideo bez połączenia z internetem — i robił to płynnie, bez sekundowych zamulień na każdym przewinięciu listy — musisz trzymać duże pliki lokalnie. Standardowo SwiftData wrzuca wszystkie pola do głównego pliku bazy, więc po kilkuset rekordach każde zapytanie zwalnia.

Tego ratuje atrybut `@Attribute(.externalStorage)`. SwiftData zachowuje metadane w bazie, a sam binarny content trzyma jako osobne pliki obok. Dalej pokazuję model, pobieranie z API i wyświetlanie z cache.

## Jak to działa — przepływ danych

```mermaid
sequenceDiagram
    actor U as Użytkownik
    participant App as Aplikacja
    participant API as JSONPlaceholder API
    participant Net as URLSession
    participant SD as SwiftData (ModelContext)
    participant Disk as Pliki externalStorage
    Note over App,Disk: --- pierwsze uruchomienie ---
    U->>App: otwiera widok galerii
    App->>API: GET /photos
    API-->>App: lista PhotoObject (bez binarki)
    loop dla każdego zdjęcia
        App->>Net: GET url do binarki
        Net-->>App: Data
        App->>SD: PhotoObject(photo: Data)
        SD->>Disk: zapisuje binarkę osobno
        SD->>SD: zapisuje metadane w bazie
    end
    Note over App,Disk: --- kolejne uruchomienia (offline) ---
    U->>App: otwiera widok galerii
    App->>SD: @Query PhotoObject
    SD->>Disk: ładuje binarki na żądanie
    SD-->>App: rekordy z polem photo
    App-->>U: SwiftUI Image
```

## Model SwiftData z obsługą zewnętrznego przechowywania

Atrybut `@Attribute(.externalStorage)` informuje SwiftData, że dane powinny być przechowywane poza głównym plikiem bazy. To kluczowe dla wydajności przy dużych plikach.

```swift
@Model
class PhotoObject {
    var albumId: Int
    @Attribute(.unique) var id: Int
    var title: String
    var url: String
    var thumbnailUrl: String
    @Attribute(.externalStorage) var photo: Data?
    
    init(albumId: Int, id: Int, title: String, url: String, thumbnailUrl: String, photo: Data? = nil) {
        self.albumId = albumId
        self.id = id
        self.title = title
        self.url = url
        self.thumbnailUrl = thumbnailUrl
        self.photo = photo
    }
}
```

## Pobieranie i zapisywanie danych binarnych

W `WebService` pobieramy dane obrazu asynchronicznie i przypisujemy je do encji przed zapisem w `ModelContext`.

```swift
private func getDataFrom(url: String) async -> Data? {
    do {
        let (data, _) = try await URLSession.shared.data(from: URL(string: url)!)
        return data
    } catch {
        print("Błąd pobierania danych: \(error)")
        return nil
    }
}
```

## Wyświetlanie danych offline

Aby aplikacja działała offline, pobieramy obrazy bezpośrednio z właściwości `photo` i konwertujemy je na `UIImage`.

```swift
if let imageData = item.photo,
   let uiImage = UIImage(data: imageData) {
    Image(uiImage: uiImage)
        .resizable()
        .scaledToFit()
        .frame(width: 50, height: 50)
}
```

Dzięki temu Twoja aplikacja może działać w pełni offline po początkowym pobraniu danych.
