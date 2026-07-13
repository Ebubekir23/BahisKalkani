# -*- coding: utf-8 -*-
"""BahisKalkanı tespit modeli — eğitim + TFLite dönüşümü.

Girdi:  model/data/egitim.jsonl (sentetik) + model/data/gercek.jsonl (varsa)
Çıktı:  model/cikti/model.tflite, model_vocab.json, egitim_raporu.json

Çalıştırma (Colab):  python model/scripts/train.py
İsteğe bağlı ön adım: python model/scripts/ayarla.py  (Optuna hiperparametre
araması; sonucu cikti/en_iyi_ayarlar.json'a yazar, train.py varsa onu kullanır)

Aşırı öğrenme (overfitting) önlemleri — 13 Temmuz güncellemesi:
- SpatialDropout1D (embedding kanallarını topluca düşürür — küçük veri için etkili)
- L2 ağırlık cezası (conv + dense), etiket yumuşatma (label smoothing)
- EarlyStopping (val_auc) + ReduceLROnPlateau
- Çoğaltma yalnız eğitim bölmesine (bölme ÇOĞALTMADAN ÖNCE — varyant sızıntısı yok)
- Rapora eğitim/doğrulama farkı yazılır ("asiri_ogrenme_farki") — fark
  büyükse (>~%4-5) ezber var demektir, ayarla.py koşulmalı
"""

import json
import random
import shutil
import sys
import unicodedata
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import tensorflow as tf

# ---------------------------------------------------------------- sabitler

MODEL_DIR = Path(__file__).resolve().parent.parent
DATA = MODEL_DIR / "data" / "egitim.jsonl"          # sentetik set (kontrollü kapsam)
GERCEK = MODEL_DIR / "data" / "gercek.jsonl"        # gerçek set (varsa eklenir)
CIKTI = MODEL_DIR / "cikti"
AYAR_DOSYASI = CIKTI / "en_iyi_ayarlar.json"        # ayarla.py (Optuna) çıktısı

MAX_LEN = 192          # kodpoint cinsinden; spec/ON_ISLEME.md ile senkron
PAD, OOV = 0, 1
SEED = 42

# ayarla.py bulursa üzerine yazar; bulamazsa bu değerlerle eğitilir
VARSAYILAN_AYARLAR = {
    "embed_dim": 32,
    "filtreler": 64,
    "cekirdekler": [2, 3, 4, 5],
    "spatial_dropout": 0.15,
    "dropout1": 0.3,
    "dropout2": 0.2,
    "dense_birim": 64,
    "l2": 1e-4,
    "lr": 1e-3,
    "label_smoothing": 0.05,
    "batch": 32,
}

# Sözlük ON_ISLEME.md'deki tanımın tek kaynağı burasıdır; model_vocab.json
# olarak dışa yazılır ve Kotlin tarafı aynı dosyayı okur. Sıra ÖNEMLİDİR
# (id'ler sıradan türetilir) — yeni karakter eklemek gerekirse SONA ekle.
VOCAB_CHARS = (
    "abcçdefgğhıijklmnoöprsştuüvyzqwx"   # Türk alfabesi + q w x
    "0123456789"
    " .,!?;:'\"/\\()[]{}<>@#$%^&*+-_=~|₺€"
    "💚🔥🎰💰⚽🎁✅⭐📲"                  # bahis paylaşımlarında sık görülen emojiler
)
CHAR2ID = {c: i + 2 for i, c in enumerate(VOCAB_CHARS)}  # 0=pad, 1=oov

