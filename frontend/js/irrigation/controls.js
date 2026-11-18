/* =============================================================================
   FILE:      frontend/js/irrigation/controls.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/irrigation/controls.js
   PURPOSE:   User actions: manual override, retrain, export CSV.
   ============================================================================= */

window.IrrigationControls = (function () {

  function bind() {
    const ovr = document.getElementById("overrideBtn");
    if (ovr) ovr.onclick = toggleOverride;

    const rt = document.getElementById("retrainBtn");
    if (rt) rt.onclick = retrain;

    const ex = document.getElementById("exportBtn");
    if (ex) ex.onclick = () => { window.location.href = "/api/export"; };
  }

  async function toggleOverride() {
    const pwd = prompt("Admin password:");
    if (!pwd) return;
    const res = await Utils.api("/api/manual-override/toggle?password=" + encodeURIComponent(pwd));
    if (res.data && res.data.error) alert(res.data.error);
    IrrigationData.refreshAll();
  }

  async function retrain() {
    const res = await Utils.api("/api/retrain");
    if (res.data && res.data.message) alert(res.data.message);
    IrrigationData.refreshAll();
  }

  return { bind, toggleOverride, retrain };
})();
