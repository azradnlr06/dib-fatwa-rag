"use client";

import { useState } from "react";
import FetvaModal from "./fetva_modal";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const MODE_LABELS = {
  keyword: "Anahtar Kelime",
  semantic: "Anlamsal",
  hybrid: "Hibrit",
};


export default function FetvaSonucKarti({ result, mode }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [detailStatus, setDetailStatus] = useState("idle"); // idle | loading | ready | error
  const [detail, setDetail] = useState(null);

  async function openModal() {
    setModalOpen(true);

    if (detailStatus === "idle") {
      setDetailStatus("loading");
      try {
        const res = await fetch(`${API_BASE_URL}/api/fetva/${result.id}`);
        const data = await res.json();

        if (!res.ok) {
          throw new Error(data?.message || "Fetva bulunamadı.");
        }

        setDetail(data);
        setDetailStatus("ready");
      } catch (err) {
        setDetailStatus("error");
      }
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openModal();
    }
  }

  return (
    <>
      <article
        className="result-card"
        role="button"
        tabIndex={0}
        onClick={openModal}
        onKeyDown={handleKeyDown}
      >
        <div className="result-top">
          <span className="result-id">{result.id}</span>
          <span className="relevance-badge">
            %{result.relevance} eşleşme · {MODE_LABELS[mode]}
          </span>
        </div>

        <h3 className="result-title">{result.baslik}</h3>
        <p className="result-snippet">{result.ozet}</p>

        {result.etiketler?.length > 0 && (
          <div className="result-tags">
            {result.etiketler.map((t, i) => (
              <span className="result-tag" key={i}>
                {t}
              </span>
            ))}
          </div>
        )}

        <span className="result-expand-hint">Detayları gör ✦</span>
      </article>

      {modalOpen && (
        <FetvaModal
          result={result}
          mode={mode}
          status={detailStatus}
          detail={detail}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}