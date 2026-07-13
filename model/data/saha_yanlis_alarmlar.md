# Saha Yanlış Alarmları — yeniden eğitim adayları

13 Temmuz, cihaz testi (Ebubekir). Uygulama eşiği **0.92** iken modelin
yanlış alarm verdiği gerçek ekran metinleri. Hata-analizi döngüsünün girdisi
(YOL_HARITASI "V3" maddesi): bu kalıplarda 50-100 hedefli negatif üretilip
v6 eğitimi yapılmalı.

## Kesin yanlış alarmlar (label=0 adayı)

| Metin | Kalıp |
|---|---|
| Hürriyet https://www.hurriyet.com.tr 76 milyar 284 milyon işlem hacmi! 68 şüpheli adliyeye sevk edildi | haber başlığı + URL + para/rakam yoğunluğu |
| Hürriyet https://www.hurriyet.com.tr Son Dakika Yasa Dışı Bahis Hakkında Güncel Haber ve Bilgiler | haber listeleme sayfası başlığı + URL |
| 780+ beğenme · 2 hafta önce | sosyal medya meta verisi (sayı + zaman) |
| Sadece kayıtlı üyeler yorum yapabilir. Bir kaç saniye içerisinde kayıt olabilirsiniz. | forum üyelik kalıbı — "kayıt ol" davetine benziyor ama bahis değil |

## Sınırda (etiket kararı Halil'in)

| Metin | Not |
|---|---|
| Kanal linkini dm atsana | Telegram davet kalıbı — bahis bağlamında gerçek sinyal, bağlamsız yorumda masum |
| Kanal linkini bana dm atarsın | aynı |

## Uygulama tarafında bu arada yapılanlar (mükerrer iş olmasın)

- Eşik 0.63 → 0.92 (tanı taramasındaki bant)
- 15 karakterden kısa metinler modele sorulmuyor
- contentDescription taranmıyor (yalnızca görünen metin)

Yani v6'nın hedefi yukarıdaki uzun-metin kalıpları; kısa metin ve ikon
kaynaklı alarmlar uygulama tarafında çözüldü.
