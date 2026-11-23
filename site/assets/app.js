(function () {
  const cryptoBox = document.getElementById("crypto-ticker");
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
    if (!cryptoBox) return;
    const parts = [];
    coins.forEach(function (c) {
      const row = data[c.id];
      if (!row || typeof row.usd !== "number") return;
      const ch = row.usd_24h_change || 0;
      const cls = ch >= 0 ? "up" : "down";
      const sign = ch >= 0 ? "+" : "";
      parts.push('<span class="coin ' + cls + '"><b>' + c.symbol + "</b> $" + money(row.usd) + " " + sign + ch.toFixed(2) + "%</span>");
    });
    if (parts.length) cryptoBox.innerHTML = parts.join(" ");
  }

  async function loadCrypto() {
    if (!cryptoBox) return;
    const url = cryptoBox.getAttribute("data-endpoint");
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("status " + res.status);
      renderCrypto(await res.json());
    } catch (err) {
      if (!cryptoBox.querySelector(".coin")) {
        cryptoBox.innerHTML = '<span class="ticker-status">Prices unavailable right now.</span>';
      }
    }
  }

  if (cryptoBox) {
    loadCrypto();
    setInterval(loadCrypto, 60000);
  }

  function collapseCards(forceOpen) {
    document.querySelectorAll(".notes[data-collapse]").forEach(function (box) {
      const limit = parseInt(box.getAttribute("data-collapse") || "5", 10);
      const notes = box.querySelectorAll(".note");
      const searching = forceOpen;
      notes.forEach(function (note, i) {
        if (searching) {
          note.classList.remove("is-collapsed");
        } else {
          note.classList.toggle("is-collapsed", i >= limit);
        }
      });
      const btn = box.parentElement && box.parentElement.querySelector("[data-more]");
      if (btn) {
        const hidden = box.querySelectorAll(".note.is-collapsed").length;
        btn.hidden = searching || hidden === 0;
        if (!searching) btn.textContent = "Show " + hidden + " more";
      }
    });
  }

  document.querySelectorAll("[data-more]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const box = btn.parentElement.querySelector(".notes");
      if (!box) return;
      const collapsed = box.querySelectorAll(".note.is-collapsed");
      if (collapsed.length) {
        collapsed.forEach(function (n) { n.classList.remove("is-collapsed"); });
        btn.textContent = "Show less";
      } else {
        collapseCards(false);
      }
    });
  });

  const input = document.getElementById("q");
  const chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  const notes = Array.prototype.slice.call(document.querySelectorAll(".note"));
  const sections = Array.prototype.slice.call(document.querySelectorAll(".cat-card"));
  const empty = document.getElementById("empty");
  let active = "all";

  function apply() {
    const q = (input && input.value ? input.value : "").trim().toLowerCase();
    collapseCards(Boolean(q) || active !== "all");
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
      const extras = section.querySelector(".anime-extra");
      const cat = section.getAttribute("data-category") || "";
      const catOk = active === "all" || cat === active;
      section.hidden = !catOk || (!any && !(extras && !q));
    });
    if (empty) empty.hidden = visible !== 0 || (active !== "all" && !q && document.querySelector('.cat-card:not([hidden]) .anime-extra'));
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      active = chip.getAttribute("data-filter") || "all";
      chips.forEach(function (c) { c.classList.toggle("is-on", c === chip); });
      apply();
    });
  });
  if (input) input.addEventListener("input", apply);

  const style = document.createElement("style");
  style.textContent = ".note.is-collapsed { display: none; }";
  document.head.appendChild(style);
  collapseCards(false);
})();
