from enum import Enum
from pydantic import BaseModel, Field


class SearchMode(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"


class ResultItem(BaseModel):
    id: str
    relevance: int  # 0-100 arası yüzde, frontend "%{relevance} eşleşme" diye gösteriyor
    baslik: str
    ozet: str
    etiketler: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    results: list[ResultItem]


class FetvaDetail(BaseModel):
    kayit_id: int
    soru: str
    ana_baslik: str
    alt_baslik: str
    anahtar_kelimeler: list[str] = Field(default_factory=list)
    link: str
    tarih: str
    tam_metin: str


class ErrorResponse(BaseModel):
    message: str