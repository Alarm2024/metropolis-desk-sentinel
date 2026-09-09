const btn = document.getElementById("evaluate-btn");
const statusPill = document.getElementById("status-pill");
const cardPanel = document.getElementById("card-panel");
const emptyState = document.getElementById("empty-state");

const signalBadge = document.getElementById("signal-badge");
const safeHold = document.getElementById("safe-hold");
const summary = document.getElementById("summary");
const confidence = document.getElementById("confidence");
const agentVersion = document.getElementById("agent-version");
const timestamp = document.getElementById("timestamp");
const reasonsList = document.getElementById("reasons");
const provenanceHash = document.getElementById("provenance-hash");

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
  } else {
    safeHold.classList.add("hidden");
  }

  summary.textContent = card.summary;
  confidence.textContent = `${(card.confidence * 100).toFixed(1)}%`;
  agentVersion.textContent = card.agent_version;
  timestamp.textContent = new Date(card.timestamp_ms).toISOString();
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
    const res = await fetch("/api/evaluate", { method: "POST" });
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

btn.addEventListener("click", runEvaluation);
loadLast();
