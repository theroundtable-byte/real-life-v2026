(function () {
  const ticker = document.getElementById("crypto-ticker");
  const coins = [
    { id: "bitcoin", symbol: "BTC" },
    { id: "ethereum", symbol: "ETH" },
    { id: "solana", symbol: "SOL" },
    { id: "ripple", symbol: "XRP" },
    { id: "dogecoin", symbol: "DOGE" },
    { id: "cardano", symbol: "ADA" },
  ];

  function money(n) {
    if (n >= 1000) return n.toLocaleString("en-US", { maximumFractionDigits: 0 });
    if (n >= 1) return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return n.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 6 });
  }

  function renderCrypto(data) {
    const parts = ['<span class="ticker-label">Crypto (live)</span>'];
    coins.forEach(function (c) {
      const row = data[c.id];
      if (!row || typeof row.usd !== "number") return;
      const ch = row.usd_24h_change || 0;
      const cls = ch >= 0 ? "up" : "down";
      const sign = ch >= 0 ? "+" : "";
      parts.push(
        '<span class="coin"><b>' +
          c.symbol +
          "</b> $" +
          money(row.usd) +
          ' <span class="' +
          cls +
          '">' +
          sign +
          ch.toFixed(2) +
          "%</span></span>"
      );
    });
    ticker.innerHTML = parts.join("");
  }

  async function loadCrypto() {
    if (!ticker) return;
    const url = ticker.getAttribute("data-endpoint");
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("status " + res.status);
      renderCrypto(await res.json());
    } catch (err) {
      if (!ticker.querySelector(".coin")) {
        ticker.innerHTML =
          '<span class="ticker-label">Crypto (live)</span><span class="ticker-status">Prices unavailable right now. They will retry automatically.</span>';
      }
    }
  }

  if (ticker) {
    loadCrypto();
    setInterval(loadCrypto, 60000);
  }

  const input = document.getElementById("q");
  const chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  const notes = Array.prototype.slice.call(document.querySelectorAll(".note"));
  const sections = Array.prototype.slice.call(document.querySelectorAll(".cat-section"));
  const empty = document.getElementById("empty");
  let active = "all";

  function apply() {
    const q = (input && input.value ? input.value : "").trim().toLowerCase();
    let visible = 0;
    notes.forEach(function (note) {
      const cat = note.getAttribute("data-category") || "";
      const text = note.getAttribute("data-text") || note.textContent.toLowerCase();
      const catOk = active === "all" || cat === active;
      const qOk = !q || text.indexOf(q) !== -1;
      const show = catOk && qOk;
      note.hidden = !show;
      if (show) visible += 1;
    });
    sections.forEach(function (section) {
      const any = section.querySelector(".note:not([hidden])");
      section.hidden = !any;
    });
    if (empty) empty.hidden = visible !== 0;
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      active = chip.getAttribute("data-filter") || "all";
      chips.forEach(function (c) {
        c.classList.toggle("is-on", c === chip);
      });
      apply();
    });
  });
  if (input) input.addEventListener("input", apply);
})();
