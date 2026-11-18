/* =============================================================================
   FILE:      frontend/js/upload/upload_library.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/upload/upload_library.js
   PURPOSE:   Lets the admin send a stored surveillance recording to the
              tomato analysis pipeline.
   ============================================================================= */

window.UploadLibrary = (function () {

  function bind() {
    const btn = document.getElementById("libraryAnalyzeBtn");
    if (btn) btn.onclick = analyze;
  }

  async function refreshList() {
    const sel = document.getElementById("recordingSelect");
    if (!sel) return;
    const res = await Utils.api("/api/surveillance/recordings");
    if (!res.ok || !res.data) return;
    sel.innerHTML = "";
    (res.data.recordings || []).forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r.id;
      opt.textContent = `#${r.id} · ${r.timestamp} · ${r.event_count} events`;
      sel.appendChild(opt);
    });
    if (!sel.options.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No recordings available";
      sel.appendChild(opt);
    }
  }

  async function analyze() {
    const sel = document.getElementById("recordingSelect");
    const status = document.getElementById("libraryStatus");
    if (!sel || !sel.value) { status.textContent = "Select a recording."; return; }
    status.textContent = "Queued...";
    const fd = new FormData();
    // backend reads no body; still sends an empty multipart to satisfy auth-less POST
    const res = await Utils.postForm("/api/tomato/analyze_recording/" + sel.value, fd);
    if (!res.ok || !res.data.job_id) {
      status.textContent = "Failed (" + res.status + ")";
      return;
    }
    status.textContent = "Job: " + res.data.job_id;
    TomatoAsyncJob.watch(res.data.job_id, status);
  }

  return { bind, refreshList };
})();
