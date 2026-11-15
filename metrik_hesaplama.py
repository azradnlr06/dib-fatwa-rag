"""
FETVA RAG - 3 YÖNTEM İÇİN KARŞILAŞTIRMALI METRİK HESAPLAMA
------------------------------------------------------------
semantic / keyword / hibrit retrieval sonuçlarını AYRI AYRI değerlendirir,
sonra yan yana karşılaştırır. Hiçbir metrik tek bir sayıya indirgenip
yöntemler karıştırılmaz.

Yani aynı 108-120 soruyu üç retrieval yönteminizden de ayrı ayrı geçirip
her birinin top-5 sonucunu kendi kolon grubuna yazacaksınız. Aynı sorular,
aynı ground truth (kayit_id) - değişen sadece hangi yöntemin getirdiği
sonuçlar.
"""

import pandas as pd
import numpy as np
import os
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill

INPUT_XLSX = "sonuclar.xlsx"
OUTPUT_XLSX = "degerlendirme_raporu.xlsx" 
K_VALUES = [1, 3, 4]   # sonuclar.py'de TOP_K=4 kullanıldığı için üst sınır 4 (5 anlamsız olurdu, hiç getirilmiyor)
METHODS = ["semantic", "keyword", "hybrid"]   # kolon prefix'leri buna göre aranır (sonuclar.xlsx'teki gerçek isimlerle eşleşmeli)


def get_method_cols(df, method):
    cols = [c for c in df.columns if c.startswith(f"{method}_getirilen_kayit_id_")]
    return sorted(cols, key=lambda x: int(x.split("_")[-1]))


def compute_metrics_for_method(df, method, k_values=K_VALUES):
    cols = get_method_cols(df, method)
    if not cols:
        return None, None

    results = []
    for _, row in df.iterrows():
        dogru = row["kayit_id"]
        getirilenler = [row[c] for c in cols if pd.notna(row[c])]

        rank = None
        for i, g in enumerate(getirilenler, 1):
            if g == dogru:
                rank = i
                break

        rec = {
            "test_id": row["test_id"],
            "kullanici_sorusu": row.get("kullanici_sorusu", ""),
            "dogru_kayit_id": dogru,
            "yontem": method,
            "bulundu_mu": rank is not None,
            "kacinci_sirada": rank if rank else "",
            "reciprocal_rank": (1.0 / rank) if rank else 0.0,
        }
        for k in k_values:
            rec[f"hit@{k}"] = 1 if (rank is not None and rank <= k) else 0
        results.append(rec)

    res_df = pd.DataFrame(results)

    summary = {"Yöntem": method, "Toplam Soru": len(res_df)}
    summary["MRR"] = round(res_df["reciprocal_rank"].mean(), 4)
    for k in k_values:
        summary[f"Hit Rate@{k}"] = round(res_df[f"hit@{k}"].mean(), 4)
    for k in k_values:
        summary[f"Precision@{k}"] = round(res_df[f"hit@{k}"].mean() / k, 4)
    summary["Hiç Bulunamayan"] = int((res_df["kacinci_sirada"] == "").sum())

    return res_df, summary


def build_question_level_sheet(df, method_results, methods):
    """Her sorunun her yöntem tarafından bulunup bulunamadığını ve kaçıncı
    sırada bulunduğunu tek tabloda gösterir. Başarısız olan yöntem sayısı
    en çok olan sorular en üstte listelenir - hangi sorularda sistemin
    zorlandığını hızlıca görmek için."""
    base_cols = ["test_id", "kullanici_sorusu", "ana_baslik"] if "ana_baslik" in df.columns else ["test_id", "kullanici_sorusu"]
    merged = df[base_cols + ["kayit_id"]].rename(columns={"kayit_id": "dogru_kayit_id"})

    for method in methods:
        res_df = method_results.get(method, {}).get("res_df")
        if res_df is None:
            continue
        sub = res_df[["test_id", "bulundu_mu", "kacinci_sirada"]].rename(
            columns={
                "bulundu_mu": f"{method}_bulundu_mu",
                "kacinci_sirada": f"{method}_kacinci_sirada",
            }
        )
        merged = merged.merge(sub, on="test_id", how="left")

    bulundu_cols = [c for c in merged.columns if c.endswith("_bulundu_mu")]
    merged["basarisiz_yontem_sayisi"] = merged[bulundu_cols].apply(lambda r: (r == False).sum(), axis=1)
    merged = merged.sort_values(["basarisiz_yontem_sayisi", "test_id"], ascending=[False, True]).reset_index(drop=True)
    return merged



def build_disagreement_sheet(df, method_results):
    """Yöntemlerin birbirinden farklı sonuç verdiği (biri buluyor biri
    bulamıyor) soruları listeler - kalitatif inceleme için en kritik yer."""
    rows = []
    for _, row in df.iterrows():
        tid = row["test_id"]
        hits = {}
        for method in METHODS:
            res_df = method_results.get(method, {}).get("res_df")
            if res_df is None:
                continue
            match = res_df[res_df["test_id"] == tid]
            if len(match):
                hits[method] = bool(match.iloc[0]["bulundu_mu"])
        if len(set(hits.values())) > 1:  # yöntemler arasında fark varsa
            r = {"test_id": tid, "kullanici_sorusu": row.get("kullanici_sorusu", "")}
            r.update({f"{m}_buldu_mu": hits.get(m) for m in METHODS})
            rows.append(r)
    return pd.DataFrame(rows)


