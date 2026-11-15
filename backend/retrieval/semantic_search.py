from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
 
from .base import COLLECTION_NAME, DENSE_MODEL_NAME, DENSE_VECTOR_NAME, TOP_K, get_qdrant_client, payload_to_hit
 
 
def load_model(model_name: str = DENSE_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)
 
 
def retrieve_semantic(
    query: str,
    model: SentenceTransformer,
    client: QdrantClient,
    top_k: int = TOP_K,
) -> list[dict]:
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()[0]
 
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        using=DENSE_VECTOR_NAME,
        limit=top_k,
    ).points
 
    hits = [
        payload_to_hit(r.payload, r.id, score=r.score)
        for r in results
    ]
    return hits
 
 
def main():
    model = load_model()
    client = get_qdrant_client()
 
    count = client.count(COLLECTION_NAME).count
    print(f"Koleksiyonda {count} chunk var.\n")
 
    print("Semantic arama testi. Çıkmak için 'q' yazın.\n")
    while True:
        query = input("Soru: ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue
 
        hits = retrieve_semantic(query, model, client)
 
        print(f"\n--- En alakalı {len(hits)} sonuç ---")
        for i, h in enumerate(hits, 1):
            print(f"\n[{i}] Benzerlik: {h['score']}")
            print(f"    Başlık: {h['ana_baslik']}")
            print(f"    Soru: {h['soru']}")
            print(f"    Link: {h['link']}")
            print(f"    Metin (ilk 150 karakter): {h['metin'][:150]}...")
        print("\n" + "-" * 60 + "\n")
 
 
if __name__ == "__main__":
    main()
 