/* =============================================================================
   FILE:      frontend/js/irrigation/ui.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/irrigation/ui.js
   PURPOSE:   Renders irrigation data into the DOM.
   ============================================================================= */

window.IrrigationUI = (function () {

  function updateStatus(s) {
    const light = document.getElementById("pumpLight");
    const text  = document.getElementById("pumpText");
    if (light) light.className = "pump-light " + (s.pump_status ? "on" : "");
    if (text)  text.textContent = "Pump: " + (s.pump_status ? "ON" : "OFF");

    const batt = document.getElementById("batteryLevel");
    if (batt) {
      const pct = (s.battery_percentage || 0).toFixed(1);
      batt.textContent = pct + "%";
      batt.parentElement.classList.toggle("low", s.battery_percentage < 20);
    }

    const ovr = document.getElementById("overrideBtn");
    if (ovr) ovr.textContent = "Manual Override " + (s.manual_override ? "ON" : "OFF");

    const ai = document.getElementById("aiStatus");
    if (ai) ai.textContent = s.model_accuracy
      ? `Active (${(s.model_accuracy * 100).toFixed(1)}%)`
      : "Training...";

    const sys = document.getElementById("systemStats");
    if (sys) sys.innerHTML = `Database: ${s.database_entries}<br>Battery: ${pct}%`;
  }

  function updateStats(data) {
    if (!data.length) return;
    const latest = data[0];
    const cards = [
      { key: "soil_moisture", label: "Soil",      unit: "m³/m³" },
      { key: "temperature",   label: "Temp",      unit: "°C" },
      { key: "humidity",      label: "Humidity",  unit: "%" },
      { key: "vibration",     label: "Vibration", unit: "g" },
    ];
    const html = cards.map((c) => {
      const v = latest[c.key];
      return `<div class="stat-card">
        <div class="stat-value">${v !== undefined ? Utils.fmtNumber(v) : "--"}</div>
        <div class="stat-label">${c.label} (${c.unit})</div>
      </div>`;
    }).join("");
    const g = document.getElementById("clickableGrid");
    if (g) g.innerHTML = html;
  }

  function updateTable(data) {
    const tb = document.getElementById("tableBody");
    if (!tb) return;
    tb.innerHTML = data.slice(0, 10).map((r) => {
      const isFault = r.vibration_fault && r.vibration_fault !== "Normal";
      return `<tr>
        <td>${Utils.fmtTime(r.timestamp)}</td>
        <td>${Utils.fmtNumber(r.soil_moisture, 3)}</td>
        <td>${Utils.fmtNumber(r.temperature, 1)}</td>
        <td>${Utils.fmtNumber(r.humidity, 1)}</td>
        <td>${Utils.fmtNumber(r.vibration, 3)}</td>
        <td>${Utils.fmtNumber(r.battery, 1)}</td>
        <td>${r.pump_decision === 1 ? "ON" : "OFF"}</td>
        <td>${r.smart_schedule === 1 ? "Yes" : "—"}</td>
        <td>${isFault ? r.vibration_fault : "Normal"}</td>
        <td>${r.is_anomaly ? "Anomaly" : "OK"}</td>
      </tr>`;
    }).join("");
  }

  function updateAnalyticsTable(data) {
    const tb = document.getElementById("analyticsTableBody");
    if (!tb) return;
    tb.innerHTML = data.slice(0, 20).map((r) => {
      const isFault = r.vibration_fault && r.vibration_fault !== "Normal";
      return `<tr>
        <td>${r.timestamp || ""}</td>
        <td>${Utils.fmtNumber(r.soil_moisture, 3)}</td>
        <td>${Utils.fmtNumber(r.temperature, 1)}</td>
        <td>${Utils.fmtNumber(r.humidity, 1)}</td>
        <td>${Utils.fmtNumber(r.vibration, 3)}</td>
        <td>${Utils.fmtNumber(r.battery, 1)}</td>
        <td>${r.pump_decision === 1 ? "ON" : "OFF"}</td>
        <td>${Utils.fmtNumber(r.pump_confidence, 1)}</td>
        <td>${r.smart_schedule === 1 ? "Yes" : "No"}</td>
        <td>${isFault ? r.vibration_fault : "Normal"}</td>
      </tr>`;
    }).join("");
  }

  function updateThresholds(th) {
    const html = Object.entries(th).map(([k, v]) => `
      <div class="threshold-card">
        <div class="param">${k.replace("_", " ").toUpperCase()}</div>
        <div class="vals">Min ${Utils.fmtNumber(v.min, 3)}<br>Max ${Utils.fmtNumber(v.max, 3)}</div>
      </div>`).join("");
    ["thresholdGrid", "dashboardThresholdGrid"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    });
  }

  function updateForecast(f) {
    if (!f || f.error) {
      const html = `<div class="forecast-card">${f?.error || "Waiting for data..."}</div>`;
      ["forecastGrid", "dashboardForecastGrid", "analyticsForecastGrid"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
      });
      return;
    }
    let html = "";
    if (f.soil_forecast) html += forecastCard("Soil Moisture", f.soil_forecast, f.soil_confidence, "m³/m³");
    if (f.temp_forecast) html += forecastCard("Temperature", f.temp_forecast, f.temp_confidence, "°C");
    if (f.hum_forecast)  html += forecastCard("Humidity", f.hum_forecast, f.hum_confidence, "%");
    if (f.irrigation_needed !== undefined) {
      html += `<div class="forecast-card">
        <div class="label">Irrigation Prediction</div>
        <div class="value">${f.irrigation_needed ? "Irrigation needed soon" : "No irrigation needed"}</div>
        ${f.irrigation_time ? `<div class="conf">Expected in ~${f.irrigation_time} hours</div>` : ""}
      </div>`;
    }
    ["forecastGrid", "dashboardForecastGrid", "analyticsForecastGrid"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    });
  }

  function forecastCard(label, arr, conf, unit) {
    const vals = arr.map((v) => Utils.fmtNumber(v, 2)).join(" → ");
    return `<div class="forecast-card">
      <div class="label">${label}</div>
      <div class="value">${vals} ${unit}</div>
      <div class="conf">Confidence: ${Utils.fmtNumber(conf, 1)}%</div>
    </div>`;
  }

  return {
    updateStatus, updateStats, updateTable, updateAnalyticsTable,
    updateThresholds, updateForecast,
  };
})();
