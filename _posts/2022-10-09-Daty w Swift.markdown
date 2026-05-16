---
layout: post
title: "Daty w Swift"
date: 2022-10-09
categories: swift ios
---

![Daty w Swift: Walka z budzikiem](/assets/images/swift-dates.png)

Konwersja dat w Swift — praktyczne snippety do kopiowania: string↔Date, rozszerzenia, formaty i pułapka z UTC.

Zamiana daty na string

``` Swift
let currentDate = Date()
let dateFormatter = DateFormatter()
dateFormatter.dateFormat = "YYYY-MM-dd"
dateFormatter.locale = Calendar.current.locale

let currentDayString = dateFormatter.string(from: currentDate)
```

**Uwaga: jeśli nie wskażemy locale/timezone, używany jest czas UTC!**

Można to zamienić na funkcję:

``` Swift
func extractDate(date: Date, format: String) -> String{
    let formatter = DateFormatter()

    formatter.dateFormat = format
    return formatter.string(from: date)
}
```

i wywoływać np. tak:

``` Swift
print(extractDate(date: currentDate, format: "EEE"))
print(extractDate(date: currentDate, format: "YYYY-MM-dd"))
print(extractDate(date: currentDate, format: "YY/MM/dd"))
```

Można rozszerzyć typ Date:

``` Swift
extension Date {
   func getFormattedDate(format: String) -> String {
        let dateformat = DateFormatter()
        dateformat.dateFormat = format
        dateformat.locale = Calendar.current.locale
        return dateformat.string(from: self)
    }
}
```

i wywoływać tak:

``` Swift
let format = date.getFormattedDate(format: "yyyy-MM-dd HH:mm:ss")
```

Zamiana String → Date

``` Swift
extension String {
    func toDate(withFormat format: String = "yyyy-MM-dd HH:mm:ss") -> Date? {
        let dateFormatter = DateFormatter()
        dateFormatter.locale = Calendar.current.locale
        dateFormatter.dateFormat = format
        return dateFormatter.date(from: self)
    }
}

// wywołanie:
let date2string = "2022-10-10T21:08:13"
let date2 = date2string.toDate(withFormat: "yyyy-MM-dd'T'HH:mm:ss")
```

Wyświetlanie daty w SwiftUI

``` Swift
Text(Date.now.formatted(date: .long, time: .shortened))
```

Przykłady formatów:

``` txt
Wednesday, Sep 12, 2018           --> EEEE, MMM d, yyyy
09/12/2018                        --> MM/dd/yyyy
09-12-2018 14:11                  --> MM-dd-yyyy HH:mm
Sep 12, 2:11 PM                   --> MMM d, h:mm a
September 2018                    --> MMMM yyyy
Sep 12, 2018                      --> MMM d, yyyy
Wed, 12 Sep 2018 14:11:54 +0000   --> E, d MMM yyyy HH:mm:ss Z
2018-09-12T14:11:54+0000          --> yyyy-MM-dd'T'HH:mm:ssZ
12.09.18                          --> dd.MM.yy
10:41:02.112                      --> HH:mm:ss.SSS
```

Więcej formatów: <http://www.unicode.org/reports/tr35/tr35-31/tr35-dates.html#Date_Format_Patterns>
