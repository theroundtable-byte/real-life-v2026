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

  const DAY_COLOR = "#f4efe4";
  const NIGHT_COLOR = "#171814";
  const toggle = document.getElementById("theme-toggle");
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "night" ? "night" : "day";
  }

  function syncToggle(theme) {
    if (!toggle) return;
    const night = theme === "night";
    toggle.setAttribute("aria-label", night ? "Switch to light mode" : "Switch to dark mode");
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
      const head = article.querySelector(".patch-head") || article;
      if (head && !head.querySelector(".fresh-flag")) {
        const flag = document.createElement("p");
        flag.className = "fresh-flag";
        flag.textContent = "New since your last visit";
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
  const sections = Array.prototype.slice.call(document.querySelectorAll(".sec-card, .patch-section"));
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

  document.querySelectorAll(".expand").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const card = btn.closest(".sec-card");
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (card) card.classList.toggle("is-open", open);
      const label = btn.getAttribute("data-more-label") || "Show more";
      btn.textContent = open ? "Show less" : label;
    });
  });

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
      const has = section.querySelector(".entry:not([hidden])");
      section.hidden = !has;
      if (filtering && has) section.classList.add("is-open");
      else if (!filtering && !section.querySelector(".expand[aria-expanded='true']")) {
        if (section.querySelector(".expand")) section.classList.remove("is-open");
      }
    });
    if (empty) empty.hidden = visible !== 0;
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      active = chip.getAttribute("data-filter") || "all";
      if (active === "all" && input) input.value = "";
      chips.forEach(function (c) { c.classList.toggle("is-on", c === chip); });
      apply();
      if (article && chip.getBoundingClientRect().bottom < (article.getBoundingClientRect().top)) {
        article.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
      }
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

  const reveals = document.querySelectorAll(".reveal");
  if (reduce) {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  } else if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(function (rows) {
      rows.forEach(function (row) {
        if (row.isIntersecting) {
          row.target.classList.add("is-in");
          io.unobserve(row.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }

  const stage = document.getElementById("world-stage") || document.querySelector(".hero-art");
  const motion = stage && stage.querySelector(".world-motion");
  if (stage && !reduce) {
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        const y = window.scrollY || 0;
        stage.style.setProperty("--py", Math.max(-28, Math.min(18, y * -0.08)) + "px");
        ticking = false;
      });
    }, { passive: true });
    if (motion && window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
      stage.addEventListener("mousemove", function (e) {
        const r = stage.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        motion.style.setProperty("--tilt-x", (-y * 10).toFixed(2) + "deg");
        motion.style.setProperty("--tilt-y", (x * 14).toFixed(2) + "deg");
      });
      stage.addEventListener("mouseleave", function () {
        motion.style.setProperty("--tilt-x", "0deg");
        motion.style.setProperty("--tilt-y", "0deg");
      });
    }
  }

  if (!reduce && window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll(".sec-card").forEach(function (card) {
      card.addEventListener("mousemove", function (e) {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = "translateY(-6px) rotateX(" + (-y * 4).toFixed(2) + "deg) rotateY(" + (x * 5).toFixed(2) + "deg)";
      });
      card.addEventListener("mouseleave", function () {
        card.style.transform = "";
      });
    });
  }
})();
