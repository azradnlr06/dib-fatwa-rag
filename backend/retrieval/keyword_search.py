from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import SparseVector

from .base import COLLECTION_NAME, SPARSE_MODEL_NAME, SPARSE_VECTOR_NAME, TOP_K, get_qdrant_client, payload_to_hit


def load_sparse_model(model_name: str = SPARSE_MODEL_NAME) -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name=model_name)


def retrieve_keyword(
    query: str,
    sparse_model: SparseTextEmbedding,
    client: QdrantClient,
    top_k: int = TOP_K,
) -> list[dict]:
    sparse_embedding = next(sparse_model.query_embed([query]))
    query_vector = SparseVector(
        indices=sparse_embedding.indices.tolist(),
        values=sparse_embedding.values.tolist(),
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using=SPARSE_VECTOR_NAME,
        limit=top_k,
    ).points

    return [payload_to_hit(r.payload, r.id, score=r.score) for r in results]


def main():
    client = get_qdrant_client()

    print("Sparse (BM25) model yükleniyor...")
    sparse_model = load_sparse_model()
    print("Hazır.\n")

    print("Keyword arama testi. Çıkmak için 'q' yazın.\n")
    while True:
        query = input("Soru: ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue

        hits = retrieve_keyword(query, sparse_model, client)

        print(f"\n--- En alakalı {len(hits)} sonuç ---")
        for i, h in enumerate(hits, 1):
            print(f"\n[{i}] BM25 skoru: {h['score']}")
            print(f"    Başlık: {h['ana_baslik']}")
            print(f"    Soru: {h['soru']}")
            print(f"    Link: {h['link']}")
            print(f"    Metin (ilk 150 karakter): {h['metin'][:150]}...")
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()