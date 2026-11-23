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

  const DAY_COLOR = "#eef4e6";
  const NIGHT_COLOR = "#0c1612";
  const toggle = document.getElementById("theme-toggle");
  const themeMeta = document.querySelector('meta[name="theme-color"]');

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "night" ? "night" : "day";
  }

  function syncToggle(theme) {
    if (!toggle) return;
    const night = theme === "night";
    toggle.setAttribute("aria-label", night ? "Switch to day mode" : "Switch to night mode");
    toggle.setAttribute("aria-pressed", night ? "true" : "false");
    if (themeMeta) themeMeta.setAttribute("content", night ? NIGHT_COLOR : DAY_COLOR);
  }

  function setTheme(theme, persist) {
    if (theme === "night") document.documentElement.setAttribute("data-theme", "night");
    else document.documentElement.removeAttribute("data-theme");
    if (persist) {
      try { localStorage.setItem("rlv2026:theme", theme); } catch (err) {}
    }
    syncToggle(theme);
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get("theme") === "night" || params.get("theme") === "day") {
    setTheme(params.get("theme"), false);
  } else {
    syncToggle(currentTheme());
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      setTheme(currentTheme() === "night" ? "day" : "night", true);
    });
  }

  const article = document.getElementById("latest");
  const patchId = article && article.getAttribute("data-patch-id");
  const LAST_KEY = "rlv2026:lastPatch";
  if (article && patchId) {
    let prev = null;
    try { prev = localStorage.getItem(LAST_KEY); } catch (err) {}
    const forceFresh = params.get("fresh") === "1";
    if ((prev && prev !== patchId) || forceFresh) {
      article.classList.add("is-fresh");
      const head = article.querySelector(".patch-head");
      if (head && !head.querySelector(".fresh-flag")) {
        const flag = document.createElement("p");
        flag.className = "fresh-flag";
        flag.textContent = "New patch since your last visit";
        head.insertBefore(flag, head.firstChild);
      }
    }
    function remember() {
      try { localStorage.setItem(LAST_KEY, patchId); } catch (err) {}
    }
    if (!prev) remember();
    window.addEventListener("pagehide", remember);
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

  function copyShare(text, url, btn) {
    const payload = (text + " — " + url).trim();
    const done = function () {
      if (!btn) return;
      const old = btn.textContent;
      btn.textContent = "Copied";
      btn.classList.add("is-copied");
      setTimeout(function () {
        btn.textContent = old;
        btn.classList.remove("is-copied");
      }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(payload).then(done).catch(function () {
        window.prompt("Copy this patch line", payload);
      });
    } else {
      window.prompt("Copy this patch line", payload);
    }
  }

  document.querySelectorAll(".share").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const text = btn.getAttribute("data-share-text") || "";
      const url = btn.getAttribute("data-share-url") || "";
      if (navigator.share) {
        navigator.share({ title: "Real Life v2026", text: text, url: url }).catch(function () {
          copyShare(text, url, btn);
        });
        return;
      }
      copyShare(text, url, btn);
    });
  });
})();
