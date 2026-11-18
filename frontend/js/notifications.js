/* =============================================================================
   FILE:      frontend/js/notifications.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/notifications.js
   PURPOSE:   Toast notification system shared by every tab.
              Uses CSS classes: .toast, .human, .animal, .disease, .warning, .success
   ============================================================================= */

window.Notifications = (function () {
  const container = () => document.getElementById("notifications");

  function show(title, message = "", kind = "success", timeout = 5000) {
    const c = container();
    if (!c) return;
    const div = Utils.el("div", "toast " + kind);
    div.innerHTML =
      `<div class="title">${title}</div>` +
      (message ? `<div>${message}</div>` : "") +
      `<div class="time">${new Date().toLocaleTimeString()}</div>`;
    c.appendChild(div);
    setTimeout(() => {
      div.classList.add("leaving");
      setTimeout(() => div.remove(), 350);
    }, timeout);
  }

  function human(msg)   { show("Human detected", msg, "human"); }
  function animal(msg)  { show("Animal detected", msg, "animal"); }
  function disease(msg) { show("Tomato disease", msg, "disease", 8000); }
  function warning(msg) { show("Notice", msg, "warning", 8000); }
  function success(msg) { show("Done", msg, "success"); }
  function error(msg)   { show("Error", msg, "disease"); }

  return { show, human, animal, disease, warning, success, error };
})();
