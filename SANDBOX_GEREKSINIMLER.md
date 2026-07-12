# Sandbox Uygulaması Gereksinimleri (Kalkan Uyumu)

Hedef okuyucu: Yazılımcı 3. Final demosu aynı telefonda sandbox + kalkan
kuruluyken yapılacak: jüri feed'i kaydırdıkça kalkan bahis gönderilerini canlı
yakalayıp kapatacak. Bu belge, kalkanın sandbox'ta kusursuz çalışması için
sandbox'ın uyması gereken kuralları listeler.

## Temel çerçeve (PROJE.md'den)

Kotlin + Jetpack Compose, `LazyColumn` feed, gönderiler yerel JSON'dan,
tamamen offline (INTERNET izni yok). Instagram benzeri görünüm.

## Kalkanın çalışması için kritik kurallar

1. **Metinler erişilebilirlik ağacında olmalı.** Gönderi metinlerini normal
   `Text` composable ile çiz. Metni resmin/Canvas'ın içine gömme — kalkan
   yalnızca erişilebilirlik ağacındaki metni görür, resim içindeki yazıyı
   göremez.
2. **Gönderinin tamamının kapanmasını istiyorsak:** gönderi kartının kök
   composable'ına `Modifier.semantics(mergeDescendants = true) {}` ekle.
   Böylece kartın tüm metni tek düğümde birleşir ve kalkan kartın tamamını
   kapatır. Eklenmezse yalnızca eşleşen `Text` satırı kapanır — hangisinin
   demoda daha iyi göründüğüne ilk ortak testte birlikte karar verelim.
3. **Kart boyutu:** kapakta uyarı + "yine de göster" butonunun görünmesi için
   bölge en az ~320 px genişlik ve ~220 px yükseklik olmalı. Feed kartları
   doğal olarak bunun üstündedir, sorun çıkmaz; çok küçük öğelerde yalnızca
   düz kapak çizilir.
4. **WebView kullanma.** Native Compose kal.
5. **Uygulama adında ve sabit arayüz metinlerinde bahis kelimeleri geçmesin**
   (ör. uygulamaya "BahisFeed" deme, sekmeye "Bahisler" yazma) — kalkan
   onları da kapatır. Gönderi İÇERİKLERİNDE geçmesi zaten işin amacı.
6. Yorum yazma kutusu gibi yazı alanları güvenli — kalkan `isEditable`
   alanları bilinçli olarak kapatmıyor.

## Demo verisi (gönderi JSON'u)

- Bahis gönderileri kalkanın kelime listesiyle eşleşmeli. Tek kaynak bu
  repodaki `app/src/main/assets/keywords.json` — gönderileri yazarken bu
  listeden beslen.
- Çeşitlilik olsun:
  - düz yazım: "deneme bonusu", "canlı bahis", "çevrimsiz bonus"
  - sansürlü yazım: "b0nus", "ç3vrim", "b4his" (kalkan bunları da yakalıyor)
  - kupon paylaşımı ve Telegram davet dili
- Masum gönderiler de olsun; araya "Betül", "alfabetik" gibi tuzak kelimeli
  masum gönderiler serpiştir — jüriye yanlış pozitif üretmediğimizi gösterir.
- Karışım önerisi: ~%30 bahis, ~%70 masum; jüri kaydırdıkça düzenli
  aralıklarla yakalama görünsün.

## Entegrasyon testi

- Kalkan bu repodan derleniyor: `gradlew.bat assembleDebug`
- Sandbox'ın ilk kaydırılabilir sürümü çıkar çıkmaz aynı cihazda ortak test
  yapalım — 24 Temmuz'u bekleme, feed + 10 gönderi yeterli.
- 4-5 Ağustos'ta rapor ekran kayıtları bu ikili üzerinden çekilecek; o tarihte
  akıcı çalışıyor olmalı.
