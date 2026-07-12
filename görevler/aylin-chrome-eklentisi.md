# Aylin AKAGÜNDÜZ — Chrome Eklentisi

## Görev

Android Kalkan'ın tarayıcı versiyonu: sayfadaki bahis-teşvik metinlerini
tespit edip kapatan bir Chrome eklentisi (Manifest V3). Ayrı repoda
geliştirilecek; tespit mantığı ve kelime listesi Android tarafıyla eşdeğer
tutulacak.

## Teslim edilecekler

1. **Manifest V3 eklentisi**: `content_script` her sayfada çalışır, metin
   düğümlerini tarar, eşleşen öğenin üstünü kapatır
2. **Sayaç popup'ı**: eklenti simgesine tıklayınca "bu oturumda N içerik
   engellendi" gösterir (Android'deki ana ekran sayacının karşılığı)
3. **"Yine de göster"**: kapatılan öğe üzerinde buton; tıklanınca o içerik
   oturum boyunca açık kalır

## Android tarafıyla eşdeğerlik (kritik)

Bu repodaki `app/src/main/assets/keywords.json` **tek kaynak** — dosyayı
eklentiye aynen kopyala, format şu:

- `keywords`: eşleşme "içeriyor mu" mantığıyla, Türkçe küçük harfe çevirerek
  (`toLocaleLowerCase('tr')`) yapılır — "bahisleri", "1xbahis" gibi türevler
  de yakalanır
- `ignored`: eşleşmeden ÖNCE metinden çıkarılır ("bahiskalkanı" gibi — ürünün
  kendi adı tespiti tetiklememeli)
- Sansür normalizasyonu eşleşmeden önce uygulanır: 0→o, 1→i, 3→e, 4→a, 5→s,
  7→t, @→a, $→s ("b0nus" → "bonus")

Listeyi kim güncellerse diğer tarafa iletir (şimdilik elle senkron).

## Nasıl (önerilen yol)

1. Boş MV3 iskeleti: `manifest.json` + content script + popup
2. Tespit fonksiyonunu ayrı bir `detector.js` dosyasına koy (Android'deki
   `Detector` arayüzünün karşılığı — Faz 2'de buraya da model bağlanabilir)
3. Sayfa metnini `TreeWalker` ile gez; eşleşen metin düğümünün en yakın
   blok öğesini kapat (örtü `div` + uyarı + "yine de göster")
4. Dinamik içerik için `MutationObserver` kur (sonsuz kaydırmalı siteler)
5. Sayaç: content script → `chrome.runtime.sendMessage` → popup okur;
   yalnızca SAYI tut, metin saklama

## Değişmez kurallar (KVKK)

- Hiçbir kullanıcı verisi kaydedilmez; okunan sayfa metni saklanmaz, loglanmaz
- Hiçbir ağ isteği atılmaz: fetch/XHR yok, analytics yok, uzak sunucudan liste
  çekme yok — kelime listesi eklenti paketinin içinde gelir
- İzinleri dar tut: `host_permissions` gerekli minimumda, gereksiz `storage`
  vb. ekleme (rapor ve mağaza incelemesi için de önemli)

## Takvim

- 24 Temmuz: temel tespit + kapatma çalışıyor (popup basit olabilir)
- 4-5 Ağustos: rapor ekran görüntüleri (eklenti bahisli bir sayfada engelleme
  yaparken + sayaç popup'ı)
