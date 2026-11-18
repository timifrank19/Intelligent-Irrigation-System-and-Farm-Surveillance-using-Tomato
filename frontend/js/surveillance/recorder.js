/* =============================================================================
   FILE:      frontend/js/surveillance/recorder.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/surveillance/recorder.js
   PURPOSE:   Records the camera stream in 5-minute chunks (video only, NO
              audio), and uploads each chunk when it closes. The backend
              keeps the chunk only if it contains detections.
   ============================================================================= */

window.SurvRecorder = (function () {
  let recorder = null;
  let chunks = [];
  let chunkTimer = null;
  let recording = false;

  function indicator() { return document.getElementById("recIndicator"); }

  function start() {
    if (recording) return;
    const v = document.getElementById("surveillanceVideo");
    if (!v || !v.srcObject) { alert("Start the camera first"); return; }

    chunks = [];
    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp8")
      ? "video/webm;codecs=vp8" : "video/webm";

    // Extract ONLY the video track — no audio.
    const videoTrack = v.srcObject.getVideoTracks()[0];
    const videoOnly = new MediaStream([videoTrack]);

    recorder = new MediaRecorder(videoOnly, { mimeType: mime });
    recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = uploadCurrentChunk;
    recorder.start(1000);

    recording = true;
    indicator().style.display = "block";

    // Roll into a new chunk every 5 minutes.
    chunkTimer = setInterval(() => {
      if (recorder && recorder.state === "recording") {
        recorder.stop();                     // triggers onstop → upload
        chunks = [];
        const t = new MediaStream([videoTrack.clone()]);
        recorder = new MediaRecorder(t, { mimeType: mime });
        recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
        recorder.onstop = uploadCurrentChunk;
        recorder.start(1000);
      }
    }, APP_CONFIG.SURVEILLANCE_CHUNK_MS);
  }

  async function stop() {
    if (!recording) return;
    recording = false;
    if (chunkTimer) { clearInterval(chunkTimer); chunkTimer = null; }
    if (recorder && recorder.state !== "inactive") recorder.stop();
    indicator().style.display = "none";
  }

  async function uploadCurrentChunk() {
    if (!chunks.length) return;
    const blob = new Blob(chunks, { type: "video/webm" });
    const frameCount = SurvVideo.getFrameCount();

    const fd = new FormData();
    fd.append("file", blob, `chunk_${Date.now()}.webm`);
    fd.append("duration_sec", String(APP_CONFIG.SURVEILLANCE_CHUNK_MS / 1000));
    fd.append("mode", SurvMode.get());
    // event_count is approximated from recent in-memory events; backend can
    // re-check if needed. The backend still enforces its own rule.
    fd.append("event_count", String(SurvEvents._count ? SurvEvents._count() : 0));

    const res = await Utils.postForm("/api/surveillance/recordings", fd);
    if (res.ok && res.data) {
      if (res.data.kept) Notifications.success("Recording kept (id " + res.data.recording_id + ")");
      else               Notifications.warning("Recording discarded (no detections)");
    }
  }

  function isRecording() { return recording; }
  return { start, stop, isRecording };
})();
