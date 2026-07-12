# Ebubekir YILMAZ — Android Kalkan (proje lideri)

## Görev

Bu repodaki Android uygulaması: AccessibilityService ile ekran metnini okur,
tespit motoruna sorar, bahis içeriğinin üstüne overlay çizer. Ek olarak proje
liderliği: ekipler arası koordinasyon, entegrasyonlar, rapor demosu.

## Mevcut durum (12 Temmuz)

Çekirdek çalışıyor: servis + kelime listesi tespiti (sansürlü yazım dahil) +
dokunuş-geçirgen kapaklar + "yine de göster" + toplu çip + ana ekran + sayaç.

## Yapılacaklar

1. **Model entegrasyonu (24 Temmuz sonrası):** Halil'in TFLite modeli gelince
   `TfLiteDetector : Detector` sınıfını yaz, `ScreenReaderService` içinde
   tespitçiyi değiştir (tek satır). Kelime listesi yedek kalacak: model VEYA
   liste eşleşirse engelle. Kabul test setiyle doğrula. Teslim formatı:
   [halil-tespit-modeli.md](halil-tespit-modeli.md)
2. **Sandbox uçtan uca testi:** Ezgi'nin ilk kaydırılabilir sürümü çıkar çıkmaz
   aynı cihazda ortak test; overlay konumlandırması sandbox'ta kusursuz olmalı
   (final demosu orada). Uyum kuralları: [ezgi-demo-sandbox.md](ezgi-demo-sandbox.md)
3. **Overlay cilası:** kapak görünümü (renk/animasyon), kaydırmada takip
   akıcılığı, gereksiz tarama azaltma (pil).
4. **Rapor malzemesi (4-5 Ağustos):** sandbox + kalkan ekran kaydı, ana ekran
   ve sayaç görüntüleri.
5. **Koordinasyon:** keywords.json değişince Aylin'e iletmek; açık soruları
   (MODEL_ENTEGRASYON.md sonundaki) Halil'le bu hafta kapatmak.

## Nasıl

- Derleme/test komutları ve mimari kurallar: [CLAUDE.md](../CLAUDE.md)
- Kod yapısı: `detection/` (Detector arayüzü — tek değiştirilebilir nokta),
  `overlay/`, `service/`, `stats/`
- Değişmez kurallar: KVKK (veri kaydı yok, ağ yok, INTERNET izni yok),
  tespit her zaman Detector arayüzünün arkasında
