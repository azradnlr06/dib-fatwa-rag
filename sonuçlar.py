"""
sonuclar_uret.py
-----------------
test_seti.xlsx içindeki 108 soruyu okur, semantic / keyword / hybrid
retrieval fonksiyonlarını her soru için çalıştırır ve sonuçları
sonuclar.xlsx olarak kaydeder.
"""

import sys
import os
import pandas as pd


# backend/ klasörünü
# Python'un import arama yoluna (sys.path) elle ekliyoruz.

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, BACKEND_DIR)

TEST_SETI_PATH = "test_seti.xlsx"
SONUCLAR_PATH = "sonuclar.xlsx"


SORU_KOLONU = "kullanici_sorusu"

TOP_K = 4
 

from retrieval.base import get_qdrant_client
from retrieval.semantic_search import load_model, retrieve_semantic
from retrieval.keyword_search import load_sparse_model, retrieve_keyword
from retrieval.hibrit_search import retrieve_hybrid


def kayit_idleri_al(hits: list[dict], top_k: int) -> list:
    """Bir retrieval sonucundan kayit_id listesini çıkarır, top_k uzunluğa tamamlar (eksikse None ile doldurur)."""
    ids = [h.get("kayit_id") for h in hits]
    while len(ids) < top_k:
        ids.append(None)
    return ids[:top_k]


def main():
    print(f"'{TEST_SETI_PATH}' okunuyor...")
    df = pd.read_excel(TEST_SETI_PATH)

    if SORU_KOLONU not in df.columns:
        raise ValueError(
            f"'{SORU_KOLONU}' kolonu test_seti.xlsx içinde bulunamadı. "
            f"Mevcut kolonlar: {list(df.columns)}"
        )

    print("Qdrant client bağlanıyor...")
    client = get_qdrant_client()

    print("Dense model yükleniyor (bge-m3)...")
    dense_model = load_model()

    print("Sparse (BM25) model yükleniyor...")
    sparse_model = load_sparse_model()

    print(f"\nToplam {len(df)} soru için retrieval çalıştırılacak.\n")

    semantic_cols = {f"semantic_getirilen_kayit_id_{i}": [] for i in range(1, TOP_K + 1)}
    keyword_cols = {f"keyword_getirilen_kayit_id_{i}": [] for i in range(1, TOP_K + 1)}
    hybrid_cols = {f"hybrid_getirilen_kayit_id_{i}": [] for i in range(1, TOP_K + 1)}

    for idx, row in df.iterrows():
        query = str(row[SORU_KOLONU]).strip()
        print(f"[{idx + 1}/{len(df)}] Soru işleniyor: {query[:60]}...")

        # --- semantic ---
        sem_hits = retrieve_semantic(query, dense_model, client, top_k=TOP_K)
        sem_ids = kayit_idleri_al(sem_hits, TOP_K)
        for i, val in enumerate(sem_ids, 1):
            semantic_cols[f"semantic_getirilen_kayit_id_{i}"].append(val)

        # --- keyword ---
        key_hits = retrieve_keyword(query, sparse_model, client, top_k=TOP_K)
        key_ids = kayit_idleri_al(key_hits, TOP_K)
        for i, val in enumerate(key_ids, 1):
            keyword_cols[f"keyword_getirilen_kayit_id_{i}"].append(val)

        # --- hybrid ---
        hyb_hits = retrieve_hybrid(query, dense_model, sparse_model, client, top_k=TOP_K)
        hyb_ids = kayit_idleri_al(hyb_hits, TOP_K)
        for i, val in enumerate(hyb_ids, 1):
            hybrid_cols[f"hybrid_getirilen_kayit_id_{i}"].append(val)

    # Yeni kolonları orijinal df'e ekle
    for col_name, values in {**semantic_cols, **keyword_cols, **hybrid_cols}.items():
        df[col_name] = values

    df.to_excel(SONUCLAR_PATH, index=False)
    print(f"\nBitti! '{SONUCLAR_PATH}' oluşturuldu. Toplam kolon sayısı: {len(df.columns)}")


if __name__ == "__main__":
    main()