(function () {
  function money(n, kind) {
    if (typeof n !== "number" || !isFinite(n)) return "—";
    if (kind === "index") return n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 1000) return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 1) return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (n >= 0.01) return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 6, maximumFractionDigits: 6 });
  }
  function pct(n) {
    if (typeof n !== "number" || !isFinite(n)) return "—";
    const sign = n >= 0 ? "+" : "";
    return sign + n.toFixed(2) + "%";
  }
  function sparkSvg(values, width, height, id, up, thick) {
    width = width || 640; height = height || 220; thick = thick || 2.2;
    if (!values || values.length < 2) {
      return '<svg class="spark" viewBox="0 0 ' + width + " " + height + '" aria-hidden="true"></svg>';
    }
    var lo = Math.min.apply(null, values), hi = Math.max.apply(null, values);
    var span = (hi - lo) || 1;
    var padX = 2, padY = 3, pts = [];
    for (var i = 0; i < values.length; i++) {
      var x = padX + (width - 2 * padX) * i / (values.length - 1);
      var y = height - padY - (height - 2 * padY) * (values[i] - lo) / span;
      pts.push([x, y]);
    }
    var d = "M" + pts.map(function (p) { return p[0].toFixed(2) + "," + p[1].toFixed(2); }).join(" L");
    var area = d + " L" + pts[pts.length - 1][0].toFixed(2) + "," + height + " L" + pts[0][0].toFixed(2) + "," + height + " Z";
    var color = up ? "var(--up)" : "var(--down)";
    var gid = ("sp-js-" + (id || "x") + "-" + values.length).replace(/[^a-zA-Z0-9_-]/g, "");
    return '<svg class="spark" viewBox="0 0 ' + width + " " + height + '" preserveAspectRatio="none" aria-hidden="true">' +
      '<defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0%" stop-color="' + color + '" stop-opacity="0.32"/>' +
      '<stop offset="100%" stop-color="' + color + '" stop-opacity="0"/>' +
      "</linearGradient></defs>" +
      '<path d="' + area + '" fill="url(#' + gid + ')"/>' +
      '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="' + thick + '" stroke-linejoin="round" stroke-linecap="round"/>' +
      '<circle cx="' + pts[pts.length - 1][0].toFixed(2) + '" cy="' + pts[pts.length - 1][1].toFixed(2) + '" r="2.4" fill="' + color + '"/>' +
      "</svg>";
  }

  var marketsData = null;
  var featuredId = null;
  var featuredRange = "5d";
  var dataNode = document.getElementById("markets-data");
  if (dataNode) {
    try { marketsData = JSON.parse(dataNode.textContent || "{}"); } catch (err) { marketsData = null; }
  }
  if (marketsData && marketsData.featured) featuredId = marketsData.featured;

  function assetById(id) {
    if (!marketsData || !marketsData.assets) return null;
    for (var i = 0; i < marketsData.assets.length; i++) {
      if (marketsData.assets[i].id === id) return marketsData.assets[i];
    }
    return null;
  }
  function seriesFor(asset, range) {
    if (!asset) return [];
    if (range === "1d" && asset.h1d && asset.h1d.length >= 2) return asset.h1d;
    if (range === "5d" && asset.h5d && asset.h5d.length >= 2) return asset.h5d;
    if (range === "1m" && asset.h1m && asset.h1m.length >= 2) return asset.h1m;
    return asset.h5d && asset.h5d.length >= 2 ? asset.h5d : (asset.h1m || asset.h1d || []);
  }
  function hasRange(asset, range) {
    var key = range === "1d" ? "h1d" : range === "1m" ? "h1m" : "h5d";
    var min = range === "1d" ? 8 : 2;
    return asset && asset[key] && asset[key].length >= min;
  }
  function isUp(asset, range) {
    if (!asset) return true;
    if (typeof asset.change_pct === "number") return asset.change_pct >= 0;
    var s = seriesFor(asset, range || "5d");
    return !s.length || s[s.length - 1] >= s[0];
  }
  function paintPrices(asset) {
    if (!asset) return;
    var up = isUp(asset);
    var cls = up ? "up" : "down";
    document.querySelectorAll('[data-id="' + CSS.escape(String(asset.id)) + '"]').forEach(function (el) {
      el.classList.toggle("up", up);
      el.classList.toggle("down", !up);
      var px = el.querySelector(".mkt-px");
      var ch = el.querySelector(".mkt-ch") || (el.classList.contains("feat-price") ? el.querySelector("span") : null);
      if (px) px.textContent = money(asset.price, asset.kind);
      if (ch) ch.textContent = pct(asset.change_pct);
    });
    var feat = document.getElementById("mkt-featured");
    if (feat && feat.getAttribute("data-id") === String(asset.id)) {
      var priceEl = document.getElementById("feat-price");
      if (priceEl) {
        priceEl.className = "feat-price " + cls;
        priceEl.innerHTML = money(asset.price, asset.kind) + " <span>" + pct(asset.change_pct) + "</span>";
      }
    }
  }
  function renderFeatured(id, range) {
    var asset = assetById(id);
    var feat = document.getElementById("mkt-featured");
    var chart = document.getElementById("feat-chart");
    if (!asset || !feat || !chart) return;
    featuredId = id;
    var chosen = range;
    if (!hasRange(asset, chosen)) {
      chosen = hasRange(asset, "5d") ? "5d" : hasRange(asset, "1m") ? "1m" : hasRange(asset, "1d") ? "1d" : "5d";
    }
    featuredRange = chosen;
    feat.setAttribute("data-id", asset.id);
    var name = document.getElementById("feat-name");
    if (name) name.innerHTML = asset.name + ' <span class="feat-sym">' + asset.symbol + "</span>";
    var priceEl = document.getElementById("feat-price");
    var up = isUp(asset, chosen);
    if (priceEl) {
      priceEl.className = "feat-price " + (up ? "up" : "down");
      priceEl.innerHTML = money(asset.price, asset.kind) + " <span>" + pct(asset.change_pct) + "</span>";
    }
    chart.innerHTML = sparkSvg(seriesFor(asset, chosen), 640, 220, "feat-" + asset.id + "-" + chosen, up, 2.2);
    feat.querySelectorAll(".mkt-range").forEach(function (btn) {
      var r = btn.getAttribute("data-range");
      btn.disabled = !hasRange(asset, r);
      btn.classList.toggle("is-on", r === chosen);
    });
    document.querySelectorAll("#mkt-grid .mkt-card").forEach(function (card) {
      var on = card.getAttribute("data-id") === String(asset.id);
      card.classList.toggle("is-on", on);
      card.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  var ticker = document.getElementById("mkt-ticker");
  if (ticker) {
    function pause() { ticker.classList.add("is-paused"); }
    function resume() { ticker.classList.remove("is-paused"); }
    ticker.addEventListener("pointerdown", pause);
    ticker.addEventListener("pointerup", resume);
    ticker.addEventListener("pointercancel", resume);
    ticker.addEventListener("pointerleave", resume);
    ticker.addEventListener("touchstart", pause, { passive: true });
    ticker.addEventListener("touchend", resume);
    ticker.addEventListener("touchcancel", resume);
  }

  var rangeBox = document.querySelector("#mkt-featured .mkt-ranges");
  if (rangeBox) {
    rangeBox.addEventListener("click", function (e) {
      var btn = e.target.closest(".mkt-range");
      if (!btn || btn.disabled) return;
      renderFeatured(featuredId, btn.getAttribute("data-range"));
    });
  }
  var grid = document.getElementById("mkt-grid");
  if (grid) {
    grid.addEventListener("click", function (e) {
      if (e.target.closest(".mkt-card-link")) return;
      var card = e.target.closest(".mkt-card");
      if (!card) return;
      e.preventDefault();
      renderFeatured(card.getAttribute("data-id"), featuredRange);
    });
  }

  // Live crypto: reuse baked ids, refresh prices about once a minute.
  var cryptoIds = [];
  if (marketsData && marketsData.assets) {
    marketsData.assets.forEach(function (a) {
      if (a.kind === "crypto") cryptoIds.push(a.id);
    });
  }
  var cryptoBox = document.getElementById("crypto-ticker");
  if (!cryptoIds.length && cryptoBox && cryptoBox.getAttribute("data-endpoint")) {
    // Archive / legacy card still uses the old six-coin ticker.
    cryptoIds = ["bitcoin", "ethereum", "solana", "ripple", "dogecoin", "cardano"];
  }
  function renderLegacyCrypto(data) {
    if (!cryptoBox) return;
    var map = { bitcoin: "BTC", ethereum: "ETH", solana: "SOL", ripple: "XRP", dogecoin: "DOGE", cardano: "ADA" };
    var parts = [];
    cryptoIds.forEach(function (id) {
      var row = data[id];
      if (!row || typeof row.usd !== "number") return;
      var ch = row.usd_24h_change || 0;
      parts.push('<span class="coin ' + (ch >= 0 ? "up" : "down") + '"><b>' + (map[id] || id.toUpperCase()) + "</b> " + money(row.usd) + " " + pct(ch) + "</span>");
    });
    if (parts.length) cryptoBox.innerHTML = parts.join(" ");
  }
  async function loadCrypto() {
    if (!cryptoIds.length) return;
    var url = "https://api.coingecko.com/api/v3/simple/price?ids=" + encodeURIComponent(cryptoIds.join(",")) + "&vs_currencies=usd&include_24hr_change=true";
    if (cryptoBox && cryptoBox.getAttribute("data-endpoint") && !document.getElementById("markets-data")) {
      url = cryptoBox.getAttribute("data-endpoint");
    }
    try {
      var res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("status " + res.status);
      var data = await res.json();
      if (marketsData && marketsData.assets) {
        marketsData.assets.forEach(function (asset) {
          if (asset.kind !== "crypto") return;
          var row = data[asset.id];
          if (!row || typeof row.usd !== "number") return;
          asset.price = row.usd;
          if (typeof row.usd_24h_change === "number") asset.change_pct = row.usd_24h_change;
          paintPrices(asset);
        });
      } else {
        renderLegacyCrypto(data);
      }
    } catch (err) {
      if (cryptoBox && !cryptoBox.querySelector(".coin")) {
        cryptoBox.innerHTML = '<span class="ticker-status">Prices unavailable right now.</span>';
      }
    }
  }
  if (cryptoIds.length) {
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
      if (section.id === "markets" || section.id === "status" || section.classList.contains("status-card") || section.closest("#status") || section.closest("#markets")) {
        section.hidden = false;
        return;
      }
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
      var target = (active === "Markets" && document.getElementById("markets")) ? document.getElementById("markets") : article;
      if (target && chip.getBoundingClientRect().bottom < (target.getBoundingClientRect().top + 8)) {
        target.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
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
