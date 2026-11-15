from contextlib import asynccontextmanager
 
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
 
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings
from app.schemas import SearchMode, SearchResponse, FetvaDetail
from app.utils import hits_to_results
 
from retrieval.base import get_qdrant_client, TOP_K, COLLECTION_NAME
from retrieval.semantic_search import load_model, retrieve_semantic
from retrieval.keyword_search import load_sparse_model, retrieve_keyword
from retrieval.hibrit_search import retrieve_hybrid
 

ml = {}


def _parse_anahtar_kelimeler(raw: str | None) -> list[str]:
    """Qdrant payload'ında 'zaruret, maslahat, cerrahî müdahale' gibi tek bir
    string olarak duran anahtar kelimeleri listeye çevirir."""
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Qdrant client bağlanıyor...")
    ml["client"] = get_qdrant_client()
 
    print("Dense model (bge-m3) yükleniyor, bu biraz sürebilir...")
    ml["dense_model"] = load_model()
 
    print("Sparse (BM25) model yükleniyor...")
    ml["sparse_model"] = load_sparse_model()
 
    print("Backend hazır.")
    yield
    ml.clear()
 
 
app = FastAPI(title="Fetva Arşivi API", lifespan=lifespan)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
 
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})
 
 
@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": bool(ml)}
 
 
@app.get("/api/search", response_model=SearchResponse)
def api_search(
    q: str = Query(..., min_length=1, description="Kullanıcı sorgusu"),
    mode: SearchMode = Query(SearchMode.hybrid),
    top_k: int = Query(TOP_K, ge=1, le=50),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="0-1 arası minimum benzerlik"),
):
    client = ml["client"]
    dense_model = ml["dense_model"]
    sparse_model = ml["sparse_model"]
 
    try:
        if mode == SearchMode.semantic:
            hits = retrieve_semantic(q, dense_model, client, top_k=top_k)
        elif mode == SearchMode.keyword:
            hits = retrieve_keyword(q, sparse_model, client, top_k=top_k)
        elif mode == SearchMode.hybrid:
            hits = retrieve_hybrid(
                q, dense_model, sparse_model, client,
                top_k=top_k, candidate_k=settings.hybrid_candidate_k,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Bilinmeyen mod: {mode}")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Arama sırasında hata oluştu: {exc}",
        )
 
    results = hits_to_results(hits, mode)
 
    # threshold (0-1) -> normalize edilmiş relevance (0-100) üzerinden filtre
    threshold_percent = threshold * 100
    results = [r for r in results if r.relevance >= threshold_percent]
 
    return SearchResponse(query=q, mode=mode, results=results)


@app.get("/api/fetva/{kayit_id}", response_model=FetvaDetail)
def api_fetva_detail(kayit_id: int):
    client = ml["client"]


    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="kayit_id", match=MatchValue(value=kayit_id))]
        ),
        with_payload=True,
        with_vectors=False,
        limit=50,  # bir fetvanın chunk sayısı için güvenli üst sınır
    )

    if not points:
        raise HTTPException(status_code=404, detail="Fetva bulunamadı.")

    payloads = sorted(
        (p.payload for p in points), key=lambda p: p.get("chunk_index", 0)
    )

    ilk = payloads[0]
    tam_metin = "\n\n".join(p.get("chunk_metni", "") for p in payloads)

    return FetvaDetail(
        kayit_id=kayit_id,
        soru=ilk.get("soru", ""),
        ana_baslik=ilk.get("ana_baslik", ""),
        alt_baslik=ilk.get("alt_baslik", ""),
        anahtar_kelimeler=_parse_anahtar_kelimeler(ilk.get("anahtar_kelimeler")),
        link=ilk.get("link", ""),
        tarih=ilk.get("tarih", ""),
        tam_metin=tam_metin,
    )