if not os.path.exists(INPUT_XLSX):
    print(f"UYARI: {INPUT_XLSX} bulunamadı.")
    print("Önce test_seti.xlsx'i semantic/keyword/hibrit sistemlerinizden ayrı ayrı")
    print("geçirip sonuçları yukarıdaki formatta 'sonuclar.xlsx' olarak kaydedin.")
else:
    df = pd.read_excel(INPUT_XLSX)

    method_results = {}
    summaries = []
    for method in METHODS:
        res_df, summary = compute_metrics_for_method(df, method)
        if res_df is None:
            print(f"UYARI: '{method}' için 'getirilen_kayit_id' kolonları bulunamadı, atlanıyor.")
            continue
        method_results[method] = {"res_df": res_df, "summary": summary}
        summaries.append(summary)

    if not summaries:
        raise SystemExit("Hiçbir yöntem için veri bulunamadı. Kolon isimlerini kontrol edin.")

    summary_df = pd.DataFrame(summaries).set_index("Yöntem").T

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        # --- Özet karşılaştırma ---
        summary_df.to_excel(writer, sheet_name="Ozet_Karsilastirma")

        # --- Konu bazlı, uzun format (yöntem karşılaştırmalı) ---
        if "ana_baslik" in df.columns:
            topic_rows = []
            for method, d in method_results.items():
                merged = d["res_df"].merge(df[["test_id", "ana_baslik"]], on="test_id")
                grp = merged.groupby("ana_baslik").agg(
                    soru_sayisi=("bulundu_mu", "count"),
                    hit_rate_5=("hit@4", "mean"),
                    mrr=("reciprocal_rank", "mean"),
                ).round(3)
                grp["yontem"] = method
                topic_rows.append(grp.reset_index())
            topic_df = pd.concat(topic_rows, ignore_index=True)
            pivot = topic_df.pivot(index="ana_baslik", columns="yontem", values="hit_rate_5")
            pivot.to_excel(writer, sheet_name="Konu_Bazli")

        # --- Yöntem başına soru detay + başarısız sorular ---
        for method, d in method_results.items():
            d["res_df"].to_excel(writer, sheet_name=f"Detay_{method}"[:31], index=False)
            basarisiz = d["res_df"][d["res_df"]["kacinci_sirada"] == ""]
            basarisiz.to_excel(writer, sheet_name=f"Basarisiz_{method}"[:31], index=False)

        # --- Soru bazlı karşılaştırma (hangi soru, hangi yöntemde başarısız) ---
        question_level_df = build_question_level_sheet(df, method_results, METHODS)
        question_level_df.to_excel(writer, sheet_name="Soru_Bazli_Karsilastirma", index=False)

        # --- Yöntemler arası anlaşmazlık ---
        disagreement_df = build_disagreement_sheet(df, method_results)
        disagreement_df.to_excel(writer, sheet_name="Anlasmazlik", index=False)

    # --- Excel'e bar chart ekle (Hit Rate@1 / @3 / @4 karşılaştırması, gruplu) ---
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment

    wb = load_workbook(OUTPUT_XLSX)
    ws = wb["Ozet_Karsilastirma"]

    # başlık satırını kalınlaştır
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Hit Rate@k satırlarının konumunu bul (artık kod içinde bitişik sıralanıyorlar)
    hit_rows = [r for r in range(1, ws.max_row + 1) if str(ws.cell(row=r, column=1).value).startswith("Hit Rate@")]

    if hit_rows:
        chart = BarChart()
        chart.type = "col"
        chart.grouping = "clustered"
        chart.title = "Yöntemlere Göre Hit Rate Karşılaştırması (@1 / @3 / @4)"
        chart.y_axis.title = "Hit Rate"
        chart.x_axis.title = "Yöntem"
        n_methods = len(method_results)

        # min_col=1 dahil ediliyor ki satır başlıkları (Hit Rate@1 vb.) seri adı olarak kullanılsın
        data = Reference(ws, min_col=1, max_col=1 + n_methods, min_row=min(hit_rows), max_row=max(hit_rows))
        cats = Reference(ws, min_col=2, max_col=1 + n_methods, min_row=1, max_row=1)
        chart.add_data(data, titles_from_data=True, from_rows=True)
        chart.set_categories(cats)
        chart.legend.position = "b"
        chart.height = 9
        chart.width = 18
        ws.add_chart(chart, f"A{ws.max_row + 3}")

    # --- Soru bazlı karşılaştırma sheet'inde başarısız hücreleri kırmızıya boya ---
    if "Soru_Bazli_Karsilastirma" in wb.sheetnames:
        ws2 = wb["Soru_Bazli_Karsilastirma"]
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        for cell in ws2[1]:
            cell.font = Font(bold=True)
        header = [c.value for c in ws2[1]]
        bulundu_col_idxs = [i + 1 for i, h in enumerate(header) if isinstance(h, str) and h.endswith("_bulundu_mu")]
        for r in range(2, ws2.max_row + 1):
            for c_idx in bulundu_col_idxs:
                cell = ws2.cell(row=r, column=c_idx)
                if cell.value is False:
                    cell.fill = red_fill

    wb.save(OUTPUT_XLSX)

    print(f"Rapor oluşturuldu -> {OUTPUT_XLSX}")
    print("\nÖZET KARŞILAŞTIRMA:")
    print(summary_df)