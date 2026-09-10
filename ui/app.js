const btn = document.getElementById("evaluate-btn");
const seedInput = document.getElementById("demo-seed");
const statusPill = document.getElementById("status-pill");
const cardPanel = document.getElementById("card-panel");
const emptyState = document.getElementById("empty-state");
const scenarioButtons = document.getElementById("scenario-buttons");
const decisionLog = document.getElementById("decision-log");
const logIntegrity = document.getElementById("log-integrity");

const signalBadge = document.getElementById("signal-badge");
const trustPosture = document.getElementById("trust-posture");
const safeHold = document.getElementById("safe-hold");
const refusalPanel = document.getElementById("refusal-panel");
const refusalCode = document.getElementById("refusal-code");
const refusalReason = document.getElementById("refusal-reason");
const summary = document.getElementById("summary");
const confidence = document.getElementById("confidence");
const schemaVersion = document.getElementById("schema-version");
const agentVersion = document.getElementById("agent-version");
const timestamp = document.getElementById("timestamp");
const metricsSeed = document.getElementById("metrics-seed");
const provenanceStatus = document.getElementById("provenance-status");
const reasonsList = document.getElementById("reasons");
const reasonCodes = document.getElementById("reason-codes");
const provenanceHash = document.getElementById("provenance-hash");
const copyHashBtn = document.getElementById("copy-hash-btn");

function setStatus(text, cls) {
  statusPill.textContent = text;
  statusPill.className = `pill ${cls}`;
}

function renderCard(card) {
  emptyState.classList.add("hidden");
  cardPanel.classList.remove("hidden");

  signalBadge.textContent = card.signal;
  signalBadge.className = `badge ${card.signal}`;

  trustPosture.textContent = card.trust_posture || "—";
  trustPosture.className = `posture ${card.trust_posture || ""}`;

  if (card.safe_hold) {
    safeHold.classList.remove("hidden");
    refusalPanel.classList.remove("hidden");
    refusalCode.textContent = card.refusal_code ?? "—";
    refusalReason.textContent = card.refusal_reason ?? "—";
  } else {
    safeHold.classList.add("hidden");
    refusalPanel.classList.add("hidden");
  }

  summary.textContent = card.summary;
  confidence.textContent = `${(card.confidence * 100).toFixed(1)}%`;
  schemaVersion.textContent = card.schema_version || "—";
  agentVersion.textContent = card.agent_version;
  timestamp.textContent = new Date(card.timestamp_ms).toISOString();
  metricsSeed.textContent = (card.metrics && card.metrics.seed) || "—";
  provenanceHash.textContent = card.provenance_hash;

  reasonsList.innerHTML = "";
  (card.reasons || []).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = r;
    reasonsList.appendChild(li);
  });

  reasonCodes.innerHTML = "";
  (card.reason_codes || []).forEach((c) => {
    const span = document.createElement("span");
    span.className = "chip";
    span.textContent = c;
    reasonCodes.appendChild(span);
  });

  verifyProvenance(card);
}

async function verifyProvenance(card) {
  provenanceStatus.textContent = "checking…";
  provenanceStatus.className = "";
  try {
    const res = await fetch("/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(card),
    });
    const data = await res.json();
    provenanceStatus.textContent = data.valid ? "valid ✓" : "invalid ✗";
    provenanceStatus.className = data.valid ? "ok-text" : "err-text";
  } catch {
    provenanceStatus.textContent = "error";
    provenanceStatus.className = "err-text";
  }
}

async function runEvaluation(body = null) {
  btn.disabled = true;
  setStatus("evaluating", "loading");
  try {
    const payload = body || (seedInput.value.trim() ? { seed: seedInput.value.trim() } : {});
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const card = await res.json();
    renderCard(card);
    setStatus("updated", "ok");
    await loadDecisionLog();
  } catch (err) {
    setStatus("error", "err");
    console.error(err);
  } finally {
    btn.disabled = false;
  }
}

async function runScenario(name) {
  btn.disabled = true;
  setStatus("scenario", "loading");
  try {
    const res = await fetch(`/api/scenarios/${name}/evaluate`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const card = await res.json();
    renderCard(card);
    setStatus(name, "ok");
    await loadDecisionLog();
  } catch (err) {
    setStatus("error", "err");
    console.error(err);
  } finally {
    btn.disabled = false;
  }
}

async function loadScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    if (!res.ok) return;
    const scenarios = await res.json();
    scenarioButtons.innerHTML = "";
    scenarios.forEach((s) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "scenario-btn";
      b.title = s.description;
      b.textContent = s.name.replace(/_/g, " ");
      b.addEventListener("click", () => runScenario(s.name));
      scenarioButtons.appendChild(b);
    });
  } catch {
    /* scenarios optional on first load */
  }
}

async function loadDecisionLog() {
  try {
    const res = await fetch("/api/decisions?limit=8");
    if (!res.ok) return;
    const data = await res.json();
    logIntegrity.textContent = data.integrity_ok ? "chain ok" : "chain broken";
    logIntegrity.className = `pill ${data.integrity_ok ? "ok" : "err"}`;

    decisionLog.innerHTML = "";
    data.entries.slice().reverse().forEach((entry) => {
      const li = document.createElement("li");
      const card = entry.card;
      li.innerHTML = `
        <span class="log-id">#${entry.entry_id}</span>
        <span class="log-signal ${card.signal}">${card.signal}</span>
        <span class="log-meta">${card.refusal_code || card.trust_posture}</span>
        <code class="log-hash">${card.provenance_hash.slice(0, 12)}…</code>
      `;
      decisionLog.appendChild(li);
    });
  } catch {
    /* log panel optional */
  }
}

async function loadLast() {
  try {
    const res = await fetch("/api/last");
    if (!res.ok) return;
    const card = await res.json();
    if (card.signal) {
      renderCard(card);
      setStatus("cached", "ok");
    }
  } catch {
    /* first visit */
  }
}

copyHashBtn.addEventListener("click", async () => {
  const hash = provenanceHash.textContent;
  if (!hash || hash === "—") return;
  try {
    await navigator.clipboard.writeText(hash);
    copyHashBtn.textContent = "Copied";
    setTimeout(() => { copyHashBtn.textContent = "Copy"; }, 1500);
  } catch {
    copyHashBtn.textContent = "Failed";
    setTimeout(() => { copyHashBtn.textContent = "Copy"; }, 1500);
  }
});

btn.addEventListener("click", () => runEvaluation());
loadScenarios();
loadDecisionLog();
loadLast();
