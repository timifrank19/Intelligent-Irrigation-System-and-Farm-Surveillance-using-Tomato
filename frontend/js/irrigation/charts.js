/* =============================================================================
   FILE:      frontend/js/irrigation/charts.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/irrigation/charts.js
   PURPOSE:   Chart.js setup for the irrigation dashboard.
   ============================================================================= */

window.IrrigationCharts = (function () {
  let mainChart = null;
  let dashChart = null;

  function init() {
    const c1 = document.getElementById("mainChart");
    if (c1) {
      mainChart = new Chart(c1.getContext("2d"), {
        type: "line",
        data: {
          labels: [],
          datasets: [
            { label: "Soil",       data: [], borderColor: "#2ecc71", backgroundColor: "rgba(46,204,113,0.15)", tension: 0.4 },
            { label: "Temp",       data: [], borderColor: "#e74c3c", backgroundColor: "rgba(231,76,60,0.15)",  tension: 0.4 },
            { label: "Humidity",   data: [], borderColor: "#3498db", backgroundColor: "rgba(52,152,219,0.15)", tension: 0.4 },
            { label: "Vibration",  data: [], borderColor: "#9b59b6", backgroundColor: "rgba(155,89,182,0.15)", tension: 0.4 },
          ],
        },
        options: { responsive: true, maintainAspectRatio: false,
                   interaction: { mode: "index", intersect: false } },
      });
    }

    const c2 = document.getElementById("dashboardChart");
    if (c2) {
      dashChart = new Chart(c2.getContext("2d"), {
        type: "line",
        data: { labels: [], datasets: [
          { label: "Soil Moisture", data: [], borderColor: "#2ecc71",
            backgroundColor: "rgba(46,204,113,0.15)", tension: 0.4 } ] },
        options: { responsive: true, maintainAspectRatio: false },
      });
    }
  }

  function update(data) {
    if (!mainChart && !dashChart) return;
    const rev = data.slice().reverse();
    const labels = rev.map((r) => Utils.fmtTime(r.timestamp));
    const soil = rev.map((r) => r.soil_moisture || 0);
    const temp = rev.map((r) => r.temperature || 0);
    const hum = rev.map((r) => r.humidity || 0);
    const vib = rev.map((r) => r.vibration || 0);

    if (mainChart) {
      mainChart.data.labels = labels;
      mainChart.data.datasets[0].data = soil;
      mainChart.data.datasets[1].data = temp;
      mainChart.data.datasets[2].data = hum;
      mainChart.data.datasets[3].data = vib;
      mainChart.update("none");
    }
    if (dashChart) {
      dashChart.data.labels = labels;
      dashChart.data.datasets[0].data = soil;
      dashChart.update("none");
    }
  }

  return { init, update };
})();
