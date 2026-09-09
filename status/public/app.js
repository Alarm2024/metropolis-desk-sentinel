async function loadCard() {
  const loading = document.getElementById("loading");
  const view = document.getElementById("card-view");
  const empty = document.getElementById("empty");

  try {
    const res = await fetch("/api/card");
    if (!res.ok) throw new Error("no card");

    const card = await res.json();
    loading.hidden = true;
    view.hidden = false;

    const action = card.signal.action;
    const banner = document.getElementById("signal-action");
    banner.textContent = action;
    banner.className = "signal-banner " + action.replace(/\s+/g, "-");

    document.getElementById("generated-at").textContent = card.generatedAt;
    document.getElementById("card-id").textContent = card.cardId;
    document.getElementById("provenance-hash").textContent = card.provenanceHash;
    document.getElementById("desk-json").textContent = JSON.stringify(card.desk, null, 2);
    document.getElementById("signal-json").textContent = JSON.stringify(card.signal, null, 2);
    document.getElementById("trust-json").textContent = JSON.stringify(card.trust, null, 2);
  } catch {
    loading.hidden = true;
    empty.hidden = false;
  }
}

loadCard();
setInterval(loadCard, 15000);
