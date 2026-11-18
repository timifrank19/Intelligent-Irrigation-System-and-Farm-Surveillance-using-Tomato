/* =============================================================================
   FILE:      frontend/js/surveillance/overlay.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/surveillance/overlay.js
   PURPOSE:   Draws human/animal bounding boxes on the surveillance video.
   ============================================================================= */

window.SurvOverlay = (function () {
  let canvas = null;
  let ctx = null;

  function attach() {
    canvas = document.getElementById("surveillanceOverlay");
    if (!canvas) return;
    const v = document.getElementById("surveillanceVideo");
    if (v) {
      canvas.width = v.videoWidth || 640;
      canvas.height = v.videoHeight || 480;
    }
    ctx = canvas.getContext("2d");
  }

  function clear() {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function draw(result) {
    if (!ctx || !canvas) return;
    clear();
    const v = document.getElementById("surveillanceVideo");
    if (v && (canvas.width !== v.videoWidth || canvas.height !== v.videoHeight)) {
      canvas.width = v.videoWidth || canvas.width;
      canvas.height = v.videoHeight || canvas.height;
    }

    const sx = canvas.width / (canvas.width || 1);
    const sy = canvas.height / (canvas.height || 1);

    (result.humans || []).forEach((h) => drawBox(h, "#3498db", sx, sy));
    (result.animals || []).forEach((a) => drawBox(a, "#9b59b6", sx, sy));
  }

  function drawBox(det, color, sx, sy) {
    const b = det.bbox;
    if (!b || b.length < 4) return;
    const [x1, y1, x2, y2] = b;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x1 * sx, y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy);

    const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
    ctx.font = "14px sans-serif";
    const tw = ctx.measureText(label).width + 10;
    ctx.fillStyle = color;
    ctx.fillRect(x1 * sx, y1 * sy - 20, tw, 20);
    ctx.fillStyle = "#fff";
    ctx.fillText(label, x1 * sx + 5, y1 * sy - 6);
  }

  return { attach, clear, draw };
})();
