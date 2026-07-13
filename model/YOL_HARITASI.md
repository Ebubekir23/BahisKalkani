# Tespit Modeli — Yol Haritası ve Devir Belgesi

Son güncelleme: 13 Temmuz 2026. Bu belge iki iş görür: (1) modelin güncel
durumu ve kalan işlerin sahipli listesi, (2) bu çalışmayı devralacak kişi
ya da yapay zekâ oturumu için işleyiş talimatı. Teslim sözleşmesinin kendisi
[görevler/halil-tespit-modeli.md](../görevler/halil-tespit-modeli.md).

## Durum özeti

| Teslimat | Durum |
|---|---|
| 1. `model.tflite` (≤10 MB) | ✅ **NİHAİ** — Colab'da Halil eğitti (13 Tem): 88 KB, sentetik kabul %96, gerçek saha %94.2; artefaktın yereldeki doğrulaması birebir tuttu |
| 2. Ön işleme speki | ✅ [spec/ON_ISLEME.md](spec/ON_ISLEME.md) + iki dilde referans kod |
| 3. Eşik önerisi + kalibrasyon | ✅ **0.63** (doğrulama bölmesi platosu 0.62–0.65) — `cikti/esik.json`; Kotlin sabiti eşitlendi |
| 4. ~100 örnek kabul seti | ✅ `data/kabul_testi.jsonl` (çok ajanlı üretim + çekişmeli denetim) |
| + Gerçek veri (13 Tem, Halil kararı) | ✅ `data/gercek.jsonl` 1.375 eğitim + `data/kabul_gercek.jsonl` 120 saha testi — kaynak/lisans: [data/GERCEK_VERI_KAYNAKLARI.md](data/GERCEK_VERI_KAYNAKLARI.md) |

### Deneme geçmişi (12-13 Temmuz, yerel doğrulama koşuları)

| Koşu | Kabul doğruluğu | FP | FN | Eşik | Not |
|---|---|---|---|---|---|
| v1 | %91* | 1 | 8 | 0.82* | *eşik kabul setinde seçilmişti — iyimser sapmalı, yöntem düzeltildi |
| v2 | %90* | 6 | 4 | 0.14* | negatif ascii çoğaltması abartıldı, geri alındı |
| v3 (1064 örnek, sabit eşik) | %87 | 5 | 8 | 0.38 | dürüst ölçüm; hata analizi 3 veri açığı gösterdi |
| v4 (1543 örnek, sabit eşik) | %96 | 4 | 0 | 0.32 | hedefli 479 ek örnek sonrası — hedef karşılandı |
| **v5 — NİHAİ (Colab, 2918 örnek: sentetik+gerçek, Optuna 40 deneme)** | **%96** (FP 0, FN 4) | | | **0.63** | **GERÇEK saha seti: %94.2** (FP 1, FN 6); tuzak FP 0; 88 KB; 0.12 ms; eşik platosu 0.62–0.65 (sağlıklı); aşırı öğrenme farkı %5.0 (sınırda, kabul edilebilir — eğitim acc 1.0, val acc 0.95) |

Eşik artık eğitimin doğrulama bölmesinde seçiliyor (kabulden bağımsız).
v4'te kaçan pozitif yok; kalan 4 yanlış alarm coşkulu günlük dil sınır
örnekleri. Tanı taraması kabul üstünde 0.91–0.95 aralığının %97 verdiğini
gösteriyor — demo günü yanlış alarm öncelikliyse eşik oraya çekilebilir
(kaçan pozitif riski karşılığında; karar sandbox verisiyle ikinci
kalibrasyon turunda). `cikti/` v4 koşusunun çıktısını içeriyor; nihai
eğitim Colab'da aynı veriyle tekrarlanacak (deterministik, aynı sonucu
vermesi beklenir; GPU'da binde birlik oynama olabilir).

### Aşırı öğrenme önlemleri + hiperparametre araması (13 Tem, Halil isteği)