# Sansür ikamesi (KeywordDetector'dakiyle aynı harita) — burada TERSİNE,
# veri çoğaltma için kullanılır: temiz pozitiflerden sansürlü varyant üretir.
CENSOR = {"o": "0", "i": "1", "e": "3", "a": "4", "s": "5", "t": "7"}
CENSOR_EXTRA = {"a": "@", "s": "$"}
ASCII_FOLD = {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u"}
SPACED_KEYWORDS = [
    "bahis", "iddaa", "casino", "kumar", "rulet", "bonus",
    "çevrim", "freebet", "jackpot", "kazino",
]

# ---------------------------------------------------------------- ön işleme


def turkish_lower(text: str) -> str:
    """Kotlin'deki lowercase(Locale("tr")) ile birebir aynı sonucu verir.

    Python'un .lower()'ı 'I'→'i' yapar (Türkçede 'ı' olmalı) ve 'İ'→'i̇'
    (i + U+0307) bırakır; ikisi de elle düzeltilir.
    """
    text = text.replace("İ", "i").replace("I", "ı")
    text = text.lower()
    return text.replace("̇", "")


def preprocess(text: str) -> list[int]:
    """Metin → id dizisi. Spec: spec/ON_ISLEME.md (Kotlin ile adım adım aynı)."""
    text = unicodedata.normalize("NFC", text)
    text = turkish_lower(text)
    ids = [CHAR2ID.get(ch, OOV) for ch in text][:MAX_LEN]
    return ids + [PAD] * (MAX_LEN - len(ids))


# ---------------------------------------------------------------- veri


def veri_yukle() -> list[dict]:
    """Sentetik + (varsa) gerçek eğitim verisini yükler. ayarla.py de kullanır."""
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Sentetik eğitim verisi: {len(rows)} örnek "
          f"({sum(r['label'] for r in rows)} pozitif)")
    if GERCEK.exists():
        gercek = [json.loads(l) for l in GERCEK.read_text(encoding="utf-8").splitlines() if l.strip()]
        rows += [{"text": r["text"], "label": r["label"]} for r in gercek]
        print(f"Gerçek eğitim verisi: {len(gercek)} örnek eklendi "
              f"({sum(r['label'] for r in gercek)} pozitif) — toplam {len(rows)}")
    return rows


def ayarlari_yukle() -> dict:
    a = dict(VARSAYILAN_AYARLAR)
    if AYAR_DOSYASI.exists():
        kayit = json.loads(AYAR_DOSYASI.read_text(encoding="utf-8"))
        a.update(kayit["ayarlar"])
        print(f"Ayarlar: Optuna araması (cv_auc={kayit.get('cv_auc'):.4f}, "
              f"{kayit.get('denemeler')} deneme) — {AYAR_DOSYASI.name}")
    else:
        print("Ayarlar: varsayılan (isteğe bağlı arama için: python model/scripts/ayarla.py)")
    return a


# ---------------------------------------------------------------- veri çoğaltma


def censor_variant(text: str, rng: random.Random) -> str:
    out = []
    for ch in text:
        lower = ch.lower()
        if lower in CENSOR and rng.random() < 0.45:
            if lower in CENSOR_EXTRA and rng.random() < 0.3:
                out.append(CENSOR_EXTRA[lower])
            else:
                out.append(CENSOR[lower])
        else:
            out.append(ch)
    return "".join(out)


def ascii_variant(text: str) -> str:
    return "".join(ASCII_FOLD.get(ch, ASCII_FOLD.get(ch.lower(), ch)) for ch in text)


def spaced_variant(text: str, rng: random.Random) -> str | None:
    lower = turkish_lower(text)
    for kw in SPACED_KEYWORDS:
        idx = lower.find(kw)
        if idx >= 0:
            sep = rng.choice([" ", ".", "-"])
            word = text[idx : idx + len(kw)]
            return text[:idx] + sep.join(word) + text[idx + len(kw) :]
    return None


def augment(rows: list[dict], rng: random.Random) -> list[dict]:
    """Pozitiflere yoğun, negatiflere hafif gürültü ekler.

    Negatiflere de sansür/ascii varyantı eklenir ki model "rakamlı yazım =
    bahis" gibi sahte bir bağıntı öğrenmesin (oyuncu dili 'n00b' masumdur).
    """
    out = list(rows)
    for r in rows:
        text, label = r["text"], r["label"]
        if label == 1:
            if rng.random() < 0.55:
                out.append({"text": censor_variant(text, rng), "label": 1})
            if rng.random() < 0.60:
                out.append({"text": ascii_variant(text), "label": 1})
            if rng.random() < 0.50:
                sp = spaced_variant(text, rng)
                if sp:
                    out.append({"text": sp, "label": 1})
        else:
            # negatif tarafta hafif tutulur; "aksansız/rakamlı yazım = bahis"
            # sahte bağıntısına karşı asıl çözüm organik aksansız örnekler
            if rng.random() < 0.15:
                out.append({"text": censor_variant(text, rng), "label": 0})
            if rng.random() < 0.30:
                out.append({"text": ascii_variant(text), "label": 0})
    # çoğaltma sonrası tekilleştir
    seen, dedup = set(), []
    for r in out:
        key = " ".join(turkish_lower(r["text"]).split())
        if key and key not in seen:
            seen.add(key)
            dedup.append(r)
    return dedup


