"use client";

import { useState } from "react";
import FetvaSonucKarti from "./fetva_result.card";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const MODES = [
  {
    key: "keyword",
    name: "Anahtar Kelime",
    desc: "Sorgudaki kelimelerin metinde birebir geçtiği fetvaları bulur.",
  },
  {
    key: "semantic",
    name: "Anlamsal",
    desc: "Kelimeler farklı olsa bile anlamca yakın fetvaları bulur.",
  },
  {
    key: "hybrid",
    name: "Hibrit",
    desc: "Anahtar kelime ve anlamsal sonuçları birlikte değerlendirir.",
  },
];

const MODE_LABELS = Object.fromEntries(MODES.map((m) => [m.key, m.name]));

export default function Page() {
  const [selectedMode, setSelectedMode] = useState(null);
  const [showModeWarning, setShowModeWarning] = useState(false);
  const [shake, setShake] = useState(false);

  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(50);

  const [status, setStatus] = useState("idle"); // idle | loading | message | results
  const [message, setMessage] = useState("");
  const [results, setResults] = useState([]);
  const [resultMode, setResultMode] = useState(null);

  function handleSelectMode(modeKey) {
    setSelectedMode(modeKey);
    setShowModeWarning(false);
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!selectedMode) {
      setShowModeWarning(true);
      setShake(false);
      // reflow benzeri: animasyonu yeniden tetiklemek için
      requestAnimationFrame(() => setShake(true));
      document
        .querySelector(".mode-grid")
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      document.getElementById("query")?.focus();
      return;
    }

    await runSearch(trimmedQuery, selectedMode, topK, threshold);
  }

  async function runSearch(q, mode, topKValue, thresholdValue) {
    setStatus("loading");

    try {
      const params = new URLSearchParams({
        q,
        mode,
        top_k: String(topKValue),
        threshold: (Number(thresholdValue) / 100).toFixed(2), // 0-100 -> 0-1
      });

      const res = await fetch(`${API_BASE_URL}/api/search?${params.toString()}`);
      const data = await res.json();

      if (!res.ok) {
        setStatus("message");
        setMessage(data.message || "Bir hata oluştu.");
        return;
      }

      if (!data.results || data.results.length === 0) {
        setStatus("message");
        setMessage(`"${data.query}" için sonuç bulunamadı.`);
        return;
      }

      setResultMode(data.mode);
      setResults(data.results);
      setStatus("results");
    } catch (err) {
      setStatus("message");
      setMessage(
        `Sunucuya ulaşılamadı (${API_BASE_URL}). Python backend'in çalıştığından ve CORS'un açık olduğundan emin olun.`
      );
    }
  }

  const isLoading = status === "loading";

  return (
    <main className="page">
      <header className="hero">
        <p className="eyebrow">1367 FETVA</p>
        <h1 className="title">Fetva Arşivi</h1>
        <p className="subtitle">
          Bir arama yöntemi seçin, sorunuzu yazın; arşiv size en ilgili
          fetvaları getirsin.
        </p>
      </header>

      <section className="panel" aria-labelledby="mode-heading">
        <div className="mode-block">
          <div className="mode-heading-row">
            <h2 id="mode-heading">Arama yöntemi</h2>
          </div>

          <div
            className="mode-grid"
            role="radiogroup"
            aria-labelledby="mode-heading"
          >
            {MODES.map((m) => (
              <button
                key={m.key}
                type="button"
                className="mode-card"
                data-mode={m.key}
                role="radio"
                aria-checked={selectedMode === m.key}
                onClick={() => handleSelectMode(m.key)}
              >
                <span className="mode-star" aria-hidden="true">
                  ✦
                </span>
                <span className="mode-name">{m.name}</span>
                <span className="mode-desc">{m.desc}</span>
              </button>
            ))}
          </div>

          {showModeWarning && (
            <p
              className={`mode-warning${shake ? " shake" : ""}`}
              id="mode-warning"
              role="alert"
              onAnimationEnd={() => setShake(false)}
            >
              Devam etmeden önce bir arama yöntemi seçmelisiniz.
            </p>
          )}
        </div>

        <div className="advanced-block" id="advanced-block">
          <div className="advanced-heading-row">
            <span className="advanced-summary-text">Gelişmiş Ayarlar</span>
            <span className="optional-tag">opsiyonel</span>
          </div>

          <div className="advanced-grid">
            <div className="advanced-field">
              <div className="advanced-field-head">
                <label htmlFor="topk-input">
                  Getirilecek sonuç sayısı (Top K)
                </label>
                <span className="advanced-value" id="topk-value">
                  {topK}
                </span>
              </div>
              <input
                type="range"
                id="topk-input"
                name="topk"
                min="1"
                max="20"
                step="1"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              />
              <p className="advanced-hint">
                Aramanın en fazla kaç fetva getireceğini belirler.
              </p>
            </div>

            <div className="advanced-field">
              <div className="advanced-field-head">
                <label htmlFor="threshold-input">Benzerlik eşiği</label>
                <span className="advanced-value" id="threshold-value">
                  %{threshold}
                </span>
              </div>
              <input
                type="range"
                id="threshold-input"
                name="threshold"
                min="0"
                max="100"
                step="5"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
              />
              <p className="advanced-hint">
                Sorgu ile fetva arasında aranacak minimum benzerlik oranı.
              </p>
            </div>
          </div>
        </div>

        <div className="divider" aria-hidden="true">
          <span>✦</span>
          <span className="line"></span>
          <span>✦</span>
          <span className="line"></span>
          <span>✦</span>
        </div>

        <form
          className="search-block"
          id="search-form"
          autoComplete="off"
          onSubmit={handleSubmit}
        >
          <label className="search-label" htmlFor="query">
            Sorunuz
          </label>
          <div className="search-row">
            <input
              type="text"
              id="query"
              name="query"
              placeholder="Örn. seferde namaz nasıl kısaltılır?"
              aria-describedby="mode-warning"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              type="submit"
              className="ara-button"
              id="ara-button"
              disabled={isLoading}
            >
              {isLoading ? "Aranıyor…" : "Ara"}
            </button>
          </div>
          <p className="hint">
            Seçili yöntem:{" "}
            <span id="selected-mode-label">
              {selectedMode ? MODE_LABELS[selectedMode] : "yok"}
            </span>
          </p>
        </form>
      </section>

      <section className="results" id="results" aria-live="polite">
        {status === "idle" && (
          <div className="results-empty" id="results-empty">
            <span className="najma-icon" aria-hidden="true">
              ✧
            </span>
            <p>Sonuçlar burada görünecek. Bir yöntem seçip aramaya başlayın.</p>
          </div>
        )}

        {status === "loading" && (
          <div className="loading">
            <span className="najma-icon" aria-hidden="true">
              ✧
            </span>
            <p>Fetva arşivi taranıyor…</p>
          </div>
        )}

        {status === "message" && (
          <div className="results-empty">
            <span className="najma-icon" aria-hidden="true">
              ✧
            </span>
            <p>{message}</p>
          </div>
        )}

        {status === "results" &&
          results.map((r) => (
            <FetvaSonucKarti key={r.id} result={r} mode={resultMode} />
          ))}
      </section>

      <footer className="footer">
        <p>
          Bu arayüz, gerçek 1367 fetvalık veri seti ve embedding modeli
          bağlanmadan önce mimariyi doğrulamak için 20 örnek/mock kayıt
          kullanır.
        </p>
      </footer>
    </main>
  );
}