`train.py`'ye SpatialDropout1D, L2 cezası, etiket yumuşatma ve
ReduceLROnPlateau eklendi; rapor artık eğitim/doğrulama farkını yazıyor
(`asiri_ogrenme_farki` > ~%5 ise ezber uyarısı). `ayarla.py` (Optuna, isteğe
bağlı) 3-katlı çapraz doğrulamayla arama yapar — tek bölmeye ayar ezberletmemek
için; çıktısını train.py otomatik kullanır. Colab'da `degerlendir.py` sonunda
tüm çıktılar `model_cikti.zip` olarak otomatik indirilir.

## İşleyiş — bu çalışma nasıl yürüyor

1. **Veri** `data/egitim.jsonl`'de durur. Üretim yöntemi: kategori başına
   bağımsız üretici (7 pozitif + 7 negatif kategori + sınır örnekleri),
   her parti ayrı bir denetçi tarafından etiket/gerçekçilik süzgecinden
   geçirildi, kabul setiyle çakışan eğitim örnekleri atıldı.
2. **Eğitim** deterministiktir (sabit tohum, sabit sözlük): `train.py`
   her çalıştığında aynı veriden aynı modeli üretir. Sözlük veriden
   TÜRETİLMEZ — yeniden eğitim Kotlin tarafını bozmaz.
3. **Kalibrasyon:** eşik `train.py` içinde, eğitimin doğrulama bölmesindeki
   F1 platosunun (en uzun bitişik blok) ortasından seçilir — kabul setinde
   SEÇİLMEZ; aynı sette hem eşik seçmek hem başarı raporlamak iyimser sapma
   yaratır (13 Temmuz iç denetim bulgusu üzerine düzeltildi).
4. **Kabul ölçütü** (sözleşme): `degerlendir.py` kabul setini SABİT eşikle
   koşar; ≥ %90 doğruluk VE tuzak negatiflerde 0 yanlış pozitif hedefini
   son satırda EVET/HAYIR olarak basar. Kabul üstünde tarama yalnızca tanı
   amaçlı yazdırılır.
5. Her anlamlı adım küçük commit olarak `main`'e gider (önce `git pull`).

## Yapılacaklar — öncelik sırasıyla

### Bu oturumun devamı / devralan model için (Halil tarafı)

- [x] ~~V1: Eğitimi çalıştır ve sonucu buraya işle~~ — v3/v4 koşuları yapıldı
      (yukarıdaki tablo).
- [x] ~~V2: hata analizi döngüsü~~ — v3 hata analizi 3 açık gösterdi
      (aksansız sade teşvik, oyun/başarım dili, coşkulu günlük dil); 479
      hedefli örnek eklendi → v4 %96. Aynı döngü gerekirse tarif: `cikti/
      esik.json` → `hatalar` → zayıf kategoride 50-100 yeni örnek → eğit.
- [x] ~~Colab'da nihai eğitim (Halil)~~ — 13 Tem yapıldı: Optuna (40 deneme,
      CV AUC 0.988) + eğitim + iki kabul seti. Sonuçlar üstteki v5 satırında;
      çıktılar `cikti/`de, yerel doğrulama birebir tuttu.
- [ ] **V3 (gerekirse): eşik/duyarlılık dengesi** — tuzak FP=0 kısıtı
      bozulursa tuzak örneklerini incele: etiketi tartışmalı olan varsa kabul
      setinde düzeltme yapılabilir ama SEBEBİNİ commit mesajına yaz
      (kabul seti sözleşmedir, sessiz değiştirilmez).
- [ ] **Gecikme ölçümü telefonda** — PC ölçümü yalnızca gösterge;
      Ebubekir'in cihazında `TfLiteDetector.score()` için ölçüm alın
      (hedef ≤ 20 ms/metin, bütçe 10 metinde ~200 ms).
- [ ] **Sandbox verisiyle çapraz doğrulama** — Ezgi'nin `posts.json`'u
      çıkınca modeli o gönderiler üstünde çalıştır (yeni `degerlendir.py`
      girdisi olarak), demo gününde sürpriz yaşanmasın.

