# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Bu depoda çalışırken her oturumun başında şu dosyaları oku ve talimatlarına uy:

- **ProjeAkışı.md** — mimari kararlar, teknik bilgiler, derleme/test komutları ve kod yapısı. Bu depodaki asıl çalışma talimatları orada.
- **PROJE.md** — ekip, görev sahipleri, ekip genelinde geçerli kurallar ve takvim.
- **görevler/** — kişi başına görev tanımları; **MODEL_ENTEGRASYON.md** ve **SANDBOX_GEREKSINIMLER.md** — diğer bileşenlerle sözleşmeler.

Dosyalara bakmadan önce bilinmesi gereken iki kesin kural:

1. **KVKK:** Hiçbir kullanıcı verisi kaydedilmez, hiçbir ağ isteği atılmaz, `INTERNET` izni eklenmez. Ekran metinleri loglanmaz (yalnızca debug derlemede, geçici olarak izin verilir).
2. **Tespit mantığı her zaman `Detector` arayüzünün arkasında kalır** (`detection/` paketi); kelime listesinin tek kaynağı `app/src/main/assets/keywords.json`.
