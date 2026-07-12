## Proje Amacı

BahisKalkanı, TEKNOFEST 2026 için geliştirilen bir Android uygulamasıdır (Kotlin). Amaç: bir **AccessibilityService** ile ekrandaki metinleri okuyup bahse teşvik eden içerikleri tespit etmek ve bu içerikleri **overlay** ile kapatmak.

## Mimari Kararlar

- **Tespit katmanı değiştirilebilir olmalı:** Faz 1'de tespit basit bir kelime listesiyle yapılacak; Faz 2'de bu liste bir makine öğrenmesi modeliyle değiştirilecek. Bu yüzden tespit mantığı tek bir değiştirilebilir fonksiyon/arayüz arkasında tutulmalı (ör. `(metin) -> tespit sonucu` imzalı bir arayüz); AccessibilityService ve overlay kodu tespit yönteminin ayrıntısını bilmemeli.
- **KVKK kuralı (kesin):** Hiçbir kullanıcı verisi kaydedilmeyecek ve hiçbir ağ isteği atılmayacak. Erişilebilirlik servisinin okuduğu ekran metinleri kalıcı depoya yazılmaz, loglanmaz, cihaz dışına çıkmaz. `INTERNET` izni eklenmemeli; ağ bağımlılığı olan kütüphaneler tercih edilmemeli.

## Teknik Bilgiler

- Paket/namespace: `com.teknofest.bahiskalkani`
- Kotlin 2.2 + Jetpack Compose (Material 3), minSdk 26, target/compileSdk 36, Java 11
- Bağımlılıklar `gradle/libs.versions.toml` sürüm kataloğu üzerinden yönetilir — yeni bağımlılığı önce kataloğa ekle, `app/build.gradle.kts` içinde `libs.*` ile referans ver
- Compose ekranlarını `BahisKalkaniTheme` ile sarmala (`ui/theme/` altında; koyu tema ve Android 12+ dinamik renk destekli)

## Komutlar

Depo kökünden Gradle wrapper kullan (`gradlew.bat` Windows'ta, `./gradlew` diğer sistemlerde):

- Debug APK derle: `gradlew.bat assembleDebug`
- Bağlı cihaza/emülatöre kur: `gradlew.bat installDebug`
- Birim testleri (JVM): `gradlew.bat testDebugUnitTest`
  - Tek sınıf: `gradlew.bat testDebugUnitTest --tests "com.teknofest.bahiskalkani.ExampleUnitTest"`
  - Tek metot: `--tests` içindeki sınıfa `.metotAdi` ekle
- Cihaz testleri (çalışan emülatör/cihaz gerekir): `gradlew.bat connectedDebugAndroidTest`
- Lint: `gradlew.bat lint` (rapor: `app/build/reports/lint-results-debug.html`)

## Yapı

- `app/src/main/java/com/teknofest/bahiskalkani/` — uygulama kodu
  - `detection/` — `Detector` arayüzü (tek değiştirilebilir tespit noktası) ve Faz 1 `KeywordDetector`; kelime listesinin tek kaynağı `app/src/main/assets/keywords.json` (Chrome eklentisiyle eşdeğer tutulur)
  - `overlay/` — `OverlayController` (TYPE_ACCESSIBILITY_OVERLAY; bölge başına iki pencere: dokunuş-geçirgen kapak + ayrı dokunulabilir "yine de göster" butonu — kapak dokunulabilir yapılırsa kaydırmayı öldürür, yapma)
  - `service/` — `ScreenReaderService` (AccessibilityService; ekranı tarar, tespitçiyi çağırır, overlay'i günceller)
  - `stats/` — `BlockStats` (engelleme sayacı; KVKK gereği yalnızca bellekte, yalnızca sayı)
- `app/src/test/` — JVM birim testleri (JUnit 4)
- `app/src/androidTest/` — cihaz/Compose UI testleri

Ekip, görev dağılımı ve proje bağlamı için PROJE.md dosyasına bak.
