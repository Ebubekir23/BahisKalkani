# 🛡 BahisKalkanı

TEKNOFEST 2026 "Bağımlılıklarla Mücadelede Teknolojik Uygulamalar" yarışması
projesi. Ekrandaki bahse teşvik eden içerikleri cihaz üstünde tespit edip
overlay ile kapatan Android uygulaması. Hiçbir veri kaydedilmez, hiçbir ağ
isteği atılmaz.

## Yeni katıldıysan okuma sırası

1. **[PROJE.md](PROJE.md)** — ürün ne, kim neyin sahibi, ortak kurallar, takvim (5 dk)
2. **`görevler/` altındaki kendi dosyan** — görevin, nasıl yapacağın, teslim listesi:
   - [Ebubekir — Android Kalkan](görevler/ebubekir-android-kalkan.md)
   - [Aylin — Chrome Eklentisi](görevler/aylin-chrome-eklentisi.md)
   - [Ezgi — Demo Sandbox](görevler/ezgi-demo-sandbox.md)
   - [Halil — Tespit Modeli](görevler/halil-tespit-modeli.md)
3. Gerektikçe:
   - **Aylin:** [keywords.json](app/src/main/assets/keywords.json) (aynen
     kopyalanacak tek kaynak) + [KeywordDetector.kt](app/src/main/java/com/teknofest/bahiskalkani/detection/KeywordDetector.kt)
     (birebir taşınacak eşleşme mantığı)
   - **Halil:** [Detector.kt](app/src/main/java/com/teknofest/bahiskalkani/detection/Detector.kt)
     (modelin takılacağı arayüz)
   - **Ezgi:** gönderi JSON'unu yazarken [keywords.json](app/src/main/assets/keywords.json)

[CLAUDE.md](CLAUDE.md) bu repoda kod yazanlar içindir (mimari kurallar,
derleme/test komutları); diğer bileşen sahiplerinin okuması gerekmez.

## Hızlı başlangıç (bu repo)

```
gradlew.bat assembleDebug      # derle
gradlew.bat installDebug       # bağlı cihaza kur
gradlew.bat testDebugUnitTest  # birim testleri
```

Kurulumdan sonra: telefonda **Ayarlar → Erişilebilirlik → BahisKalkanı**'nı
etkinleştir. Doğrulama: `adb logcat -s BahisKalkani`.

## Kesin kurallar (KVKK)

- Kullanıcı verisi kaydedilmez; okunan ekran metinleri saklanmaz, loglanmaz
- Ağ isteği atılmaz; `INTERNET` izni yok ve eklenmeyecek
- Tespit mantığı `Detector` arayüzünün arkasında kalır (Faz 2'de TFLite
  modeli aynı arayüze takılacak)
