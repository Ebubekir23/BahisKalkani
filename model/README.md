# Tespit Modeli — Detaylı Rehber

Türkçe bahis-teşvik metni sınıflandırıcısı. Bu belge dört soruya cevap verir:
**(1)** bu model projeyle/görevle gerçekten ilgili mi, nerede ve nasıl
kullanılacak; **(2)** veriler neye göre sınıflandırıldı; **(3)** model hangi
yöntemlerle ve NEDEN böyle hazırlandı; **(4)** kodlarda ne var, ne yapıldı.

---

## 1. Modelin projedeki yeri — görevle bağı

BahisKalkanı (TEKNOFEST 2026 "Bağımlılıklarla Mücadelede Teknolojik
Uygulamalar"), telefonda ekrandaki metinleri okuyup **yasa dışı bahis teşvik
içeriğini kullanıcıya ulaşmadan kapatan** bir koruma uygulamasıdır. Uygulama
şu an Faz 1'de: tespit, `assets/keywords.json` kelime listesiyle yapılıyor.
Kelime listesi "bahis", "iddaa" gibi açık terimleri yakalar ama şunları
KAÇIRIR: boşluklu yazım ("b a h i s"), yeni argo ("kasa katladık", "yeşil
gördük"), kelimesiz teşvik ("hoca dünkü maçtan 5 kat aldık, DM at").
**Bu model tam olarak o boşluğu kapatmak için var** — Faz 2'nin kendisi.

[görevler/halil-tespit-modeli.md](../görevler/halil-tespit-modeli.md)
sözleşmesindeki teslimatlarla birebir eşleşme:

| Görev dosyasındaki teslimat | Bu klasördeki karşılığı |
|---|---|
| 1. `model.tflite` (≤10 MB, APK'ya gömülecek) | `cikti/model.tflite` (88 KB) |
| 2. Ön işleme speki (Kotlin'de yeniden yazılabilir) | `spec/ON_ISLEME.md` + `kotlin/TfLiteDetector.kt` + `cikti/model_vocab.json` |
| 3. Skor eşiği önerisi + kalibrasyon yöntemi | `cikti/esik.json` (0.63) + bu belgenin §4.4'ü |
| 4. ~100 örneklik kabul test seti (sansürlü + tuzaklı) | `data/kabul_testi.jsonl` (100) + bonus: `data/kabul_gercek.jsonl` (120 gerçek örnek) |

Görevin sınırları da korunur: **tamamen cihaz üstü** (ağ yok, `INTERNET`
izni yok), kişisel veri kaydı yok, metin başına ≤20 ms bütçesi (ölçülen:
0,12 ms), girdi 5-200 karakterlik tek ekran öğesi metni.

## 2. Uygulamada nerede ve nasıl kullanılacak

Çalışma anı akışı (her ekran değişiminde):

```
AccessibilityService ekran metnini okur (ScreenReaderService.kt)
        │  düğüm başına bir metin (5-200 karakter)
        ▼
Detector.isBettingContent(text)          ← tek değiştirilebilir nokta
        │
        ├── KeywordDetector (Faz 1, kalıyor)  ─┐
        │                                      ├─ VEYA → biri "evet" derse
        └── TfLiteDetector (BU MODEL)         ─┘
        ▼
OverlayController: içeriğin üstüne opak kapak + uyarı + "yine de göster"
```

Entegrasyon adımları (Ebubekir, [YOL_HARITASI.md](YOL_HARITASI.md)'de sahipli liste):

1. `cikti/model.tflite` + `cikti/model_vocab.json` → `app/src/main/assets/`
2. `kotlin/TfLiteDetector.kt` → `app/src/main/java/com/teknofest/bahiskalkani/detection/`
3. `app/build.gradle.kts` bağımlılığı: `com.google.ai.edge.litert:litert:1.2.0`
   (eski `org.tensorflow:tensorflow-lite` paketi AGP 9'da derlenmiyor;
   LiteRT API/import uyumlu, kod değişmez)
4. `ScreenReaderService` (satır ~31) birleşik tespitçi:
   `Detector { t -> keyword.isBettingContent(t) || model.isBettingContent(t) }`
5. Kabul setleriyle doğrulama + telefonda gecikme ölçümü

Model **yalnızca 0..1 arası skor üretir**; engelleme kararını eşikle
uygulama verir (eşik = ayrı ayar, model dosyasına gömülü değil). Kelime
listesi güvenlik ağı olarak kalır: model bir şeyi kaçırırsa liste, liste
kaçırırsa model yakalar.

## 3. Veriler neye göre sınıflandırıldı

### 3.1 Etiket tanımı (tüm veri işlerinde aynı sözleşme)

- **label=1 (bahse teşvik):** okuyanı bahse YÖNLENDİREN içerik — kupon
  paylaşımı/çağrısı, bonus-çevrim promosyonu, site/kanal tanıtımı, katılım
  daveti, kazanç vaadi ("yatır kazan", "DM at", "linkten üye ol"). Bahis
  sitesinin kendi tanıtım metni de teşviktir.
- **label=0 (teşvik yok):** geri kalan her şey — kritik incelik şurada:
  bahis KELİMESİ geçen ama teşvik İÇERMEYEN metinler de 0'dır:
  "yasa dışı bahis operasyonu: 12 gözaltı" (haber), "her gün bahis reklamı
  geliyor, bıktım" (şikayet), kumar bağımlılığı uyarıları, siteye çağrısız
  skor tahmini ("bence Fener 2-1 alır"). Model bunlara alarm verirse
  uygulama haber sitelerini ve mağdurların şikayetlerini kapatır — kabul
  edilemez. Bu yüzden bunlar "zor negatif" olarak bilinçli fazla temsil edildi.
- **Tuzak negatifler:** bahis terimlerine YÜZEYSEL benzeyen masum kelimeler —
  "Betül" (bet), "alfabetik" (bet), "bahsettiğim" (bahis kökü), "iddialı"
  (iddaa değil), "BahisKalkanı" (uygulamanın kendi adı — marka muafiyeti).
  Sözleşme gereği bunlarda **sıfır yanlış alarm** şartı var; kabul setinde
  `tuzak=true` bayrağıyla ayrı ölçülür.
- Kararsız kalınabilecek örnekler veri setine hiç alınmadı (üretici ve
  denetçi ajanlara "tartışmalıysa AT" kuralı).

### 3.2 Sentetik set — `data/egitim.jsonl` (1.543 örnek)

Görev dosyasının önerdiği yol ("elle + üretken çeşitleme ile kendi setini
kur"). 14 kategoride (7 pozitif: kupon, bonus/çevrim, Telegram daveti,
sansürlü yazım, casino/slot, dolaylı-argo, canlı bahis; 7 negatif: günlük
dil, spor sohbeti, tuzak kelimeler, finans/kazanç, haber/uyarı, oyun/uygulama
dili, sınır örnekleri) ayrı üretici ajanlarla üretildi; **her parti bağımsız
bir denetçi ajandan geçti** (etiket doğruluğu, gerçekçilik, uzunluk).
İlk modelin kabul testindeki hata analizine göre üç zayıf kategoriye
(aksansız sade teşvik, oyun/başarım dili, coşkulu günlük dil) 479 hedefli
örnek eklendi. Güçlü yanı: sansürlü varyasyon ve tuzak kelime kapsamı
kontrollü. Zayıf yanı: kalıpları gerçek hayattan düzgün — bu yüzden:

### 3.3 Gerçek set — `data/gercek.jsonl` (1.375 örnek)

Halka açık, üyeliksiz kaynaklardan toplandı (ayrıntı + lisanslar:
[data/GERCEK_VERI_KAYNAKLARI.md](data/GERCEK_VERI_KAYNAKLARI.md)):
Telegram bahis kanallarının web önizlemeleri (18 kanal — gerçek teşvik
üslubu), sikayetvar/ekşi'de mağdurların birebir alıntıladığı spam SMS'ler
(en değerli saha verisi), HuggingFace açık lisanslı korpuslar (bahis sitesi
tanıtım cümleleri + normal Türkçe), haber RSS başlıkları (operasyon haberleri
dahil), gerçek kampanya dili. Süreç: toplama → KVKK maskeleme (telefon/IBAN,
üç katman) → tekilleştirme (rakam-bağımsız şablon anahtarı ile) → **26
bağımsız denetçiyle etiket denetimi** (1.531 adaydan 36 tartışmalı örnek
atıldı, 2 etiket düzeltildi).

### 3.4 Kabul setleri — ölçümün dürüstlüğü

- `kabul_testi.jsonl` (100: 50/50, 12 tuzak): sözleşme seti. Görev
  dosyasının şart koştuğu sansürlü örnekler ("b0nus", "ç3vrim", "b a h i s")
  içinde; çekişmeli (adversarial) ikinci denetimden geçti.
- `kabul_gercek.jsonl` (120: 60/60): sahayı temsil eden set — 60 pozitifin
  50'si gerçek Telegram gönderisi + gerçek spam SMS alıntısı.
- İki set de eğitim verisinden **ayrık** (normalize edilmiş metin anahtarıyla
  kod düzeyinde garanti; eğitime çakışan aday alınmaz).

## 4. Model hangi yöntemlerle, neden böyle hazırlandı

### 4.1 Neden karakter seviyesi CNN? (yöntem seçiminin gerekçesi)

Görevin kısıtları alternatifleri tek tek eler:

| Alternatif | Neden elendi |
|---|---|
| Büyük transformer (BERTurk vb.) | 100+ MB model, 10 MB sınırını ve 20 ms bütçesini aşar; görev dosyası açıkça "kaçının" diyor |
| Kelime seviyesi model + hazır tokenizer | Sansürlü yazım ("b0nus") kelime sınırlarını bozar; tokenizer'ların çoğu Python'a/ağa bağımlı → Kotlin'de yeniden yazılamaz, göreve aykırı |
| TF-IDF + lojistik regresyon | TFLite'a çevirisi dolaylı; n-gram sözlüğü büyür; sansür varyasyonlarında genelleme zayıf |
| **Karakter CNN (seçilen)** | Sansür/boşluk varyasyonlarına doğal dayanıklı (karakter deseni öğrenir), tokenizasyonu ~15 satır Kotlin (spec'e uygun), ~86 bin parametre → 88 KB, 0,12 ms |

Karakter yaklaşımının göreve özgü avantajı: "b0nus", "b.a.h.i.s", "bahiis"
aynı karakter komşuluk desenlerini taşır — kelime modeli bunları üç ayrı
bilinmeyen kelime görür, karakter modeli aynı örüntünün varyantı görür.

### 4.2 Mimari

```
Girdi: int32[192]  (kodpoint id'leri; sözlük ~85 karakter: TR alfabe +
                    rakam + noktalama + 9 emoji; 0=pad, 1=bilinmeyen)
Embedding(85→48) → SpatialDropout1D(0.09)
→ paralel Conv1D(96 filtre; çekirdek 3, 4, 5) → her biri GlobalMaxPooling
→ birleştir → Dropout(0.30) → Dense(64, relu) → Dropout(0.25)
→ Dense(1, sigmoid) = "bahse teşvik" skoru (0..1)
```

Paralel farklı çekirdek boyutları farklı uzunlukta örüntüleri yakalar
(3-karakter: "dm ", 5-karakter: "bonus"). Global max pooling "metnin
herhangi bir yerinde bu örüntü var mı" sorusuna bakar — teşvik ifadesi
cümlenin neresinde olursa olsun yakalanır. Boyutlar elle seçilmedi (bkz. 4.5).

### 4.3 Aşırı öğrenmeye (overfitting) karşı alınan önlemler

1. **Bölme çoğaltmadan ÖNCE** yapılır — aynı cümlenin varyantları eğitim ve
   doğrulamaya dağılıp skoru şişiremez (sızıntı önleme).
2. **SpatialDropout1D**: embedding kanallarını topluca düşürür; küçük veri
   setinde tek karaktere ezber yapmayı kırar.
3. **L2 ağırlık cezası** (conv + dense) ve **etiket yumuşatma** (0.03):
   aşırı emin tahminleri cezalandırır.
4. **EarlyStopping** (val AUC, en iyi ağırlıklara dönüş) + **ReduceLROnPlateau**.
5. **Veri çoğaltma** yalnız eğitim bölmesine: sansür ikamesi (o→0, i→1...),
   aksansız yazım (ç→c...), boşluklu yazım — pozitife yoğun, negatife hafif
   (model "rakamlı yazım = bahis" gibi sahte bağıntı öğrenmesin diye iki
   sınıfa da uygulanır).
6. **Şeffaf ölçüm:** `egitim_raporu.json` eğitim−doğrulama farkını yazar
   (`asiri_ogrenme_farki`); %5'i aşarsa script ekranda uyarır. Nihai
   modelde %5,0 — sınırda, kabul edilebilir; bilinen ve izlenen bir durum.

### 4.4 Eşik kalibrasyonu — metodolojik dürüstlük

İlk sürümde eşik kabul setinde seçilip başarı aynı sette raporlanıyordu;
iç denetimde bunun **iyimser sapma** yarattığı tespit edildi (%91 görünen
gerçekte %87'ydi). Düzeltme: eşik artık **eğitimin doğrulama bölmesindeki**
F1 platosunun (en uzun bitişik blok) ortasından seçilir; kabul setleri bu
SABİT eşikle yalnızca rapor eder. Nihai eşik: **0.63** (plato 0.62–0.65 —
genişliği, küçük skor oynamalarına dayanıklılık demek).

### 4.5 Hiperparametre araması (Optuna) — neden ve nasıl

Embedding boyutu, filtre sayısı, dropout oranları, L2, öğrenme hızı gibi 11
ayar elle tahmin yerine **Optuna** (TPE örnekleyici + MedianPruner) ile
arandı — 40 deneme. Kritik tasarım: her deneme **3-katlı çapraz doğrulama**
ile ölçülür; tek bölmeyle aransaydı ayarlar o bölmeye "ezber" yapardı
(eşikte düzeltilen sapmanın aynısı). En iyi ayar: CV AUC 0.988
(`cikti/en_iyi_ayarlar.json`); `train.py` bu dosyayı bulunca otomatik kullanır.

### 4.6 TFLite dönüşümü ve ön işleme sözleşmesi

Keras modeli SavedModel üzerinden TFLite'a çevrilir, **dinamik aralık
kuantalama** ile küçültülür (88 KB). Tokenizasyon bilinçli olarak model
DIŞINDA tutuldu: TFLite'ın string operatör desteği zayıf; karakter→id
eşlemesi deterministik olduğundan Kotlin'de ~15 satırda birebir yazılabiliyor
(görev dosyasındaki "vocab + net kurallar" seçeneği). Python ve Kotlin'in
AYNI girdiyi üretmesi ayrı bir sözleşme belgesiyle güvenceye alındı
([spec/ON_ISLEME.md](spec/ON_ISLEME.md)): NFC normalizasyonu, Türkçe küçük
harf kuralları (İ/I), U+0307 temizliği, kodpoint (UTF-16 değil!) dolaşımı,
192'ye kes/doldur — test vektörleriyle.

## 5. Kodlarda neler var

| Script | Ne yapar |
|---|---|
| `scripts/train.py` | Veriyi yükler (sentetik + varsa gerçek), %85/15 stratified böler, eğitim bölmesini çoğaltır, modeli kurar (Optuna ayarları varsa onlarla) ve eğitir, eşiği doğrulama bölmesinde seçer, TFLite'a çevirir, sözlüğü ve raporu yazar. Deterministiktir (sabit tohum; sözlük veriden türetilmez → yeniden eğitim Kotlin tarafını bozmaz). |
| `scripts/degerlendir.py` | `model.tflite`'ı TFLite yorumlayıcısıyla iki kabul setinde SABİT eşikle koşar; doğruluk/F1/FP/FN/tuzak-FP raporlar, hatalı örnekleri listeler (veri iyileştirme döngüsünün girdisi), gecikme ölçer, `esik.json` yazar; Colab'daysa çıktıları `model_cikti.zip` olarak paketler. |
| `scripts/ayarla.py` | İsteğe bağlı Optuna araması (3-katlı CV); `en_iyi_ayarlar.json` üretir. |
| `kotlin/TfLiteDetector.kt` | Android referans implementasyonu: `Detector` arayüzünü uygular, `assets`ten model+sözlük yükler, spec'teki ön işlemeyi yapar, skor üretir, `VARSAYILAN_ESIK=0.63` ile karar verir. |

Geliştirme sürecinde yapılanların kaydı (v1→v5 deneme geçmişi, hata
analizleri, metodoloji düzeltmesi) [YOL_HARITASI.md](YOL_HARITASI.md)'dedir.

## 6. Sonuçlar ve dürüst sınırlılıklar

**Nihai model (v5 — Colab, 13 Temmuz 2026):**

| Ölçüm | Sonuç | Hedef |
|---|---|---|
| Sentetik kabul (sözleşme) | **%96** — yanlış alarm 0, tuzak FP 0 | ≥%90 + tuzak 0 ✅ |
| Gerçek saha seti | **%94,2** — 1 yanlış alarm, 6 kaçan | (bonus ölçüm) |
| Boyut / gecikme | 88 KB / 0,12 ms | ≤10 MB / ≤20 ms ✅ |

Sınırlılıklar (bilerek belgelendi):
- Kaçan gerçek pozitiflerin çoğu ÇOK KISA spam ("hesap aç 500 TL Bonus") —
  5-6 kelimelik SMS'lerde bağlam az; kelime listesi bunların bir kısmını
  zaten yakalar (VEYA mantığının değeri). Gelecek veri turu notu düşüldü.
- Tek yanlış alarm, bahis kelimeleri yoğun bir mağdur şikayeti (0.97 skor) —
  şikayet dili ile teşvik dili sınırı modelin en zor ayrımı.
- Aşırı öğrenme farkı %5,0 (sınırda): eğitim setini ezberliyor ama
  doğrulama/kabul performansı güçlü; veri büyüdükçe düşmesi beklenir.
- Eğitim verisinin yarısı sentetik; gerçek saha seti bu riski ölçüyor
  (%94,2) ama üretim kalitesi iddiası için daha geniş gerçek veri gerekir.
- Yalnız Türkçe; İngilizce teşvik kapsam dışı (kelime listesi "free spin"
  gibi terimleri karşılıyor).

## 7. Klasör haritası

| Yol | Ne |
|---|---|
| `data/egitim.jsonl` | Sentetik eğitim seti (`{"text","label"}`; 1 = teşvik) |
| `data/gercek.jsonl` | Gerçek eğitim seti (internetten, kaynak etiketli — train.py otomatik ekler) |
| `data/kabul_testi.jsonl` | 100 örneklik sentetik kabul/sözleşme seti (`tuzak` alanlı) |
| `data/kabul_gercek.jsonl` | 120 örneklik GERÇEK saha test seti (60/60, altın kaynak ağırlıklı) |
| `data/GERCEK_VERI_KAYNAKLARI.md` | Gerçek verinin kaynakları, lisanslar, KVKK önlemleri |
| `scripts/` | train.py, degerlendir.py, ayarla.py, requirements.txt |
| `spec/ON_ISLEME.md` | Ön işleme sözleşmesi (Python ↔ Kotlin) |
| `kotlin/TfLiteDetector.kt` | Ebubekir'in taşıyacağı referans implementasyon |
| `cikti/` | `model.tflite`, `model_vocab.json`, `esik.json`, raporlar, Optuna ayarları |
| `YOL_HARITASI.md` | Durum, deneme geçmişi, kalan işler, açık soruların cevap önerileri |

## 8. Çalıştırma — Google Colab (önerilen)

`model_colab.zip`'i Colab'a yükleyin, sonra:

```python
# Eski koşudan kalan klasörü temizle + sorusuz aç (soru çıkarsa ASLA 'n' demeyin:
# 'n' eski dosyaları bırakır ve farkında olmadan eski sürümü çalıştırırsınız)
!rm -rf /content/model
!unzip -q -o /content/model_colab.zip -d /content

# İSTEĞE BAĞLI: hiperparametre araması (40 deneme × 3-katlı CV, A100'de ~30-40 dk)
!pip -q install optuna
!python /content/model/scripts/ayarla.py

!python /content/model/scripts/train.py          # cikti/model.tflite + model_vocab.json
!python /content/model/scripts/degerlendir.py    # kabul testleri + cikti/esik.json
```

Son adım — çıktıları indirme (AYRI bir hücrede, `!` olmadan çalıştırın;
`files.download` yalnızca not defteri hücresinden çalışır):

```python
from google.colab import files
files.download("/content/model/model_cikti.zip")
```

İnen `model_cikti.zip`'i `Bağimlilik_TEKNOFEST` klasörüne koyun. Yerel/PC
koşusunda paketleme-indirme adımı kendiliğinden atlanır.

Model küçüktür: CPU'da 2-3 dk, GPU yalnız `ayarla.py` için anlamlı fark
yaratır. GPU'da metrikler binde birlik oynayabilir — bağlayıcı sonuç her
zaman `degerlendir.py` çıktısıdır. Aşırı öğrenme takibi:
`egitim_raporu.json` → `asiri_ogrenme_farki` %5'i aşarsa `ayarla.py` koşun.

## 9. Çalıştırma (Windows, yerel)

```
py -3.12 -m pip install -r model/scripts/requirements.txt
py -3.12 model/scripts/train.py
py -3.12 model/scripts/degerlendir.py
```

TensorFlow, Python 3.13+/3.14 için paket sunmuyor; yerelde 3.12 gerekir.
