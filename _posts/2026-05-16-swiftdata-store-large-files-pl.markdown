---
layout: post
title: "Użycie SwiftData do przechowywania dużych plików z wywołania API"
date: 2026-05-16
categories: swift ios
---

![SwiftData i duże pliki: Wieloryb w walizce](/assets/images/swiftdata-large-files.png)

Zdjęcia, podcasty, a nawet pliki wideo mogą być przechowywane w SwiftData. W tym artykule omówimy, jak przechowywać te treści w SwiftData i jak je wyświetlać, korzystając z atrybutu `.externalStorage`.

## Model SwiftData z obsługą zewnętrznego przechowywania

Atrybut `@Attribute(.externalStorage)` informuje SwiftData, że dane powinny być przechowywane poza głównym plikiem bazy danych. To kluczowe dla wydajności przy dużych plikach.

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
