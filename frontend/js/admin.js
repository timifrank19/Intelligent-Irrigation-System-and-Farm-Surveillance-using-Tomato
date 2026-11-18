/* =============================================================================
   FILE:      frontend/js/admin.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/admin.js
   PURPOSE:   Admin gate. Password stored in localStorage (persists across
              reloads). Every protected request sends X-Admin-Key.
              Clicking a locked tab opens the gate.
   ============================================================================= */

window.Admin = (function () {
  function isLoggedIn() {
    return !!localStorage.getItem(APP_CONFIG.ADMIN_STORAGE_KEY);
  }

  function getKey() {
    return localStorage.getItem(APP_CONFIG.ADMIN_STORAGE_KEY) || "";
  }

  function saveKey(key) {
    localStorage.setItem(APP_CONFIG.ADMIN_STORAGE_KEY, key);
  }

  function logout() {
    localStorage.removeItem(APP_CONFIG.ADMIN_STORAGE_KEY);
    location.reload();
  }

  function openGate(onSuccess) {
    const gate = document.getElementById("adminGate");
    const input = document.getElementById("adminPassword");
    const btn = document.getElementById("adminLoginBtn");
    const err = document.getElementById("adminError");
    err.textContent = "";
    input.value = "";
    gate.style.display = "flex";
    setTimeout(() => input.focus(), 100);

    const submit = () => {
      const val = input.value.trim();
      if (!val) { err.textContent = "Enter the password"; return; }
      // Store first; the next protected call validates against the backend.
      saveKey(val);
      gate.style.display = "none";
      if (typeof onSuccess === "function") onSuccess();
    };
    btn.onclick = submit;
    input.onkeydown = (e) => { if (e.key === "Enter") submit(); };
  }

  function requireAdmin(onSuccess) {
    if (isLoggedIn()) { onSuccess(); return; }
    openGate(onSuccess);
  }

  function updateLogoutButton() {
    const b = document.getElementById("logoutBtn");
    if (!b) return;
    b.style.display = isLoggedIn() ? "inline-block" : "none";
    b.onclick = logout;
  }

  return { isLoggedIn, getKey, saveKey, logout, openGate, requireAdmin, updateLogoutButton };
})();
