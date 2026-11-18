/* =============================================================================
   FILE:      frontend/js/surveillance/video.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/surveillance/video.js
   PURPOSE:   Opens the browser camera (video only, no audio), and posts
              frames to /api/surveillance/frame at a fixed cadence.
   ============================================================================= */

window.SurvVideo = (function () {
  let stream = null;
  let frameTimer = null;
  let running = false;
  let frameCounter = 0;

  function videoEl() { return document.getElementById("surveillanceVideo"); }

  async function start() {
    if (running) return true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
    } catch (e) {
      alert("Camera access failed: " + e.message);
      return false;
    }
    const v = videoEl();
    if (!v) return false;
    v.srcObject = stream;
    await v.play().catch(() => {});
    running = true;
    SurvOverlay.attach();
    startFrameLoop();
    return true;
  }

  function stop() {
    running = false;
    if (frameTimer) { clearInterval(frameTimer); frameTimer = null; }
    if (stream) { stream.getTracks().forEach((t) => t.stop()); stream = null; }
    const v = videoEl();
    if (v) v.srcObject = null;
    SurvOverlay.clear();
  }

  function startFrameLoop() {
    if (frameTimer) clearInterval(frameTimer);
    frameTimer = setInterval(captureAndSend, APP_CONFIG.SURVEILLANCE_FRAME_INTERVAL_MS);
  }

  async function captureAndSend() {
    if (!running) return;
    const v = videoEl();
    if (!v || v.videoWidth === 0) return;

    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(v, 0, 0);

    const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.75));
    if (!blob) return;

    const fd = new FormData();
    fd.append("file", blob, "frame.jpg");
    fd.append("mode", SurvMode.get());
    frameCounter++;

    const res = await Utils.postForm("/api/surveillance/frame", fd);
    if (res.ok && res.data) {
      SurvOverlay.draw(res.data);
      SurvEvents.addFromFrame(res.data);
    }
  }

  function isRunning() { return running; }
  function getFrameCount() { return frameCounter; }

  return { start, stop, isRunning, getFrameCount };
})();
