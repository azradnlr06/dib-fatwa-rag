import json
import re
import argparse
from typing import List, Dict, Any
 
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
 
    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except Exception:
    # kaba bir tahmine dus: ortalama 1 token ~ 0.75 kelime
    def count_tokens(text: str) -> int:
        return int(len(text.split()) / 0.75)
 
 
def split_into_paragraphs(text: str) -> List[str]:
    text = text.strip()
    parts = re.split(r"\n\s*\n", text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) > 1:
        return parts
    parts = [p.strip() for p in text.split("\n") if p.strip()]
    return parts if parts else [text]
 
 
_ABBREVIATIONS = r"(?<!\bbk)(?<!\bbkz)(?<!\bvb)(?<!\bvs)(?<!\bDr)(?<!\bNo)(?<!\bs)"
_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])" + _ABBREVIATIONS + r"\s+(?=[A-ZÇĞİÖŞÜ0-9(\"'])"
)
 
 
def split_into_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]
 
 
 
def _pack_units(units: List[str], target_tokens: int) -> List[str]:
    chunks: List[str] = []
    current = ""
    current_tokens = 0
 
    for unit in units:
        unit_tokens = count_tokens(unit)
 
        # Tek basina hedefi asan birim varsa (paragraf), cumlelere bol
        if unit_tokens > target_tokens:
            if current:
                chunks.append(current.strip())
                current, current_tokens = "", 0
            sentences = split_into_sentences(unit)
            if len(sentences) <= 1:
                # Bolunemiyor (tek cumle bile uzun) - oldugu gibi ayri chunk yap
                chunks.append(unit.strip())
                continue
            sub_chunks = _pack_units(sentences, target_tokens)
            chunks.extend(sub_chunks)
            continue
 
        candidate = (current + "\n\n" + unit).strip() if current else unit
        candidate_tokens = count_tokens(candidate)
 
        if candidate_tokens <= target_tokens:
            current, current_tokens = candidate, candidate_tokens
        else:
            if current:
                chunks.append(current.strip())
            current, current_tokens = unit, unit_tokens
 
    if current:
        chunks.append(current.strip())
 
    return chunks
 
 
def _get_overlap_prefix(previous_raw_chunk: str, overlap_ratio: float, target_tokens: int) -> str:
    target_overlap_tokens = max(1, int(target_tokens * overlap_ratio))
    sentences = split_into_sentences(previous_raw_chunk)
    if not sentences:
        return ""
 
    picked = []
    total = 0
    for sent in reversed(sentences):
        sent_tokens = count_tokens(sent)
        if picked and total + sent_tokens > target_overlap_tokens * 1.6:
            break
        picked.insert(0, sent)
        total += sent_tokens
        if len(picked) >= 2:
            break
 
    return " ".join(picked)
 
 
# Tek bir fetva kaydini chunk'lara ayirma
 
def chunk_record(
    record: Dict[str, Any],
    record_id: int,
    token_limit: int = 512,
    overlap_ratio: float = 0.15,
) -> List[Dict[str, Any]]:
    soru = (record.get("Soru") or "").strip()
    cevap = (record.get("Cevap") or "").strip()
 
    full_text = f"{soru}\n\n{cevap}".strip()
    total_tokens = count_tokens(full_text)
 
    base_meta = {
        "kayit_id": record_id,
        "soru": soru,
        "ana_baslik": record.get("Ana Başlık", ""),
        "alt_baslik": record.get("Alt Başlık", ""),
        "tarih": record.get("Tarih", ""),
        "link": record.get("Link", ""),
        "anahtar_kelimeler": record.get("Anahtar Kelimeler", ""),
    }
 
    # 1) Tek chunk yeterli mi?
    if total_tokens <= token_limit:
        return [{
            **base_meta,
            "chunk_index": 1,
            "toplam_chunk": 1,
            "chunk_metni": full_text,
            "token_sayisi": total_tokens,
        }]
 

    soru_tokens = count_tokens(soru)
    target_tokens = max(64, token_limit - soru_tokens - 10)
 

    paragraphs = split_into_paragraphs(cevap)
    raw_chunks = _pack_units(paragraphs, target_tokens)
 
    results = []
    for i, raw_chunk in enumerate(raw_chunks):
        if i == 0:
            content = raw_chunk
        else:
            overlap_prefix = _get_overlap_prefix(
                raw_chunks[i - 1], overlap_ratio, target_tokens
            )
            content = f"{overlap_prefix}\n\n{raw_chunk}".strip() if overlap_prefix else raw_chunk
 
        chunk_text = f"{soru}\n\n{content}".strip()
        results.append({
            **base_meta,
            "chunk_index": i + 1,
            "toplam_chunk": len(raw_chunks),
            "chunk_metni": chunk_text,
            "token_sayisi": count_tokens(chunk_text),
        })
 
    return results
 
 
 
def process_file(
    input_path: str,
    output_path: str,
    token_limit: int = 512,
    overlap_ratio: float = 0.15,
) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)
 
    all_chunks: List[Dict[str, Any]] = []
    for idx, record in enumerate(records):
        chunks = chunk_record(record, idx, token_limit, overlap_ratio)
        all_chunks.extend(chunks)
 
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
 
    tek_chunk = sum(1 for r in records
                    if count_tokens(f"{r.get('Soru','').strip()}\n\n{r.get('Cevap','').strip()}") <= token_limit)
    print(f"Toplam kayit          : {len(records)}")
    print(f"Tek chunk kalan       : {tek_chunk}")
    print(f"Bolunen kayit         : {len(records) - tek_chunk}")
    print(f"Uretilen toplam chunk : {len(all_chunks)}")
    print(f"Cikti dosyasi         : {output_path}")
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diyanet fetva JSON chunking araci")
    parser.add_argument("input", help="Girdi JSON dosyasi (Soru/Cevap listesi)")
    parser.add_argument("output", help="Cikti JSON dosyasi (chunk listesi)")
    parser.add_argument("--limit", type=int, default=512, help="Token siniri (varsayilan: 512)")
    parser.add_argument("--overlap", type=float, default=0.15,
                         help="Overlap orani, hedef boyutun yuzdesi (varsayilan: 0.15)")
    args = parser.parse_args()
 
    process_file(args.input, args.output, args.limit, args.overlap)
 