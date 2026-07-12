# Ezgi Efsa GÜLEÇ — Demo Sandbox

## Görev

Instagram benzeri sahte sosyal medya uygulaması (ayrı repo). Final günü jüri
demosu bunun üzerinde yapılacak: aynı telefonda sandbox + kalkan kurulu
olacak, jüri feed'i kaydırdıkça kalkan bahis gönderilerini canlı yakalayıp
kapatacak. **Demo puanının sahnesi bu uygulama** — akıcılık ve gerçekçi
görünüm önemli.

## Teslim edilecekler

1. Kotlin + Jetpack Compose uygulaması; `LazyColumn` ile kaydırılabilir feed
2. Gönderiler yerel JSON dosyasından (kullanıcı adı, avatar/renk, metin,
   opsiyonel görsel); tamamen offline, INTERNET izni yok
3. Instagram hissi veren gönderi kartı: üstte kullanıcı, ortada içerik,
   altta beğeni/yorum simgeleri (çalışması şart değil, görünmesi yeter)

## Kalkan uyumu (kritik — ayrıntı: [SANDBOX_GEREKSINIMLER.md](../SANDBOX_GEREKSINIMLER.md))

- Gönderi metinleri normal `Text` composable ile — resme/Canvas'a gömme
- Gönderinin tamamının kapanması için kart köküne
  `Modifier.semantics(mergeDescendants = true) {}` (ilk ortak testte birlikte
  ayarlarız)
- Uygulama adında ve sabit arayüz metinlerinde bahis kelimesi geçmesin
  (gönderi içeriklerinde geçmesi zaten amaç)
- WebView yok

## Demo verisi

- Bahis gönderilerini bu repodaki `app/src/main/assets/keywords.json`
  listesinden besle
- Karışım: ~%30 bahis (düz + sansürlü yazım + kupon/Telegram dili),
  ~%70 masum; araya "Betül", "alfabetik" gibi tuzak kelimeli masum
  gönderiler koy (yanlış pozitif olmadığını göstermek için)
- 30-40 gönderi yeterli; JSON'u elle yazmak sıkıcıysa Ebubekir'den yardım iste

## Nasıl (önerilen sıra)

1. Boş Compose projesi (Android Studio şablonu), minSdk 26
2. `Post` data class + `assets/posts.json` + okuma katmanı (org.json yeterli)
3. `LazyColumn` + gönderi kartı composable'ı
4. Görünüm cilası en sona — önce kaydırılabilir 10 gönderilik sürüm çıkar,
   Ebubekir'in cihazında kalkanla ortak test yapın (24 Temmuz'u bekleme)

## Takvim

- İlk kaydırılabilir sürüm: en kısa sürede (ortak test için)
- 4-5 Ağustos: rapor ekran kayıtları bu uygulama + kalkan ikilisiyle çekilecek
- 30 Eylül: final demosu (offline, Şanlıurfa)
