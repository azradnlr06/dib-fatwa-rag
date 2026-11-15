"""
FETVA RAG - TEST SETİ OLUŞTURMA
--------------------------------
Bu script chunked_output.json'dan ana başlıklara göre DENGELİ (stratified)
örneklem alır ve değerlendirme için TEK bir test seti üretir.

ÖNEMLİ: Bu test seti (aynı sorular, aynı ground truth) hem semantic, hem
keyword, hem de hibrit arama için KULLANILACAK. Üç yöntemi adil kıyaslamak
için hepsinin aynı sorularla test edilmesi şart - farklı test setleriyle
kıyaslama yaparsanız sonuçlar anlamsızlaşır.

"""

import json
import random
from collections import defaultdict
import pandas as pd
import os

random.seed(42)  # tekrarlanabilir örneklem

CHUNKED_PATH = "backend/chunked_output.json"
TOPLAM_TEST_SORUSU = 120
MIN_PER_TOPIC = 2 
OUTPUT_XLSX = "test_seti.xlsx"


with open(CHUNKED_PATH, encoding="utf-8") as f:
    chunks = json.load(f)

by_kayit = defaultdict(list)
for c in chunks:
    by_kayit[c["kayit_id"]].append(c)

records = []
for kid, clist in by_kayit.items():
    first = clist[0]
    records.append({
        "kayit_id": kid,
        "soru": first["soru"],
        "ana_baslik": first["ana_baslik"],
        "alt_baslik": first["alt_baslik"],
        "link": first["link"],
        "chunk_sayisi": len(clist),
    })

# ---- Ana başlığa göre dengeli örnekleme ----
by_topic = defaultdict(list)
for r in records:
    by_topic[r["ana_baslik"]].append(r)

n_topics = len(by_topic)
base_per_topic = max(MIN_PER_TOPIC, TOPLAM_TEST_SORUSU // n_topics)

sampled = []
for topic, items in by_topic.items():
    k = min(base_per_topic, len(items))
    sampled.extend(random.sample(items, k))

random.shuffle(sampled)
sampled = sampled[:TOPLAM_TEST_SORUSU]

rows = []
for i, r in enumerate(sampled, 1):
    rows.append({
        "test_id": i,
        "kayit_id": r["kayit_id"],
        "orijinal_soru": r["soru"],
        "kullanici_sorusu": "",
        "ana_baslik": r["ana_baslik"],
        "alt_baslik": r["alt_baslik"],
        "chunk_sayisi": r["chunk_sayisi"],
        "dogru_link": r["link"],
    })

df = pd.DataFrame(rows)

os.makedirs(os.path.dirname(OUTPUT_XLSX), exist_ok=True)
df.to_excel(OUTPUT_XLSX, index=False, sheet_name="test_seti")

print(f"{len(df)} soruluk test seti oluşturuldu -> {OUTPUT_XLSX}")
print(df["ana_baslik"].value_counts())
print("\nSıradaki adım: 'kullanici_sorusu' kolonunu kendi yönteminizle doldurun.")