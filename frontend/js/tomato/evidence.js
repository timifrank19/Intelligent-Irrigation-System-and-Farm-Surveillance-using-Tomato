/* =============================================================================
   FILE:      frontend/js/tomato/evidence.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/tomato/evidence.js
   PURPOSE:   Renders the four independent evidence cards (YOLO, HSV,
              K-means, Edge) in the Disease Results tab.
   ============================================================================= */

window.TomatoEvidence = (function () {

  function render(data) {
    const el = document.getElementById("evidenceContainer");
    if (!el) return;
    if (!data) { el.innerHTML = ""; return; }

    el.innerHTML = "";
    el.appendChild(card("yolo", "YOLOv8", {
      class: data.yolo_class,
      confidence: Utils.fmtNumber(data.yolo_confidence, 3),
      bbox: (data.yolo_bbox || []).map((v) => Math.round(v)).join(", "),
    }));

    if (data.hsv) el.appendChild(card("hsv", "HSV", {
      green_pct: Utils.fmtNumber(data.hsv.green_pct, 1) + "%",
      yellow_pct: Utils.fmtNumber(data.hsv.yellow_pct, 1) + "%",
      brown_pct: Utils.fmtNumber(data.hsv.brown_pct, 1) + "%",
      dark_pct: Utils.fmtNumber(data.hsv.dark_pct, 1) + "%",
      abnormal_pct: Utils.fmtNumber(data.hsv.abnormal_pct, 1) + "%",
    }));

    if (data.kmeans) el.appendChild(card("kmeans", "K-means", {
      n_clusters: data.kmeans.n_clusters,
      dominant_ratio: Utils.fmtNumber(data.kmeans.dominant_cluster_ratio, 3),
      dark_ratio: Utils.fmtNumber(data.kmeans.dark_cluster_ratio, 3),
      green_ratio: Utils.fmtNumber(data.kmeans.green_cluster_ratio, 3),
    }));

    if (data.edge) el.appendChild(card("edge", "Edge", {
      edge_density: Utils.fmtNumber(data.edge.edge_density, 4),
      lesion_count: data.edge.lesion_count,
      mean_edge_length: Utils.fmtNumber(data.edge.mean_edge_length, 2),
      laplacian_variance: Utils.fmtNumber(data.edge.laplacian_variance, 2),
    }));
  }

  function card(kind, title, kvs) {
    const div = document.createElement("div");
    div.className = "evidence-card " + kind;
    const rows = Object.entries(kvs).map(([k, v]) =>
      `<div class="kv"><span class="k">${k}</span><span class="v">${v}</span></div>`
    ).join("");
    div.innerHTML = `<h4>${title}</h4>${rows}`;
    return div;
  }

  return { render };
})();
