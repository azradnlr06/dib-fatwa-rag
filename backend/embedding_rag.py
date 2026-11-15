import json
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    PointStruct,
    SparseVector,
    Modifier,
)

from retrieval.base import (
    COLLECTION_NAME,
    DENSE_MODEL_NAME,
    SPARSE_MODEL_NAME,
    DENSE_VECTOR_NAME,
    SPARSE_VECTOR_NAME,
    get_qdrant_client,
)

JSON_PATH = "chunked_output.json"
EMBEDDING_DIM = 1024
BATCH_SIZE = 32


def main():
    print(f"'{JSON_PATH}' okunuyor...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Toplam {len(chunks)} chunk bulundu.")

    print("Dense model yükleniyor (BAAI/bge-m3)...")
    dense_model = SentenceTransformer(DENSE_MODEL_NAME)

    print("Sparse (BM25) model yükleniyor (Qdrant/bm25)...")
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME)

    client = get_qdrant_client()

    if client.collection_exists(COLLECTION_NAME):
        print(f"'{COLLECTION_NAME}' koleksiyonu zaten var, siliniyor...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_VECTOR_NAME: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: SparseVectorParams(
                modifier=Modifier.IDF,
            ),
        },
    )

    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding + yazma"):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["chunk_metni"] for c in batch]

        dense_embeddings = dense_model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        sparse_embeddings = list(sparse_model.embed(texts))

        points = []
        for c, dense_emb, sparse_emb in zip(batch, dense_embeddings, sparse_embeddings):
            point_id = c["kayit_id"] * 100 + c["chunk_index"]

            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        DENSE_VECTOR_NAME: dense_emb,
                        SPARSE_VECTOR_NAME: SparseVector(
                            indices=sparse_emb.indices.tolist(),
                            values=sparse_emb.values.tolist(),
                        ),
                    },
                    payload={
                        "kayit_id": c["kayit_id"],
                        "soru": c["soru"],
                        "ana_baslik": c["ana_baslik"],
                        "alt_baslik": c["alt_baslik"],
                        "tarih": c["tarih"],
                        "link": c["link"],
                        "anahtar_kelimeler": c["anahtar_kelimeler"],
                        "chunk_index": c["chunk_index"],
                        "toplam_chunk": c["toplam_chunk"],
                        "token_sayisi": c["token_sayisi"],
                        "chunk_metni": c["chunk_metni"],
                    },
                )
            )

        client.upsert(collection_name=COLLECTION_NAME, points=points)

    count = client.count(COLLECTION_NAME).count
    print(f"\nTamamlandı! {count} chunk Qdrant'a kaydedildi (dense + sparse/BM25).")


if __name__ == "__main__":
    main()