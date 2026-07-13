# Gerçek Veri Kaynakları ve Lisans Notları

`gercek.jsonl` (1.375 eğitim örneği) ve `kabul_gercek.jsonl` (120 saha test
örneği) 13 Temmuz 2026'da halka açık kaynaklardan toplandı. Her satırın
`kaynak`/`kategori` alanı kökenini taşır. Toplama → temizlik → bağımsız
etiket denetimi (26 denetçi; 1.531 adaydan 36'sı tartışmalı/bozuk diye
atıldı, 2 etiket düzeltildi) → eğitim/kabul bölmesi (kabul, eğitimden ve
sentetik setlerden ayrık).

## Kaynaklar

| Kaynak | Tür | Lisans / durum |
|---|---|---|
| HuggingFace `allenai/c4` (tr) | Bahis sitesi tanıtım/SEO cümleleri (poz) + haber/uyarı/spam-dışı (neg) | ODC-BY 1.0 (atıf şartlı) |
| HF `winvoker/turkish-sentiment-analysis-dataset` | Normal Türkçe kısa metin (neg) | CC-BY-SA-4.0 — veri seti YAYIMLANIRSA aynı lisans şartı |
| HF `FredZhang7/all-scam-spam` | Türkçe bahis-dışı spam (neg) | Apache-2.0 |
| HF `eskfestsecurity/turkish-igaming-spam-detection` | 6 örnek | CC-BY-4.0 (küçük ve elle derlenmiş görünümlü — temkinli) |
| Telegram kanal web önizlemeleri (`t.me/s/…`, 18 kanal) | Gerçek teşvik gönderileri (poz) | Resmi lisans yok; halka açık ticari spam. **Proje içi kullanım — ham haliyle yeniden yayımlamayın** |
| sikayetvar.com (~920 sayfa tarandı) + ekşi sözlük + technopat | Alıntılanan gerçek spam SMS'ler (poz) + bahis kelimeli teşviksiz şikayet cümleleri (neg) | Aynı şekilde proje içi kullanım |
| Haber RSS'leri (NTV, TRT, Sözcü vb.) | Başlıklar: genel + spor + "yasa dışı bahis operasyonu" (neg) | Başlık düzeyinde alıntı |
| Kampanya/oyun sayfaları | Meşru "kazan/bonus/fırsat" dili (neg) | Metin parçası düzeyinde |

**Lisansı belirsiz olduğu için KULLANILMAYANLAR:** akuysal/turkishSMS-ds,
anilguven/turkish_spam_email, Kaggle Türkçe SMS aynaları, batubayk/TR-News,
GPL'li çeviri SMS seti, vngrs-web-corpus (NC kısıtı), M-Arjun/SpamShield
(kapalı erişim). İleride kullanılacaksa yazarlardan izin istenmeli.

## KVKK / gizlilik önlemleri

- Telefon numaraları biçim korunarak sahteleştirildi (`0500 000 00 00`),
  IBAN'lar `TR00 …` yapıldı (toplayıcıda + temizlik regex'i + denetçi,
  üç katman).
- Sıradan kişilerin ad-soyadları alınmadı/`[AD]` yapıldı; şikayetçi
  kimlikleri hiç toplanmadı.
- Kanal ve bahis sitesi adları kamuya açık ticari spam kimliği olarak
  korundu (tespit sinyali).
- Yalnızca üyeliksiz, halka açık sayfalar kullanıldı; hesap açılmadı,
  hiçbir bot koruması aşılmadı.

## Bilinen sınırlılıklar (dürüst not)

- `p-web` pozitifleri (C4 kaynaklı, 364 adet) web sitesi düzyazısı —
  sosyal medya üslubundan farklı; mesaj-üslubu gerçek örnekler (Telegram
  182 + şikayet 42) bunu dengeliyor ve gerçek kabul setinde altın
  kaynaklara ağırlık verildi (60 pozitifin 50'si Telegram+şikayet).
- Telegram önizlemeleri özetleyici bir katmandan geçtiği için tek tük
  gönderi kırpılmış olabilir; denetçiler anlamsız kalanları attı.
- Şablonlaşmış spam (aynı kalıp farklı miktar) rakam-bağımsız anahtarla
  teklendi; yine de Telegram/SMS dilinde doğal tekrarlılık vardır.
