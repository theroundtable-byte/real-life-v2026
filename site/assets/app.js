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

  const input = document.getElementById("q");
  const chips = Array.prototype.slice.call(document.querySelectorAll(".chip[data-filter]"));
  const entries = Array.prototype.slice.call(document.querySelectorAll(".entry"));
  const sections = Array.prototype.slice.call(document.querySelectorAll(".patch-section"));
  const empty = document.getElementById("empty");
  const moreBtn = document.getElementById("full-changelog");
  const fullLog = document.getElementById("full-log");
  let active = "all";
  let userOpened = false;

  function setFullOpen(open) {
    if (!fullLog || !moreBtn) return;
    fullLog.hidden = !open;
    moreBtn.setAttribute("aria-expanded", open ? "true" : "false");
    const n = moreBtn.getAttribute("data-count") || "";
    moreBtn.textContent = open ? "Hide full changelog" : (n ? "Full changelog (" + n + " more)" : "Full changelog");
  }

  if (moreBtn && fullLog) {
    const rest = fullLog.querySelectorAll(".entry").length;
    moreBtn.setAttribute("data-count", String(rest));
    moreBtn.addEventListener("click", function () {
      const open = fullLog.hidden;
      userOpened = open;
      setFullOpen(open);
    });
  }

  function apply() {
    const q = (input && input.value ? input.value : "").trim().toLowerCase();
    const filtering = active !== "all" || Boolean(q);
    if (filtering) setFullOpen(true);
    else if (!userOpened) setFullOpen(false);

    let visible = 0;
    entries.forEach(function (item) {
      const filt = item.getAttribute("data-filter") || "";
      const text = item.getAttribute("data-text") || item.textContent.toLowerCase();
      const filtOk = active === "all" || filt === active;
      const qOk = !q || text.indexOf(q) !== -1;
      const show = filtOk && qOk;
      item.hidden = !show;
      if (show) visible += 1;
    });
    sections.forEach(function (section) {
      section.hidden = !section.querySelector(".entry:not([hidden])");
    });
    if (empty) empty.hidden = visible !== 0;
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      active = chip.getAttribute("data-filter") || "all";
      if (active === "all" && input) input.value = "";
      chips.forEach(function (c) { c.classList.toggle("is-on", c === chip); });
      apply();
    });
  });
  if (input) input.addEventListener("input", apply);
})();
