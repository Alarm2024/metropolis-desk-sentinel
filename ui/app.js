const btn = document.getElementById("evaluate-btn");
const seedInput = document.getElementById("demo-seed");
const statusPill = document.getElementById("status-pill");
const cardPanel = document.getElementById("card-panel");
const emptyState = document.getElementById("empty-state");

const signalBadge = document.getElementById("signal-badge");
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
const reasonsList = document.getElementById("reasons");
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

  if (card.safe_hold) {
    safeHold.classList.remove("hidden");
    refusalPanel.classList.remove("hidden");
    refusalCode.textContent = card.refusal_code || "SAFE_HOLD";
    refusalReason.textContent = card.refusal_reason || "Agent refused directional action.";
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
}

async function runEvaluation() {
  btn.disabled = true;
  setStatus("evaluating", "loading");
  try {
    const seed = seedInput.value.trim() || null;
    const body = seed ? { seed } : {};
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const card = await res.json();
    renderCard(card);
    setStatus("updated", "ok");
  } catch (err) {
    setStatus("error", "err");
    console.error(err);
  } finally {
    btn.disabled = false;
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
    /* first visit — no card yet */
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

btn.addEventListener("click", runEvaluation);
loadLast();
