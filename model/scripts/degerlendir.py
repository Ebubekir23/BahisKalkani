# -*- coding: utf-8 -*-
"""Kabul testi + gecikme ölçümü.

Girdi:  model/cikti/model.tflite, model/cikti/model_vocab.json,
        model/cikti/egitim_raporu.json  (train.py'nin önerdiği eşik)
        model/data/kabul_testi.jsonl    ({"text","label","tuzak","kategori"})
Çıktı:  model/cikti/esik.json           (eşik + kabul metrikleri)

Çalıştırma: py -3.12 model/scripts/degerlendir.py   (Colab: python ...)

Metodoloji: eşik train.py tarafından EĞİTİMİN DOĞRULAMA BÖLMESİNDE seçilir;
bu script kabul setini o SABİT eşikle koşar ve raporlar. Eşik kabul setinde
seçilmez — aynı sette hem seçim hem rapor iyimser sapma yaratır. Kabul seti
üstünde tarama yalnızca TANI amaçlı yazdırılır (veri iyileştirme kararı için).

Hedef (görevler/halil-tespit-modeli.md): kabul setinde ≥ %90 doğruluk +
tuzak negatiflerde sıfır yanlış pozitif.
"""

import json
import sys
import time
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import numpy as np

MODEL_DIR = Path(__file__).resolve().parent.parent
CIKTI = MODEL_DIR / "cikti"
KABUL = MODEL_DIR / "data" / "kabul_testi.jsonl"            # sentetik sözleşme seti
KABUL_GERCEK = MODEL_DIR / "data" / "kabul_gercek.jsonl"    # gerçek saha seti (varsa)

# ön işleme + plato seçimi train.py ile tek kaynak
sys.path.insert(0, str(Path(__file__).parent))
from train import MAX_LEN, en_uzun_plato, preprocess  # noqa: E402


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


def metrikler(scores, y, tuzak, esik):
    pred = scores >= esik
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
    """Bir kabul setini sabit eşikle koşar; (metrikler, hatalar) döner."""
    rows = [json.loads(l) for l in dosya.read_text(encoding="utf-8").splitlines() if l.strip()]
    texts = [r["text"] for r in rows]
    y = np.array([r["label"] for r in rows])
    tuzak = np.array([bool(r.get("tuzak")) for r in rows])
    print(f"\n{ad}: {len(rows)} örnek ({y.sum()} pozitif, {tuzak.sum()} tuzak)")

    scores = score_all(interp, texts)
    m = metrikler(scores, y, tuzak, esik)
    print(f"Sonuç @ {esik}: doğruluk {m['dogruluk']:.1%}, F1 {m['f1']:.3f}, "
          f"FP {m['yanlis_pozitif']}, FN {m['yanlis_negatif']}, tuzak FP {m['tuzak_fp']}")

    pred = scores >= esik
    hatalar = [
        {"text": r["text"], "label": r["label"],
         "kategori": r.get("kategori", r.get("kaynak", "?")),
         "skor": round(float(s), 3)}
        for r, s, p in zip(rows, scores, pred) if p != bool(r["label"])
    ]
    for h in hatalar:
        print(f"  HATA [{h['kategori']}] skor={h['skor']} label={h['label']}: {h['text'][:80]}")
    return m, hatalar, scores, y, tuzak


