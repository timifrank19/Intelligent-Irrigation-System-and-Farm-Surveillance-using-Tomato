/* =============================================================================
   FILE:      frontend/js/main.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/main.js
   PURPOSE:   App bootstrap. Wires navigation, tabs, WebSocket handlers,
              button bindings, and periodic refresh. Loaded last.
   ============================================================================= */

window.MainApp = (function () {
  let currentPage = "home";

  function showPage(name) {
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
    const el = document.getElementById(name + "-page");
    if (el) el.classList.add("active");
    document.querySelectorAll(".nav-btn").forEach((b) =>
      b.classList.toggle("active", b.dataset.page === name));
    currentPage = name;

    if (name === "upload") UploadLibrary.refreshList();
    if (name === "results") TomatoResults.refreshList();
    if (name === "surveillance") SurvEvents.refreshFromServer();
  }

  function bindNavigation() {
    document.querySelectorAll(".nav-btn[data-page]").forEach((b) => {
      b.addEventListener("click", () => {
        const page = b.dataset.page;
        const gated = b.classList.contains("admin-gated");
        if (gated) {
          Admin.requireAdmin(() => showPage(page));
        } else {
          showPage(page);
        }
      });
    });
  }

  function bindSurveillanceControls() {
    const startCam = document.getElementById("startCamBtn");
    const stopCam  = document.getElementById("stopCamBtn");
    const startRec = document.getElementById("startRecBtn");
    const stopRec  = document.getElementById("stopRecBtn");

    if (startCam) startCam.onclick = async () => {
      const ok = await SurvVideo.start();
      if (ok) { startCam.disabled = true; stopCam.disabled = false;
                startRec.disabled = false; }
    };
    if (stopCam) stopCam.onclick = () => {
      SurvRecorder.stop();
      SurvVideo.stop();
      startCam.disabled = false; stopCam.disabled = true;
      startRec.disabled = true;  stopRec.disabled = true;
    };
    if (startRec) startRec.onclick = () => {
      SurvRecorder.start();
      startRec.disabled = true; stopRec.disabled = false;
    };
    if (stopRec) stopRec.onclick = () => {
      SurvRecorder.stop();
      startRec.disabled = false; stopRec.disabled = true;
    };
  }

  function bindResultsConfirm() {
    const y = document.getElementById("confirmYes");
    const n = document.getElementById("confirmNo");
    if (y) y.onclick = () => TomatoResults.confirm(true);
    if (n) n.onclick = () => TomatoResults.confirm(false);
  }

  function bindWebSocket() {
    WS.register("human_detected", (msg) => {
      // Already shown by the frame loop; ignore duplicates quietly.
    });
    WS.register("animal_detected", () => {});
    WS.register("disease_result", (msg) => {
      Notifications.disease("New tomato disease result available");
    });
    WS.register("recording_warning", (msg) => {
      Notifications.warning(msg.message || ("Recording " + msg.recording_id + " will be deleted soon"));
    });
    WS.register("recording_deleted", (msg) => {
      Notifications.warning("Recording " + msg.recording_id + " deleted");
      UploadLibrary.refreshList();
    });
    WS.register("manual", (msg) => Notifications.show("Irrigation", msg.message, "success"));
    WS.start();
  }

  async function safe() {
    IrrigationCharts.init();
    bindNavigation();
    bindSurveillanceControls();
    bindResultsConfirm();
    SurvMode.bind();
    UploadImage.bind();
    UploadVideo.bind();
    UploadLibrary.bind();
    IrrigationControls.bind();
    Admin.updateLogoutButton();
    bindWebSocket();

    await IrrigationData.refreshAll();
    setInterval(IrrigationData.refreshAll, APP_CONFIG.REFRESH_INTERVAL_MS);

    showPage("home");
  }

  return { safe, showPage, getCurrentPage: () => currentPage };
})();

document.addEventListener("DOMContentLoaded", MainApp.safe);
