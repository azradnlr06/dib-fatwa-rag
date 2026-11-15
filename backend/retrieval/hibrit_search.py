from qdrant_client.models import Prefetch, FusionQuery, Fusion, SparseVector

from .base import COLLECTION_NAME, DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME, TOP_K, get_qdrant_client, payload_to_hit
from .semantic_search import load_model
from .keyword_search import load_sparse_model


def retrieve_hybrid(
    query: str,
    dense_model,
    sparse_model,
    client,
    top_k: int = TOP_K,
    candidate_k: int = 20,
) -> list[dict]:

    dense_vector = dense_model.encode([query], normalize_embeddings=True).tolist()[0]

    sparse_embedding = next(sparse_model.query_embed([query]))
    sparse_vector = SparseVector(
        indices=sparse_embedding.indices.tolist(),
        values=sparse_embedding.values.tolist(),
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            Prefetch(query=dense_vector, using=DENSE_VECTOR_NAME, limit=candidate_k),
            Prefetch(query=sparse_vector, using=SPARSE_VECTOR_NAME, limit=candidate_k),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
    ).points

    return [payload_to_hit(r.payload, r.id, score=r.score) for r in results]


def main():
    client = get_qdrant_client()

    print("Dense model yükleniyor...")
    dense_model = load_model()

    print("Sparse (BM25) model yükleniyor...")
    sparse_model = load_sparse_model()
    print("Hazır.\n")

    print("Hybrid arama testi. Çıkmak için 'q' yazın.\n")
    while True:
        query = input("Soru: ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue

        hits = retrieve_hybrid(query, dense_model, sparse_model, client)

        print(f"\n--- En alakalı {len(hits)} sonuç (hybrid/RRF) ---")
        for i, h in enumerate(hits, 1):
            print(f"\n[{i}] RRF skoru: {h['score']}")
            print(f"    Başlık: {h['ana_baslik']}")
            print(f"    Soru: {h['soru']}")
            print(f"    Link: {h['link']}")
            print(f"    Metin (ilk 150 karakter): {h['metin'][:150]}...")
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()