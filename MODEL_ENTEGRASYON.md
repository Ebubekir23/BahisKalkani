# Tespit Modeli Entegrasyon Kontratı (Faz 2)

Hedef okuyucu: Yapay Zekâ Sorumlusu. Bu belge, modelin Android Kalkan'a
sorunsuz takılabilmesi için teslim formatını ve teknik sınırları tanımlar.
24 Temmuz baseline hedefinden önce "Açık sorular" bölümü birlikte netleştirilmeli.

## Uygulamadaki takılma noktası

Tespit mantığı tek bir arayüzün arkasında:

```kotlin
fun interface Detector {
    fun isBettingContent(text: String): Boolean
}
```

Model geldiğinde `TfLiteDetector : Detector` sınıfı yazılacak ve serviste tek
satır değişecek. Kelime listesi (`assets/keywords.json`) yedek olarak kalacak:
model VEYA kelime listesi eşleşirse içerik engellenir.

## Teslim edilecekler

1. `model.tflite` dosyası (APK içine, `assets/` altına gömülecek)
2. Ön işleme spesifikasyonu — tercihen tokenizasyon modelin İÇİNDE gömülü olsun;
   değilse `vocab` dosyası + Kotlin'de yeniden yazılabilecek kadar net kurallar
3. Skor eşiği önerisi (threshold) ve nasıl kalibre edildiği
4. ~100 örneklik etiketli kabul test seti (pozitif/negatif karışık; sansürlü
   varyasyonlar — "b0nus", "ç3vrim" — ve masum ama riskli kelimeler —
   "Betül", "alfabetik" — dahil). Entegrasyonun doğruluğu bu setle sınanacak.

## Teknik sınırlar (KVKK kararı + demo cihazı)

- Tamamen cihaz üstü çalışır; ağ erişimi yok, telemetri yok, uygulamada
  `INTERNET` izni yok ve eklenmeyecek
- Dosya boyutu: ≤ 10 MB hedef (APK'ya gömülüyor)
- Gecikme: orta segment telefonda metin başına ≤ 20 ms — ekran taraması tek
  olayda onlarca metin sorgulayabilir, toplam bütçe ~200 ms
- Girdi: UTF-8 Türkçe metin, tipik 5–200 karakter (ekrandaki tek bir öğenin
  metni; tam sayfa değil)
- Çıktı: 0..1 arası tek skor (bahse teşvik olasılığı); eşiği uygulama uygular

## Kalkan tarafında şimdiden yapılanlar (mükerrer iş olmasın)

- Kelime listesi eşleşmesi + "içeriyor mu" türev yakalama (`KeywordDetector`)
- Basit sansür normalizasyonu: 0→o, 1→i, 3→e, 4→a, 5→s, 7→t, @→a, $→s
  karakter dönüşümü eşleşmeden önce uygulanıyor. Model bunun ötesini
  (boşluklu/noktalı yazım, yeni argo, bağlam) hedeflemeli.
- Marka muafiyeti: "bahiskalkanı" türevleri tespitten muaf (uygulamanın adı
  "bahis" içeriyor). Model eğitiminde de negatif örnek olarak eklenmeli.

## Açık sorular (24 Temmuz'dan önce cevaplanmalı)

- Tokenizasyon modelin içinde mi, dışında mı?
- Maksimum girdi uzunluğu ne; uzun metin kesilecek mi, kayan pencere mi?
- TFLite çalışma zamanı olarak hangi paket hedefleniyor (LiteRT /
  `org.tensorflow:tensorflow-lite`)? Bağımlılık, model teslimiyle birlikte
  bu repoya eklenecek.
- Eşik kalibrasyonu hangi veriyle yapılacak (öneri: sandbox uygulamasının
  gönderi JSON'u + kabul test seti, birlikte)?
