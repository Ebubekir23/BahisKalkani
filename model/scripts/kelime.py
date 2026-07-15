# -*- coding: utf-8 -*-
"""KeywordDetector.kt'nin (Android) Python kopyası — değerlendirmenin gerçek
üretim sistemini (kesin-kelime VEYA model) ölçebilmesi için.

Android tarafı yalnızca "kesin" ifadeleri tek başına engelleme sebebi sayar;
"genel" terimler (bahis, iddaa...) modele bırakılır (çıplak terimler haber ve
şikayet metinlerini de kapatıyordu). Kaynak: app/src/main/assets/keywords.json
+ app/.../detection/KeywordDetector.kt (mantık birebir).
"""
import json
from pathlib import Path

_KW_JSON = Path(__file__).resolve().parents[2] / "app/src/main/assets/keywords.json"

CENSOR = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}


def _tr_lower(t: str) -> str:
    return t.replace("İ", "i").replace("I", "ı").lower().replace("̇", "")


def _load():
    if not _KW_JSON.exists():
        return [], []
    kw = json.loads(_KW_JSON.read_text(encoding="utf-8"))
    return [k.lower() for k in kw.get("kesin", [])], [p.lower() for p in kw.get("ignored", [])]


KESIN, IGNORED = _load()


def keyword_isbetting(text: str) -> bool:
    """KeywordDetector.isBettingContent (Android, yalnız kesin) birebir."""
    low = _tr_lower(text)
    for p in IGNORED:
        low = low.replace(p, "")
    norm = "".join(CENSOR.get(c, c) for c in low)
    return any(k in norm for k in KESIN)
