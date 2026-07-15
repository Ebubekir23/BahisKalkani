# -*- coding: utf-8 -*-
"""Kabul testleri + dilim raporu + INV (değişmezlik) testleri + gecikme.

Girdi:  cikti/model.tflite, cikti/model_vocab.json, cikti/egitim_raporu.json
        data/kabul_testi.jsonl   (sentetik sözleşme seti — görev teslimatı ④)
        data/kabul_gercek.jsonl  (gerçek saha seti — varsa)
        data/kabul_saha.jsonl    (saha regresyon seti: cihazda görülen gerçek
                                  yanlış alarmlar + benzerleri — varsa)
Çıktı:  cikti/esik.json

Çalıştırma: python model/scripts/degerlendir.py

SÜRÜM KAPISI (hepsi sağlanmalı → "hedef karşılandı: EVET"):
  1. Sözleşme seti: doğruluk ≥ %90 VE tuzak negatiflerde 0 yanlış alarm
  2. Saha regresyon seti (varsa): 0 yanlış alarm — cihazda görülmüş hataların
     tekrarı sürümü düşürür (üretim-hatası→test-vakası→kapı deseni)
  3. INV-URL testi: negatife meşru-görünümlü URL eklemek alarm ÜRETMEMELİ

Eşik train.py'de kalibrasyon setinden seçilir; burada yalnızca SABİT eşikle
rapor edilir (aynı sette seçim+rapor iyimser sapma yaratır).
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

MODEL_DIR = Path(__file__).resolve().parent.parent
CIKTI = MODEL_DIR / "cikti"
DATA = MODEL_DIR / "data"

sys.path.insert(0, str(Path(__file__).parent))
from train import MAX_LEN, preprocess  # noqa: E402  (ön işleme tek kaynak)
from kelime import keyword_isbetting  # noqa: E402  (üretim: kesin-kelime VEYA model)

SETLER = [
    ("kabul_testi.jsonl", "Sözleşme (sentetik)"),
    ("kabul_gercek.jsonl", "Gerçek saha"),
    ("kabul_saha.jsonl", "Saha regresyonu (cihaz hataları)"),
]

# INV testinde negatiflere eklenen, allowlist DIŞI meşru-görünümlü adresler:
# eklenince skor eşiği AŞMAMALI (model URL varlığından alarm üretmemeli)
INV_URLLER = ["https://ornek-gunluk-blog.net", "www.yemektarifleri-ornek.com"]


def load_interpreter():
    import tensorflow as tf

    interp = tf.lite.Interpreter(model_path=str(CIKTI / "model.tflite"))
    interp.resize_tensor_input(interp.get_input_details()[0]["index"], [1, MAX_LEN])
    interp.allocate_tensors()
    return interp


def score_all(interp, texts: list[str]) -> np.ndarray:
    inp = interp.get_input_details()[0]
    out = interp.get_output_details()[0]
    scores = np.empty(len(texts), dtype=np.float32)
    for i, t in enumerate(texts):
        x = np.array([preprocess(t)], dtype=inp["dtype"])
        interp.set_tensor(inp["index"], x)
        interp.invoke()
        scores[i] = interp.get_tensor(out["index"])[0][0]
    return scores


def metrikler(pred, y, tuzak) -> dict:
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    return {
        "dogruluk": float((pred == y).mean()),
        "f1": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
        "yanlis_pozitif": fp,
        "yanlis_negatif": fn,
        "tuzak_fp": int((pred & tuzak).sum()),
    }


def seti_kos(interp, dosya: Path, esik: float, ad: str):
    """Bir seti ÜRETİM SİSTEMİYLE (kesin-kelime VEYA model) koşar; genel +
    dilim (kategori) raporu üretir. Ölçüm, sahada çalışan bileşimi yansıtır."""
    rows = [json.loads(l) for l in dosya.read_text(encoding="utf-8").splitlines() if l.strip()]
    texts = [r["text"] for r in rows]
    y = np.array([r["label"] for r in rows])
    tuzak = np.array([bool(r.get("tuzak")) for r in rows])
    scores = score_all(interp, texts)
    kw = np.array([keyword_isbetting(t) for t in texts])
    pred = kw | (scores >= esik)          # ← üretim kararı

    m = metrikler(pred, y, tuzak)
    kw_katki = int((kw & (y == 1)).sum())
    print(f"\n=== {ad}: {len(rows)} örnek ({int(y.sum())} poz, {int(tuzak.sum())} tuzak)")
    print(f"  Sistem @ {esik} (kesin-kelime VEYA model): doğruluk {m['dogruluk']:.1%}, "
          f"F1 {m['f1']:.3f}, FP {m['yanlis_pozitif']}, FN {m['yanlis_negatif']}, "
          f"tuzak FP {m['tuzak_fp']}  (kelime katkısı: {kw_katki} poz)")

    # --- dilim raporu (SİSTEM kararıyla): toplam doğruluk yüksekken kritik
    # kalıpta çuvallamayı görünür kılar (Snorkel slicing deseni)
    dilimler = defaultdict(lambda: {"n": 0, "hata": 0, "fp": 0})
    for r, p in zip(rows, pred):
        d = dilimler[r.get("kategori", r.get("kaynak", "?"))]
        d["n"] += 1
        if bool(p) != bool(r["label"]):
            d["hata"] += 1
            if r["label"] == 0:
                d["fp"] += 1
    dilim_raporu = {}
    for ad_d, d in sorted(dilimler.items()):
        dilim_raporu[ad_d] = {"n": d["n"], "hata": d["hata"], "fp": d["fp"]}
        isaret = " ←" if d["hata"] else ""
        print(f"    dilim {ad_d:<24} n={d['n']:<4} hata={d['hata']} (FP {d['fp']}){isaret}")

    hatalar = [
        {"text": r["text"], "label": r["label"],
         "kategori": r.get("kategori", r.get("kaynak", "?")),
         "skor": round(float(s), 3)}
        for r, s, p in zip(rows, scores, pred) if bool(p) != bool(r["label"])
    ]
    for h in hatalar:
        print(f"    HATA [{h['kategori']}] skor={h['skor']} label={h['label']}: {h['text'][:76]}")
    return m, dilim_raporu, hatalar, rows, scores


def inv_url_testi(interp, rows, scores, esik: float) -> dict:
    """Değişmezlik (CheckList INV) testi: negatife meşru-görünümlü URL ekle →
    alarm üretmemeli; URL'li pozitiften URL'ler çıkarılınca dil sinyali
    yeterliyse alarm sürmeli (bilgi amaçlı)."""
    from train import URL_RE

    neg = [(r, s) for r, s in zip(rows, scores) if r["label"] == 0 and s < esik]
    ihlal, denenen = 0, 0
    for (r, s0), url in [(pair, INV_URLLER[i % 2]) for i, pair in enumerate(neg)]:
        if len(r["text"]) > 160:
            continue
        denenen += 1
        s1 = float(score_all(interp, [f"{r['text']} {url}"])[0])
        if s1 >= esik:
            ihlal += 1
            if ihlal <= 5:
                print(f"    İHLAL (URL ekleyince alarm): {s0:.2f}→{s1:.2f}  {r['text'][:60]}")
    poz_url = [r for r in rows if r["label"] == 1 and URL_RE.search(r["text"])]
    dil_kacan = 0
    for r in poz_url:
        temiz = " ".join(URL_RE.sub(" ", r["text"]).split())
        if len(temiz) >= 5 and float(score_all(interp, [temiz])[0]) < esik:
            dil_kacan += 1
    print(f"  INV-URL: {denenen} negatife URL eklendi → {ihlal} ihlal"
          f" | {len(poz_url)} URL'li pozitiften URL çıkınca {dil_kacan} kaçtı (bilgi)")
    return {"denenen": denenen, "ihlal": ihlal,
            "urlsuz_pozitif_kacan": dil_kacan, "urlli_pozitif": len(poz_url)}


def main() -> None:
    rapor = json.loads((CIKTI / "egitim_raporu.json").read_text(encoding="utf-8"))
    esik = rapor["onerilen_esik"]
    print(f"Sabit eşik: {esik}  (kaynak: {rapor.get('esik_kaynagi', '?')})")

    interp = load_interpreter()
    sonuc, kapi = {}, {}

    ana_rows, ana_scores = None, None
    for dosya, ad in SETLER:
        yol = DATA / dosya
        if not yol.exists():
            continue
        m, dilimler, hatalar, rows, scores = seti_kos(interp, yol, esik, ad)
        sonuc[dosya] = {"metrikler": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()},
                        "dilimler": dilimler, "hatalar": hatalar}
        if dosya == "kabul_testi.jsonl":
            ana_rows, ana_scores = rows, scores
            kapi["sozlesme"] = m["dogruluk"] >= 0.9 and m["tuzak_fp"] == 0
        if dosya == "kabul_saha.jsonl":
            # İki katmanlı kapı (üretim-hatası-regresyon deseni):
            #  - "bildirilen": Ebubekir'in cihazda GÖRDÜĞÜ üretim hata kalıpları
            #    (haber+URL, meta-veri, çıplak URL, forum) — SÜRÜM ENGELLEYİCİ,
            #    0 FP şart (regresyon olmamalı).
            #  - "cekismeli": model sertleştirme için proaktif eklenen zor
            #    çekişmeli testler (kupon/kampanya, üyelik CTA); bazıları
            #    bağlamsız kararlaştırılamaz → İZLENİR, engellemez.
            #  - "gri": etiketi ekipçe belirsiz → hiçbir hesaba girmez.
            # Karar ÜRETİM SİSTEMİYLE (kesin-kelime VEYA model).
            y_s = np.array([r["label"] for r in rows])
            gri = np.array([bool(r.get("gri")) for r in rows])
            bildirilen = np.array([r.get("seviye") == "bildirilen" for r in rows])
            kw_s = np.array([keyword_isbetting(r["text"]) for r in rows])
            pred_s = kw_s | (scores >= esik)
            fp_neg = pred_s & (y_s == 0) & ~gri
            fp_bildirilen = int((fp_neg & bildirilen).sum())      # engelleyici
            fp_cekismeli = int((fp_neg & ~bildirilen).sum())      # izleme
            neg_cek = int(((y_s == 0) & ~gri & ~bildirilen).sum())
            kapi["bildirilen_regresyon"] = fp_bildirilen == 0
            sonuc[dosya]["izleme_cekismeli_fp"] = fp_cekismeli
            sonuc[dosya]["izleme_cekismeli_fp_orani"] = round(fp_cekismeli / max(1, neg_cek), 3)
            print(f"  KAPI (bildirilen üretim hataları, engelleyici): {fp_bildirilen} FP"
                  f"  {'✓ regresyon yok' if fp_bildirilen == 0 else '✗ REGRESYON'}")
            print(f"  İZLEME (çekişmeli zorlama, engellemez): {fp_cekismeli}/{neg_cek} FP "
                  f"(bağlamsız kararlaştırılamazlar dahil; uygulama-bazlı eşikle çözülür)")

    print("\n=== INV-URL değişmezlik testi (sözleşme seti üzerinde)")
    inv = inv_url_testi(interp, ana_rows, ana_scores, esik)
    kapi["inv_url"] = inv["ihlal"] == 0

    # --- gecikme
    metinler = [r["text"] for r in ana_rows]
    for t in metinler[:20]:
        score_all(interp, [t])
    t0 = time.perf_counter()
    n = 300
    for i in range(n):
        score_all(interp, [metinler[i % len(metinler)]])
    ms = (time.perf_counter() - t0) / n * 1000
    print(f"\nGecikme (bu makine, tek metin): ~{ms:.2f} ms  (telefon bütçesi: 20 ms)")

    basarili = all(kapi.values())
    (CIKTI / "esik.json").write_text(
        json.dumps(
            {"esik": esik, "esik_kaynagi": rapor.get("esik_kaynagi"),
             "surum_kapisi": kapi, "hedef_karsilandi": basarili,
             "inv_url_testi": inv, "olcum_gecikme_ms": round(ms, 2),
             "setler": sonuc},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSürüm kapısı: {kapi}")
    print(f"esik.json yazıldı. Hedef karşılandı mı: {'EVET' if basarili else 'HAYIR'}")

    colab_ciktilari_indir()


def colab_ciktilari_indir() -> None:
    """Colab'da koşuluyorsa çıktıları model_cikti.zip olarak paketler.

    files.download() yalnızca not defteri hücresinden çalışır; script
    '!python' ile ayrı süreçte koştuğunda paketler ve talimat yazdırır.
    Yerel/PC koşusunda hiçbir şey yapmaz.
    """
    try:
        from google.colab import files  # type: ignore
    except ImportError:
        return
    import shutil

    zip_yolu = shutil.make_archive(str(MODEL_DIR / "model_cikti"), "zip", root_dir=str(CIKTI))
    print(f"\nColab: çıktılar paketlendi → {zip_yolu}")
    try:
        files.download(zip_yolu)
        print("İndirme başlatıldı; dosyayı Bağimlilik_TEKNOFEST klasörüne kaydedin/taşıyın.")
    except Exception:
        print("Otomatik indirme bu süreçten yapılamıyor (normal). Yeni bir HÜCREDE çalıştırın:")
        print(f'    from google.colab import files; files.download("{zip_yolu}")')


if __name__ == "__main__":
    main()
