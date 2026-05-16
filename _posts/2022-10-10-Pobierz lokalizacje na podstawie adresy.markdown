---
layout: post
title: "Pobierz lokalizację na podstawie adresu"
date: 2022-10-10
categories: swift ios
---

![Lokalizacja po adresie: Detektyw i satelita](/assets/images/location-address.png)

Geokodowanie w iOS — zamiana tekstowego adresu na współrzędne `CLLocationCoordinate2D` przy użyciu `CLGeocoder`.

``` Swift
func getLocation(from address: String, completion: @escaping (_ location: CLLocationCoordinate2D?) -> Void) {
    let geocoder = CLGeocoder()
    geocoder.geocodeAddressString(address) { (placemarks, error) in
        guard let placemarks = placemarks,
              let location = placemarks.first?.location?.coordinate else {
            completion(nil)
            return
        }
        completion(location)
    }
}
```

Wywołanie:

``` Swift
getLocation(from: "ul. Marszałkowska 1, Warszawa") { coordinate in
    guard let coordinate = coordinate else { return }
    print("lat: \(coordinate.latitude), lon: \(coordinate.longitude)")
}
```

`CLGeocoder` jest asynchroniczny — wynik trafia do closure. Nie ma gwarancji kolejności wywołań przy wielu żądaniach, więc nie warto wywoływać równolegle.
