/* =============================================================================
   FILE:      frontend/js/irrigation/data.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/irrigation/data.js
   PURPOSE:   Fetches irrigation endpoints and forwards to the UI module.
   ============================================================================= */

window.IrrigationData = (function () {
  let current = [];

  async function refreshAll() {
    try {
      const [recent, status, thresholds, forecast] = await Promise.all([
        Utils.api("/api/recent?limit=30"),
        Utils.api("/api/status"),
        Utils.api("/api/thresholds"),
        Utils.api("/api/forecast"),
      ]);
      if (recent.ok && Array.isArray(recent.data)) {
        current = recent.data;
        IrrigationUI.updateStats(current);
        IrrigationUI.updateTable(current);
        IrrigationUI.updateAnalyticsTable(current);
        IrrigationCharts.update(current);
      }
      if (status.ok) IrrigationUI.updateStatus(status.data);
      if (thresholds.ok) IrrigationUI.updateThresholds(thresholds.data);
      if (forecast.ok) IrrigationUI.updateForecast(forecast.data);
    } catch (e) {
      console.error("Irrigation refresh failed", e);
    }
  }

  function getRecent() { return current; }
  return { refreshAll, getRecent };
})();
