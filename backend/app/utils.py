from app.schemas import ResultItem

KEYWORD_SCORE_K = 8.0


def normalize_to_percent(scores: list[float], mode: str) -> list[int]:
    
    if not scores:
        return []

    if mode == "semantic":
        return [max(1, min(100, round(s * 100))) for s in scores]

    if mode == "keyword":
        return [
            max(1, min(100, round(100 * s / (s + KEYWORD_SCORE_K))))
            for s in scores
        ]

    return [max(1, min(100, round(s * 100))) for s in scores]


def hits_to_results(hits: list[dict], mode: str) -> list[ResultItem]:
    if not hits:
        return []

    # score listesi
    scores = [
        h["score"] if h["score"] is not None else 0.0
        for h in hits
    ]

    # mode'e göre yüzde hesapla
    relevances = normalize_to_percent(scores, mode)

    results = []

    for hit, relevance in zip(hits, relevances):
        baslik = (
            hit.get("ana_baslik")
            or hit.get("soru")
            or "(başlık yok)"
        )

        metin = hit.get("metin") or ""

        ozet = (
            (metin[:280] + "…")
            if len(metin) > 280
            else metin
        )

        if not ozet:
            ozet = hit.get("soru") or ""

        etiketler = []

        results.append(
            ResultItem(
                id=str(hit.get("kayit_id")),
                relevance=relevance,
                baslik=baslik,
                ozet=ozet,
                etiketler=etiketler,
            )
        )

    return results