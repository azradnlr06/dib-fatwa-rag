from qdrant_client import QdrantClient

COLLECTION_NAME = "fetva_koleksiyonu"

DENSE_MODEL_NAME = "BAAI/bge-m3"
SPARSE_MODEL_NAME = "Qdrant/bm25"

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
TOP_K = 5


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def payload_to_hit(payload: dict, point_id, score: float | None = None) -> dict:
    return {
        "id": point_id,
        "kayit_id": payload.get("kayit_id"),
        "soru": payload.get("soru"),
        "ana_baslik": payload.get("ana_baslik"),
        "link": payload.get("link"),
        "metin": payload.get("chunk_metni"),
        "score": round(score, 4) if score is not None else None,
    }