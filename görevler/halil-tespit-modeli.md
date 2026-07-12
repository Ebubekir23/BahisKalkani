# Halil Hadra UZUN — Tespit Modeli (Yapay Zekâ)

## Görev

Türkçe bahis-teşvik metni sınıflandırıcısı: girdi olarak kısa bir ekran metni
alır, 0..1 arası "bahse teşvik" skoru döner. Hazır olunca Android Kalkan'daki
kelime listesinin yanına takılacak (model VEYA liste eşleşirse engelle).
Teslim formatının tam tanımı: [MODEL_ENTEGRASYON.md](../MODEL_ENTEGRASYON.md)
— bu dosya görevin özeti ve yol önerisidir.

## Teslim edilecekler (özet)

1. `model.tflite` (≤ 10 MB; APK'ya gömülecek)
2. Ön işleme spesifikasyonu (tercihen tokenizasyon model İÇİNDE; değilse
   vocab + Kotlin'de yeniden yazılabilir net kurallar)
3. Skor eşiği önerisi + kalibrasyon notu
4. ~100 örneklik etiketli kabul test seti (sansürlü varyasyonlar ve
   "Betül"/"alfabetik" gibi tuzak negatifler dahil)

## Sınırlar (KVKK + demo cihazı)

- Tamamen cihaz üstü; eğitim dahil hiçbir aşamada kullanıcı verisi yok,
  çalışma anında ağ yok
- Metin başına ≤ 20 ms (orta segment telefon); tek olayda onlarca metin
  sorgulanabilir
- Girdi tipik 5–200 karakter (ekrandaki tek öğenin metni, tam sayfa değil)

## Nasıl (önerilen yol)

1. **Veri:** elle + üretken çeşitleme ile kendi setini kur. Pozitifler:
   kupon paylaşımı, bonus/çevrim dili, Telegram davetleri, sansürlü yazımlar
   ("b0nus", "ç3vrim", boşluklu "b a h i s"). Negatifler: günlük sosyal medya
   dili + tuzak kelimeliler (spor haberi, "Betül", "iddialı" gibi). Sandbox
   gönderi JSON'u da (Ezgi) veri kaynağı olarak kullanılabilir.
2. **Baseline'ı basit tut (24 Temmuz):** karakter n-gram TF-IDF + lojistik
   regresyon bile kelime listesinden iyi olabilir; TFLite'a çevrilebilir
   olduğundan emin ol. Alternatif: Keras'ta küçük embedding + CNN/GRU metin
   sınıflandırıcısı → doğrudan TFLite'a dönüşür.
3. **Kaçınılacaklar:** büyük transformer'lar (boyut/gecikme bütçesini aşar),
   ağ gerektiren tokenizer'lar, Python'a bağımlı ön işleme (Kotlin'de
   yeniden yazılamıyorsa entegre edilemez).
4. **Doğrulama:** kabul test setinde hedef ≥ %90 doğruluk + tuzak
   negatiflerde sıfır yanlış pozitif; gecikmeyi telefonda ölçmek için
   Ebubekir'le entegrasyon sonrası ortak test.

## Bu hafta cevaplanacak açık sorular (Ebubekir'le birlikte)

- Tokenizasyon modelin içinde mi, dışında mı?
- Maksimum girdi uzunluğu; uzun metin kesme stratejisi?
- Hangi TFLite çalışma zamanı (LiteRT / org.tensorflow:tensorflow-lite)?
- Eşik kalibrasyonu hangi veriyle?

## Takvim

- **24 Temmuz:** baseline model entegrasyona hazır (kontrat formatında)
- 4-5 Ağustos: rapor için model entegre edilmiş demo (yetişmezse rapor
  kelime listesi + "model entegrasyonu sürüyor" anlatımıyla çıkar — baskı
  yok ama hedef bu)
