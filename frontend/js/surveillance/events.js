/* =============================================================================
   FILE:      frontend/js/surveillance/events.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/surveillance/events.js
   PURPOSE:   Renders the recent detections list and posts toasts.
   ============================================================================= */

window.SurvEvents = (function () {
  const recent = [];   // in-memory list
  const MAX = 100;

  function listEl() { return document.getElementById("surveillanceEvents"); }

  function addFromFrame(result) {
    (result.humans || []).forEach((h) => pushEvent("human", h, result.mode));
    (result.animals || []).forEach((a) => pushEvent("animal", a, result.mode));
    render();
  }

  function pushEvent(kind, det, mode) {
    const item = {
      kind, mode,
      class_name: det.class_name,
      confidence: det.confidence,
      time: new Date().toLocaleTimeString(),
    };
    recent.unshift(item);
    if (recent.length > MAX) recent.pop();

    if (kind === "human") Notifications.human(`${det.class_name} (${(det.confidence * 100).toFixed(0)}%)`);
    else                  Notifications.animal(`${det.class_name} (${(det.confidence * 100).toFixed(0)}%)`);
  }

  function render() {
    const el = listEl();
    if (!el) return;
    if (!recent.length) { el.innerHTML = `<div class="event-item">No detections yet.</div>`; return; }
    el.innerHTML = recent.map((e) =>
      `<div class="event-item ${e.kind}">
        <span class="event-class">${e.class_name}</span>
        <span class="event-conf">${(e.confidence * 100).toFixed(0)}%</span>
        <span class="event-time">${e.time} · ${e.mode}</span>
      </div>`).join("");
  }

  async function refreshFromServer() {
    const res = await Utils.api("/api/surveillance/events?limit=50");
    if (!res.ok || !res.data) return;
    const evs = res.data.events || [];
    const el = listEl();
    if (!el) return;
    el.innerHTML = evs.map((e) =>
      `<div class="event-item">
        <span class="event-class">${e.class_name}</span>
        <span class="event-conf">${(e.confidence * 100).toFixed(0)}%</span>
        <span class="event-time">${e.timestamp} · ${e.mode}</span>
      </div>`).join("");
  }

  return { addFromFrame, pushEvent, render, refreshFromServer };
})();
