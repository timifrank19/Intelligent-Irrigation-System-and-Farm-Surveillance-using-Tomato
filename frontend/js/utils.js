/* =============================================================================
   FILE:      frontend/js/utils.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/utils.js
   PURPOSE:   Shared helpers: fetch wrapper, formatters, DOM helpers.
   ============================================================================= */

window.Utils = (function () {
  function adminKey() {
    return localStorage.getItem(APP_CONFIG.ADMIN_STORAGE_KEY) || "";
  }

  async function api(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const key = adminKey();
    if (key) headers["X-Admin-Key"] = key;
    const opts = Object.assign({}, options, { headers });
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { /* not JSON */ }
    return { ok: res.ok, status: res.status, data };
  }

  async function postForm(path, formData) {
    const headers = {};
    const key = adminKey();
    if (key) headers["X-Admin-Key"] = key;
    const res = await fetch(path, { method: "POST", headers, body: formData });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    return { ok: res.ok, status: res.status, data };
  }

  function fmtTime(ts) {
    if (!ts) return "--";
    return String(ts).slice(-8);
  }

  function fmtNumber(v, digits = 2) {
    if (v === null || v === undefined || isNaN(v)) return "--";
    return Number(v).toFixed(digits);
  }

  function fmtBytes(n) {
    if (!n) return "0 B";
    if (n > 1024 * 1024) return (n / (1024 * 1024)).toFixed(2) + " MB";
    if (n > 1024) return (n / 1024).toFixed(1) + " KB";
    return n + " B";
  }

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  return { api, postForm, adminKey, fmtTime, fmtNumber, fmtBytes, el };
})();