def to_xy(rs: list[dict]):
    x = np.array([preprocess(r["text"]) for r in rs], dtype=np.int32)
    y = np.array([r["label"] for r in rs], dtype=np.float32)
    return x, y


# ---------------------------------------------------------------- eşik seçimi


def en_uzun_plato(adaylar: list[tuple[float, float]]) -> tuple[float, tuple[float, float]]:
    """(eşik, metrik) listesinde metriği maksimum yapan EN UZUN BİTİŞİK bloğu
    bulur; (blok ortası eşik, (blok başı, blok sonu)) döner.

    Maksimum kümesi kopuk olabilir (az örnekte metrik eşiğe göre monoton
    değildir); bitişik bloğun ortası, küçük skor oynamalarına en dayanıklı
    eşiği verir.
    """
    best = max(m for _, m in adaylar)
    en_iyi = None
    i = 0
    while i < len(adaylar):
        if adaylar[i][1] == best:
            j = i
            while j + 1 < len(adaylar) and adaylar[j + 1][1] == best:
                j += 1
            if en_iyi is None or (j - i) > (en_iyi[1] - en_iyi[0]):
                en_iyi = (i, j)
            i = j + 1
        else:
            i += 1
    i, j = en_iyi
    return adaylar[(i + j) // 2][0], (adaylar[i][0], adaylar[j][0])


# ---------------------------------------------------------------- model


def build_model(vocab_size: int, a: dict) -> tf.keras.Model:
    l2 = tf.keras.regularizers.l2(a["l2"]) if a["l2"] else None
    inp = tf.keras.Input(shape=(MAX_LEN,), dtype="int32", name="metin_idleri")
    x = tf.keras.layers.Embedding(vocab_size, a["embed_dim"], name="karakter_embedding")(inp)
    x = tf.keras.layers.SpatialDropout1D(a["spatial_dropout"])(x)
    pools = []
    for k in a["cekirdekler"]:
        c = tf.keras.layers.Conv1D(a["filtreler"], k, activation="relu",
                                   kernel_regularizer=l2, name=f"conv_k{k}")(x)
        pools.append(tf.keras.layers.GlobalMaxPooling1D()(c))
    x = tf.keras.layers.Concatenate()(pools) if len(pools) > 1 else pools[0]
    x = tf.keras.layers.Dropout(a["dropout1"])(x)
    x = tf.keras.layers.Dense(a["dense_birim"], activation="relu", kernel_regularizer=l2)(x)
    x = tf.keras.layers.Dropout(a["dropout2"])(x)
    out = tf.keras.layers.Dense(1, activation="sigmoid", name="tesvik_skoru")(x)
    model = tf.keras.Model(inp, out)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(a["lr"]),
        loss=tf.keras.losses.BinaryCrossentropy(label_smoothing=a["label_smoothing"]),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="acc"),
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="kesinlik"),
            tf.keras.metrics.Recall(name="duyarlilik"),
        ],
    )
    return model


def egitim_callbacks(patience: int = 8) -> list:
    return [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_auc", mode="max", patience=patience, restore_best_weights=True,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_auc", mode="max", factor=0.5, patience=3, min_lr=1e-5,
        ),
    ]


# ---------------------------------------------------------------- akış


