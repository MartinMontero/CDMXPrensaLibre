/* ==========================================================================
   CDMX Prensa Libre — client behaviour
   Self-contained, no dependencies, no network calls, no tracking.
   CSP-safe: all listeners attached here; no inline handlers; no eval.
   The only persistent state is a non-sensitive theme preference.
   ========================================================================== */
(function () {
  "use strict";

  /* ---------- Theme (light / dark / auto) ---------- */
  var THEME_KEY = "cpl-theme";
  var root = document.documentElement;

  function readTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }
  function writeTheme(v) {
    try { if (v) localStorage.setItem(THEME_KEY, v); else localStorage.removeItem(THEME_KEY); }
    catch (e) { /* storage may be blocked; ignore */ }
  }
  function applyTheme(v) {
    if (v === "light" || v === "dark") root.setAttribute("data-theme", v);
    else root.removeAttribute("data-theme");
  }

  var saved = readTheme();
  if (saved) applyTheme(saved);

  function currentEffective() {
    var attr = root.getAttribute("data-theme");
    if (attr) return attr;
    return (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  }

  function initThemeToggle() {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    function label() {
      var eff = currentEffective();
      btn.setAttribute("aria-label", eff === "dark" ? "Cambiar a tema claro / Switch to light theme"
                                                     : "Cambiar a tema oscuro / Switch to dark theme");
      btn.textContent = eff === "dark" ? "☀️" : "🌙";
    }
    label();
    btn.addEventListener("click", function () {
      var next = currentEffective() === "dark" ? "light" : "dark";
      applyTheme(next); writeTheme(next); label();
    });
  }

  /* ---------- Copy to clipboard ---------- */
  function flash(btn, okText) {
    var prev = btn.getAttribute("data-label") || btn.textContent;
    if (!btn.getAttribute("data-label")) btn.setAttribute("data-label", prev);
    btn.classList.add("copied");
    btn.textContent = okText;
    window.setTimeout(function () {
      btn.classList.remove("copied");
      btn.textContent = btn.getAttribute("data-label");
    }, 1800);
  }

  function legacyCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "absolute";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  function doCopy(text, btn) {
    var okText = btn.getAttribute("data-copied") || "¡Copiado! ✓";
    var failText = btn.getAttribute("data-failed") || "Selecciónalo y copia manualmente";
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { flash(btn, okText); },
        function () { if (legacyCopy(text)) flash(btn, okText); else flash(btn, failText); });
    } else {
      if (legacyCopy(text)) flash(btn, okText); else flash(btn, failText);
    }
  }

  function initCopyButtons() {
    var btns = document.querySelectorAll("[data-copy-target]");
    Array.prototype.forEach.call(btns, function (btn) {
      btn.addEventListener("click", function () {
        var sel = btn.getAttribute("data-copy-target");
        var el = sel ? document.getElementById(sel) : null;
        if (!el) return;
        var text = (el.value !== undefined && el.tagName === "TEXTAREA") ? el.value : el.textContent;
        doCopy(text, btn);
      });
    });
    // Inline command snippets: copy the sibling <code> text
    var cmdBtns = document.querySelectorAll("[data-copy-prev]");
    Array.prototype.forEach.call(cmdBtns, function (btn) {
      btn.addEventListener("click", function () {
        var code = btn.parentNode.querySelector("code");
        if (code) doCopy(code.textContent, btn);
      });
    });
  }

  /* ---------- Mobile menu ---------- */
  function initMenu() {
    var toggle = document.getElementById("menu-toggle");
    var sidebar = document.getElementById("sidebar");
    if (!toggle || !sidebar) return;
    toggle.addEventListener("click", function () {
      var open = sidebar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close after navigating on mobile
    sidebar.addEventListener("click", function (e) {
      if (e.target && e.target.tagName === "A" && window.matchMedia("(max-width: 900px)").matches) {
        sidebar.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- Active section in TOC ---------- */
  function initScrollSpy() {
    var links = document.querySelectorAll("#sidebar a[href^='#']");
    if (!links.length || !("IntersectionObserver" in window)) return;
    var map = {};
    Array.prototype.forEach.call(links, function (a) {
      var id = a.getAttribute("href").slice(1);
      if (id) map[id] = a;
    });
    var visible = {};
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting ? en.intersectionRatio : 0; });
      var bestId = null, bestRatio = 0;
      Object.keys(visible).forEach(function (id) {
        if (visible[id] > bestRatio) { bestRatio = visible[id]; bestId = id; }
      });
      if (bestId) {
        Array.prototype.forEach.call(links, function (a) { a.classList.remove("active"); });
        if (map[bestId]) map[bestId].classList.add("active");
      }
    }, { rootMargin: "-70px 0px -55% 0px", threshold: [0, 0.25, 0.5, 1] });
    Object.keys(map).forEach(function (id) {
      var sec = document.getElementById(id);
      if (sec) obs.observe(sec);
    });
  }

  /* ---------- Back to top ---------- */
  function initToTop() {
    var btn = document.getElementById("to-top");
    if (!btn) return;
    function onScroll() {
      if (window.scrollY > 600) btn.classList.add("show"); else btn.classList.remove("show");
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: (window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth") });
    });
    onScroll();
  }

  /* ---------- Print ---------- */
  function initPrint() {
    var btns = document.querySelectorAll("[data-print]");
    Array.prototype.forEach.call(btns, function (btn) {
      btn.addEventListener("click", function () { window.print(); });
    });
  }

  /* ---------- Boot ---------- */
  function boot() {
    initThemeToggle();
    initCopyButtons();
    initMenu();
    initScrollSpy();
    initToTop();
    initPrint();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