def main() -> None:
    rapor = json.loads((CIKTI / "egitim_raporu.json").read_text(encoding="utf-8"))
    esik = rapor["onerilen_esik"]
    print(f"Sabit eşik (eğitim doğrulama bölmesinden): {esik}")

    interp = load_interpreter()

    # Sözleşme seti (hedef bu sette ölçülür: ≥%90 + tuzak FP=0)
    m, hatalar, scores, y, tuzak = seti_kos(interp, KABUL, esik, "Kabul seti (sentetik sözleşme)")

    # Gerçek saha seti (varsa) — sahadaki başarının dürüst göstergesi
    m_gercek, hatalar_gercek = None, []
    if KABUL_GERCEK.exists():
        m_gercek, hatalar_gercek, *_ = seti_kos(
            interp, KABUL_GERCEK, esik, "Kabul seti (gerçek saha)")

    # --- TANI: kabul seti üstünde tarama (yalnızca bilgi — eşik BURADAN SEÇİLMEZ)
    adaylar = []
    for e in [round(0.05 + i * 0.01, 2) for i in range(91)]:
        mm = metrikler(scores, y, tuzak, e)
        if mm["tuzak_fp"] == 0:
            adaylar.append((e, mm["dogruluk"]))
    if adaylar:
        tani_esik, tani_plato = en_uzun_plato(adaylar)
        tani_acc = dict(adaylar)[tani_esik]
        print(f"\nTanı (bilgi amaçlı, seçim sapmalı): kabul üstünde en iyi bitişik "
              f"plato {tani_plato[0]}–{tani_plato[1]}, doğruluk {tani_acc:.1%}. "
              f"Sabit eşik bu platonun dışındaysa eğitim/kabul dağılımları uyumsuz olabilir.")
    else:
        tani_esik, tani_plato = None, None
        print("\nTanı: hiçbir eşik tuzaklarda sıfır FP vermiyor — veri iyileştirme gerekli.")

    # --- gecikme (PC/Colab ölçümü — telefonda Ebubekir'le tekrar ölçülecek)
    olcum_metinleri = [json.loads(l)["text"] for l in KABUL.read_text(encoding="utf-8").splitlines() if l.strip()]
    for t in olcum_metinleri[:20]:
        score_all(interp, [t])
    t0 = time.perf_counter()
    n = 300
    for i in range(n):
        score_all(interp, [olcum_metinleri[i % len(olcum_metinleri)]])
    ms = (time.perf_counter() - t0) / n * 1000
    print(f"\nGecikme (bu makine, tek metin): ~{ms:.2f} ms  (telefon bütçesi: 20 ms)")

    yuvarla = lambda d: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}
    basarili = m["dogruluk"] >= 0.9 and m["tuzak_fp"] == 0
    (CIKTI / "esik.json").write_text(
        json.dumps(
            {"esik": esik,
             "esik_kaynagi": "egitim dogrulama bolmesi (kabul setlerinden bagimsiz secildi)",
             "kabul_sentetik": yuvarla(m),
             "kabul_gercek": yuvarla(m_gercek) if m_gercek else "kabul_gercek.jsonl yok",
             "tani_kabul_taramasi": {"en_iyi_plato": tani_plato, "not": "secim sapmali, yalnizca bilgi"},
             "olcum_gecikme_ms": round(ms, 2),
             "hedef_karsilandi": basarili,
             "hatalar_sentetik": hatalar,
             "hatalar_gercek": hatalar_gercek},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"esik.json yazıldı. Sözleşme hedefi karşılandı mı: {'EVET' if basarili else 'HAYIR'}"
          + (f" | Gerçek saha doğruluğu: {m_gercek['dogruluk']:.1%}" if m_gercek else ""))

    colab_ciktilari_indir()


def colab_ciktilari_indir() -> None:
    """Colab'da koşuluyorsa çıktıları model_cikti.zip olarak paketler.

    NOT: files.download() yalnızca not defteri hücresinden çalışır; bu script
    "!python ..." ile ayrı süreçte koştuğunda Colab çekirdeğine erişemez
    (AttributeError: kernel). Bu yüzden zip her durumda oluşturulur, indirme
    DENENIR, olmazsa çalıştırılacak tek satırlık hücre yazdırılır.
    Yerel/PC koşusunda google.colab bulunmadığından hiçbir şey yapılmaz.
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
        print("Otomatik indirme bu süreçten yapılamıyor (normal — script '!python' ile koşuyor).")
        print("Yeni bir HÜCREDE şunu çalıştırın:")
        print(f'    from google.colab import files; files.download("{zip_yolu}")')
        print("İnen dosyayı Bağimlilik_TEKNOFEST klasörüne koyun.")


if __name__ == "__main__":
    main()
