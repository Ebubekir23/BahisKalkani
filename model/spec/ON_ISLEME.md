# Ön İşleme Spesifikasyonu (model v1)

Modelin Python'da eğitilirken gördüğü girdi ile Kotlin'de çalışma anında
alacağı girdi **birebir aynı** olmak zorunda; en küçük fark sessizce yanlış
skorlara yol açar. Bu belge tek kaynaktır; referans implementasyonlar:

- Python: [`scripts/train.py`](../scripts/train.py) → `preprocess()`
- Kotlin: [`kotlin/TfLiteDetector.kt`](../kotlin/TfLiteDetector.kt) → `preprocess()`

## Adımlar (sırayla)

1. **Unicode NFC normalizasyonu.**
   - Python: `unicodedata.normalize("NFC", text)`
   - Kotlin: `Normalizer.normalize(text, Normalizer.Form.NFC)`
2. **Türkçe küçük harfe çevirme + U+0307 temizliği.** Kotlin'de
   `lowercase(Locale("tr"))` doğru sonucu doğrudan verir (`İ→i`, `I→ı`).
   Python bunu bilmez; eğitim tarafında önce `İ→i`, `I→ı` elle uygulanır,
   sonra `.lower()` çağrılır. Ardından İKİ TARAFTA DA birleşik nokta
   (U+0307) silinir — ayrık yazılmış `i̇` (i + U+0307) girdileri de böylece
   aynı işlenir. Test vektörleri:
   `"BAHİS" → "bahis"`, `"IŞIK" → "ışık"`, `"CASINO" → "casıno"` (evet,
   Türkçe kuralla `I→ı`; iki taraf da aynı şekilde yaptığı sürece sorun değil).
3. **Kodpoint → id eşleme** (`cikti/model_vocab.json` içindeki `karakterler`
   haritası). Haritada olmayan her kodpoint **OOV = 1** olur. `pad = 0`.
   - DİKKAT (Kotlin): emoji'ler UTF-16'da çift `Char` kaplar. `for (c in text)`
     ile DEĞİL, **`text.codePoints()`** ile dolaşın ve her kodpointi
     `String`'e çevirip haritada arayın (referans koda bakın).
4. **Kes ve doldur:** ilk **192 kodpoint** alınır (uzunsa gerisi atılır),
   kısaysa sona `0` (pad) eklenir. Çıktı: `IntArray(192)`.
5. Model çıktısı: `float32[1][1]` — 0..1 arası "bahse teşvik" skoru.
   **Eşik modelin değil uygulamanın işi**; önerilen değer
   [`cikti/esik.json`](../cikti/esik.json) dosyasında.

## Bilinçli tasarım kararları

- **Sansür ikamesi (0→o, 1→i …) ön işlemede YOKTUR.** KeywordDetector'daki
  haritanın aksine model ham karakterleri görür; sansürlü yazımları eğitim
  verisindeki örnekler + veri çoğaltma ile öğrenir. Böylece rakamlar
  ("oran 2.5", "%100 bonus") sinyal olarak korunur ve Kotlin tarafında ekstra
  adım gerekmez.
- **Tokenizasyon model dışında ama trivialdir** (~15 satır Kotlin). TFLite'ın
  string operatör desteği zayıf olduğundan tokenizasyonu modele gömmek
  (SELECT_TF_OPS) boyut ve bağımlılık maliyeti getiriyordu; karakter→id
  eşlemesi deterministik olduğundan dışarıda tutmak güvenli.
- **Uzun metin stratejisi:** ekran öğeleri tipik ≤ 200 karakter; ilk 192
  kodpoint yeterli. Kalkan ileride tam sayfa metni tek parça verirse Kotlin
  tarafında 96 kodpoint adımlı kayan pencere + pencere başına skor maksimumu
  önerilir (şimdilik gerekmez, kod basit kalsın).

## Sözlük (`model_vocab.json`)

- `max_len`: 192, `pad`: 0, `oov`: 1
- `karakterler`: Türk alfabesi + qwx (32), rakamlar (10), boşluk + yaygın
  noktalama/semboller (₺ € dahil), bahis paylaşımlarında sık görülen 9 emoji
  (💚🔥🎰💰⚽🎁✅⭐📲). Toplam ~83 giriş.
- Sözlük eğitim script'inde sabittir (veriden türetilmez): yeniden eğitimde
  id'ler kaymaz, Kotlin tarafı değişmez.
