/* =============================================================================
   FILE:      frontend/js/upload/upload_video.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/upload/upload_video.js
   PURPOSE:   Video upload → async job (5-10 min). Polls for status and
              pushes the result to the Disease Results tab.
   ============================================================================= */

window.UploadVideo = (function () {

  function bind() {
    const btn = document.getElementById("videoAnalyzeBtn");
    if (btn) btn.onclick = analyze;
  }

  async function analyze() {
    const input = document.getElementById("videoUpload");
    const status = document.getElementById("videoStatus");
    if (!input || !input.files.length) { status.textContent = "Select a video first."; return; }

    status.textContent = "Uploading...";
    const fd = new FormData();
    fd.append("file", input.files[0]);

    const res = await Utils.postForm("/api/tomato/video", fd);
    if (!res.ok || !res.data.job_id) {
      status.textContent = "Failed (" + res.status + ")";
      Notifications.error("Video upload failed");
      return;
    }
    status.textContent = "Queued. Job: " + res.data.job_id;
    TomatoAsyncJob.watch(res.data.job_id, status);
  }

  return { bind };
})();
