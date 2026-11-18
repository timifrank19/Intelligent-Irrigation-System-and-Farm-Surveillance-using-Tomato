/* =============================================================================
   FILE:      frontend/js/tomato/async_job.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/tomato/async_job.js
   PURPOSE:   Polls /api/tomato/job/{id} until the video analysis finishes,
              then loads the result into the Disease Results tab.
   ============================================================================= */

window.TomatoAsyncJob = (function () {

  function watch(jobId, statusEl) {
    let stopped = false;

    async function poll() {
      if (stopped) return;
      const res = await Utils.api("/api/tomato/job/" + jobId);
      if (!res.ok || !res.data) {
        if (statusEl) statusEl.textContent = "Job not found";
        return;
      }
      const j = res.data;
      if (statusEl) statusEl.textContent = `Job ${j.status} — ${Math.round((j.progress || 0) * 100)}%`;

      if (j.status === "done") {
        if (j.result_id) {
          Notifications.success("Video analysis complete");
          TomatoResults.load(j.result_id);
          MainApp.showPage("results");
        } else {
          Notifications.warning("Video analysis finished with no detections");
        }
        return;
      }
      if (j.status === "failed") {
        Notifications.error("Video analysis failed: " + (j.error || "unknown"));
        return;
      }
      setTimeout(poll, 4000);
    }

    poll();
    return { stop: () => { stopped = true; } };
  }

  return { watch };
})();
