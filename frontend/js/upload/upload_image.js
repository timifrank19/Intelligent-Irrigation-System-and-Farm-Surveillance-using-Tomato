/* =============================================================================
   FILE:      frontend/js/upload/upload_image.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/upload/upload_image.js
   PURPOSE:   Image upload → instant tomato detection (~1 min).
   ============================================================================= */

window.UploadImage = (function () {

  function bind() {
    const btn = document.getElementById("imageAnalyzeBtn");
    if (btn) btn.onclick = analyze;
  }

  async function analyze() {
    const input = document.getElementById("imageUpload");
    const status = document.getElementById("imageStatus");
    if (!input || !input.files.length) { status.textContent = "Select an image first."; return; }

    status.textContent = "Analyzing...";
    const fd = new FormData();
    fd.append("file", input.files[0]);

    const res = await Utils.postForm("/api/tomato/image", fd);
    if (!res.ok) {
      status.textContent = "Failed (" + res.status + ")";
      Notifications.error("Image analysis failed");
      return;
    }
    if (res.data.found === false) {
      status.textContent = "No tomato detected.";
      return;
    }
    status.textContent = "Done. Result id: " + res.data.result_id;
    Notifications.success("Analysis complete");

    // Load the result into the Disease Results tab and switch there.
    TomatoResults.load(res.data.result_id);
    MainApp.showPage("results");
  }

  return { bind };
})();