def main() -> None:
    rng = random.Random(SEED)
    tf.random.set_seed(SEED)
    np.random.seed(SEED)

    rows = veri_yukle()
    ayarlar = ayarlari_yukle()

    # katmanlı (stratified) bölme: %85 eğitim, %15 doğrulama — ÇOĞALTMADAN ÖNCE
    # bölünür ki aynı cümlenin varyantları iki tarafa sızmasın
    pos = [r for r in rows if r["label"] == 1]
    neg = [r for r in rows if r["label"] == 0]
    rng.shuffle(pos)
    rng.shuffle(neg)
    cut_p, cut_n = int(len(pos) * 0.85), int(len(neg) * 0.85)
    train_rows = augment(pos[:cut_p] + neg[:cut_n], rng)
    val_rows = pos[cut_p:] + neg[cut_n:]
    rng.shuffle(train_rows)
    print(f"Çoğaltma sonrası eğitim: {len(train_rows)}, doğrulama: {len(val_rows)}")

    x_tr, y_tr = to_xy(train_rows)
    x_va, y_va = to_xy(val_rows)

    n_pos = float(y_tr.sum())
    n_neg = float(len(y_tr) - n_pos)
    class_weight = {0: (n_pos + n_neg) / (2 * n_neg), 1: (n_pos + n_neg) / (2 * n_pos)}

    vocab_size = len(VOCAB_CHARS) + 2
    model = build_model(vocab_size, ayarlar)
    model.summary()

    model.fit(
        x_tr, y_tr,
        validation_data=(x_va, y_va),
        epochs=60,
        batch_size=ayarlar["batch"],
        class_weight=class_weight,
        callbacks=egitim_callbacks(),
        verbose=2,
    )

    val_metrics = {k: float(v) for k, v in model.evaluate(x_va, y_va, verbose=0, return_dict=True).items()}
    tr_metrics = {k: float(v) for k, v in model.evaluate(x_tr, y_tr, verbose=0, return_dict=True).items()}
    fark = tr_metrics["acc"] - val_metrics["acc"]
    print("Doğrulama:", val_metrics)
    print(f"Aşırı öğrenme farkı (eğitim acc − doğrulama acc): {fark:+.3f} "
          f"{'— YÜKSEK, ayarla.py önerilir' if fark > 0.05 else '(makul)'}")

    # --- eşik önerisi BURADA, doğrulama bölmesinde seçilir. Kabul setinde
    # seçilmez: aynı sette hem eşik seçmek hem başarı raporlamak iyimser
    # sapma yaratır (kabul seti yalnızca SABİT eşikle rapor eder).
    p_va = model.predict(x_va, verbose=0).ravel()
    adaylar = []
    for esik in [round(0.05 + i * 0.01, 2) for i in range(91)]:
        pred = p_va >= esik
        tp = int((pred & (y_va == 1)).sum())
        fp = int((pred & (y_va == 0)).sum())
        fn = int((~pred & (y_va == 1)).sum())
        f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
        adaylar.append((esik, f1))
    onerilen_esik, plato = en_uzun_plato(adaylar)
    print(f"Önerilen eşik (doğrulama F1 platosu {plato[0]}–{plato[1]} ortası): {onerilen_esik}")

    # --- TFLite dönüşümü (Keras 3 ile en sağlam yol: SavedModel üzerinden)
    CIKTI.mkdir(exist_ok=True)
    saved = CIKTI / "_saved_model"
    model.export(str(saved))
    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved))
    converter.optimizations = [tf.lite.Optimize.DEFAULT]  # dinamik aralık kuantalama
    tflite = converter.convert()
    (CIKTI / "model.tflite").write_bytes(tflite)
    shutil.rmtree(saved, ignore_errors=True)  # ara ürün; çıktı paketine girmesin
    print(f"model.tflite: {len(tflite) / 1024:.0f} KB (sınır: 10 MB)")

    (CIKTI / "model_vocab.json").write_text(
        json.dumps(
            {"surum": 1, "max_len": MAX_LEN, "pad": PAD, "oov": OOV,
             "karakterler": {c: i for c, i in CHAR2ID.items()}},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    (CIKTI / "egitim_raporu.json").write_text(
        json.dumps(
            {"ham_ornek": len(rows), "cogaltilmis_egitim": len(train_rows),
             "dogrulama_ornek": len(val_rows), "dogrulama_metrikleri": val_metrics,
             "egitim_metrikleri": tr_metrics,
             "asiri_ogrenme_farki": round(fark, 4),
             "kullanilan_ayarlar": ayarlar,
             "onerilen_esik": onerilen_esik,
             "esik_platosu": [plato[0], plato[1]],
             "tflite_kb": round(len(tflite) / 1024, 1)},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print("Bitti. Sıradaki adım: python model/scripts/degerlendir.py")


if __name__ == "__main__":
    main()
