/* =============================================================================
   FILE:      frontend/js/surveillance/mode.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/surveillance/mode.js
   PURPOSE:   Day / Night / Auto mode selection for the surveillance page.
   ============================================================================= */

window.SurvMode = (function () {
  let current = "auto";

  function bind() {
    document.querySelectorAll(".mode-btn").forEach((b) => {
      b.onclick = () => {
        document.querySelectorAll(".mode-btn").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        current = b.dataset.mode;
      };
    });
  }

  function get() { return current; }
  function set(m) { current = m; }

  return { bind, get, set };
})();
