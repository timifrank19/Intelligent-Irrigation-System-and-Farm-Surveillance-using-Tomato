/* =============================================================================
   FILE:      frontend/js/tomato/results.js
   LOCATION:  Intelligent_Tomato_Farm/frontend/js/tomato/results.js
   PURPOSE:   Renders the final disease decision, distribution, and the
              recommendation box. Also loads the recent results table.
   ============================================================================= */

window.TomatoResults = (function () {
  let currentId = null;

  async function load(resultId) {
    const res = await Utils.api("/api/tomato/results/" + resultId);
    if (!res.ok || !res.data) { Notifications.error("Result not found"); return; }
    currentId = resultId;
    render(res.data);
    TomatoEvidence.render(res.data);
    renderRecommendation(res.data.recommendation_text);
  }

  function render(row) {
    const el = document.getElementById("latestResult");
    if (!el) return;
    const primary = row.supervisor_primary || "—";
    const conf = Utils.fmtNumber(row.supervisor_confidence, 3);
    const uncertain = row.supervisor_uncertain === 1 || row.supervisor_uncertain === true;
    const cls = uncertain ? "uncertain"
              : (String(primary).toLowerCase().includes("healthy") ? "healthy" : "diseased");

    let top3 = [];
    try { top3 = JSON.parse(row.supervisor_top3_json || "[]"); } catch (e) {}

    const dist = top3.map(([name, prob]) =>
      `<div class="row"><span>${name}</span>
         <div class="bar"><span style="width:${(prob * 100).toFixed(1)}%"></span></div>
         <span>${(prob * 100).toFixed(1)}%</span></div>`
    ).join("");

    el.className = "result-card " + cls;
    el.innerHTML = `
      <div>Final decision</div>
      <div class="decision">${primary}</div>
      <div class="conf">Confidence: ${conf}${uncertain ? " · uncertain" : ""}</div>
      ${dist ? `<div class="distribution">${dist}</div>` : ""}
    `;
  }

  function renderRecommendation(text) {
    const el = document.getElementById("recommendationBox");
    if (el) el.textContent = text || "—";
  }

  async function refreshList() {
    const res = await Utils.api("/api/tomato/results?limit=30");
    const tb = document.getElementById("resultsTableBody");
    if (!tb || !res.ok || !res.data) return;
    const rows = res.data.results || [];
    tb.innerHTML = rows.map((r) => `
      <tr>
        <td>${r.timestamp}</td>
        <td>${r.source_type}</td>
        <td>${r.yolo_class}</td>
        <td>${Utils.fmtNumber(r.yolo_confidence, 3)}</td>
        <td>${r.supervisor_primary}</td>
        <td>${r.supervisor_uncertain === 1 ? "yes" : "no"}</td>
        <td>${(r.recommendation_text || "").slice(0, 60)}…</td>
      </tr>`).join("");
  }

  async function confirm(isCorrect) {
    if (!currentId) { Notifications.warning("No result loaded"); return; }
    const fd = new FormData();
    fd.append("is_correct", isCorrect ? "true" : "false");
    if (!isCorrect) {
      const t = prompt("Enter the correct class (or leave blank for unsure):");
      if (t) fd.append("true_class", t);
    }
    const res = await Utils.postForm("/api/tomato/confirm/" + currentId, fd);
    const st = document.getElementById("confirmStatus");
    if (res.ok) { st.textContent = "Saved."; Notifications.success("Confirmation saved"); }
    else        { st.textContent = "Failed."; }
    refreshList();
  }

  return { load, render, renderRecommendation, refreshList, confirm };
})();
