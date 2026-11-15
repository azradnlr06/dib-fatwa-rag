"use client";

import { useEffect } from "react";

const MODE_LABELS = {
  keyword: "Anahtar Kelime",
  semantic: "Anlamsal",
  hybrid: "Hibrit",
};

export default function FetvaModal({ result, mode, status, detail, onClose }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="modal-close"
          onClick={onClose}
          aria-label="Kapat"
        >
          ×
        </button>

        <div className="detail-top">
          <span className="result-id">{result.id}</span>
          <span className="relevance-badge">
            %{result.relevance} eşleşme · {MODE_LABELS[mode]}
          </span>
        </div>

        <h2 className="detail-title">{result.baslik}</h2>

        {status === "loading" && (
          <div className="loading">
            <span className="najma-icon" aria-hidden="true">
              ✧
            </span>
            <p>Fetva yükleniyor…</p>
          </div>
        )}

        {status === "error" && (
          <div className="results-empty">
            <span className="najma-icon" aria-hidden="true">
              ✧
            </span>
            <p>Fetva yüklenemedi. Backend'in çalıştığından emin olun.</p>
          </div>
        )}

        {status === "ready" && detail && (
          <>
            <div className="detail-category">
              {detail.ana_baslik}
              {detail.alt_baslik && (
                <>
                  <span className="detail-category-sep">›</span>
                  {detail.alt_baslik}
                </>
              )}
            </div>

            {detail.tarih && <p className="detail-date">{detail.tarih}</p>}

            {detail.anahtar_kelimeler?.length > 0 && (
              <div className="detail-keywords">
                {detail.anahtar_kelimeler.map((k, i) => (
                  <span className="keyword-chip" key={i}>
                    {k}
                  </span>
                ))}
              </div>
            )}

            <div className="detail-divider" aria-hidden="true">
              <span>✦</span>
              <span className="line"></span>
              <span>✦</span>
              <span className="line"></span>
              <span>✦</span>
            </div>

            <div className="detail-body">
              {detail.tam_metin
                .split("\n")
                .map((para, i) => para.trim() && <p key={i}>{para}</p>)}
            </div>

            {detail.link && (
              <div className="detail-source">
                <a href={detail.link} target="_blank" rel="noopener noreferrer">
                  Kaynak: Diyanet Fetva Kurulu ↗
                </a>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}