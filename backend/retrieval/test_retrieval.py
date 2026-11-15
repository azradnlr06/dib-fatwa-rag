 
from .base import get_qdrant_client
from .semantic_search import load_model, retrieve_semantic
from .keyword_search import load_sparse_model, retrieve_keyword
from .hibrit_search import retrieve_hybrid
 
 
def print_hits(hits, label):
    print(f"\n--- {label}: en alakalı {len(hits)} sonuç ---")
    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] Skor: {h['score']}")
        print(f"    Başlık: {h['ana_baslik']}")
        print(f"    Soru: {h['soru']}")
        print(f"    Link: {h['link']}")
        print(f"    Metin (ilk 150 karakter): {h['metin'][:150]}...")
 
 
def main():
    client = get_qdrant_client()
 
    print("Dense model yükleniyor...")
    dense_model = load_model()
 
    print("Sparse (BM25) model yükleniyor...")
    sparse_model = load_sparse_model()
 
    count = client.count("fetva_koleksiyonu").count

    print("Mod seç: [1] semantic  [2] keyword  [3] hybrid ")
    mode = input("Mod: ").strip()
 
    print("\nÇıkmak için 'q' yazın.\n")
    while True:
        query = input("Soru: ").strip()
        if query.lower() == "q":
            break
        if not query:
            continue
 
        if mode == "1":
            hits = retrieve_semantic(query, dense_model, client)
            print_hits(hits, "SEMANTIC")
 
        elif mode == "2":
            hits = retrieve_keyword(query, sparse_model, client)
            print_hits(hits, "KEYWORD")
 
        elif mode == "3":
            hits = retrieve_hybrid(query, dense_model, sparse_model, client)
            print_hits(hits, "HYBRID")
 
        elif mode == "4":
            print_hits(retrieve_semantic(query, dense_model, client), "SEMANTIC")
            print_hits(retrieve_keyword(query, sparse_model, client), "KEYWORD")
            print_hits(retrieve_hybrid(query, dense_model, sparse_model, client), "HYBRID")
 
        else:
            print("Geçersiz mod, tekrar dene.")
            continue
 
        print("\n" + "-" * 60 + "\n")
 
 
if __name__ == "__main__":
    main()
 