### Ebubekir'e devredilen (entegrasyon) — 13 Temmuz'da TAMAMLANDI

- [x] `cikti/model.tflite` + `cikti/model_vocab.json` → `app/src/main/assets/`
- [x] `kotlin/TfLiteDetector.kt` → `app/.../detection/`
- [x] Bağımlılık — NOT: `org.tensorflow:tensorflow-lite:2.14.0` AGP 9'da
      derlenmiyor (alt modülleri aynı namespace'i paylaşıyor, yeni AGP
      reddediyor). Yerine yeni nesil paket kullanıldı:
      `com.google.ai.edge.litert:litert:1.2.0` — API ve importlar birebir
      aynı (`org.tensorflow.lite.*`), kod değişikliği gerekmedi.
- [x] `ScreenReaderService`'te birleşik tespitçi:
      `Detector { t -> keyword.isBettingContent(t) || model.isBettingContent(t) }`
- [x] `TfLiteDetectorTest` — cihazda duman testi (`androidTest`): 2 pozitif,
      3 negatif (tuzak dahil), gecikme bütçesi; kapsamlı doğruluk ölçümü
      `degerlendir.py` ile PC'de.
- [ ] Eşik güncellemesi (sürekli kural): `esik.json` her değiştiğinde
      `TfLiteDetector.VARSAYILAN_ESIK` sabitini eşitle.
- [ ] Telefonda gerçek gecikme ölçümü + uçtan uca test (Ebubekir):
      `gradlew.bat connectedDebugAndroidTest`

## Açık soruların cevap önerileri (Ebubekir'le kapatılacak)

1. **Tokenizasyon içeride mi dışarıda mı?** → Dışarıda ama ~15 satır ve
   deterministik (gerekçe: [spec/ON_ISLEME.md](spec/ON_ISLEME.md), "tasarım
   kararları"). Vocab dosyası + iki dilde referans kod teslimatta var.
2. **Maks girdi uzunluğu?** → 192 kodpoint, baştan kes. Ekran öğesi metni
   tipik ≤ 200 karakter; kayan pencere ancak tam-sayfa metin gelirse gerekir
   (önerisi spec'te, şimdilik uygulanmasın).
3. **Hangi TFLite çalışma zamanı?** → `org.tensorflow:tensorflow-lite:2.14.0`
   ile başla (yaygın, belgesi bol, API'si referans kodla birebir). Google'ın
   yeni adı LiteRT (`com.google.ai.edge.litert`) — ileride geçiş tek import
   değişikliği. Bağımlılık model teslimiyle birlikte eklenecek (Ebubekir).
4. **Eşik hangi veriyle kalibre edilir?** → Eğitimin doğrulama bölmesinde
   seçilir (kabul seti yalnızca sabit eşikle rapor eder — iyimser sapma
   önlemi). İkinci tur: Ezgi'nin sandbox `posts.json`'u çıkınca demo
   önceliğine göre (yanlış alarm ↔ kaçan pozitif dengesi) birlikte
   ayarlanır; tanı taramasına göre 0.32–0.95 arası oynama alanı var.

## Riskler / bilinçli sınırlar

- Eğitim verisi sentetik (elle + üretken çeşitleme, görev dosyasının
  önerdiği yol). Gerçek sosyal medya diliyle örtüşme kabul seti +
  sandbox çapraz doğrulamasıyla sınanıyor; demo kapsamı için yeterli,
  ürünleşmede gerçek veri toplama (KVKK uyumlu) gerekir.
- Model yalnız Türkçe; İngilizce bahis içeriği kapsam dışı (kelime listesi
  "free spin", "freebet" gibi terimleri zaten yakalıyor).
- `casino` kelimesi Türkçe küçük harf kuralıyla `casıno` olur (I→ı) —
  eğitim ve çalışma anı aynı dönüşümü yaptığı için sorun değil; spec'te
  test vektörü olarak duruyor.
