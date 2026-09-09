#!/usr/bin/env node
/**
 * Morning Light Desk Sentinel — mock desk agent.
 * Emits structured JSON cards from simulated metrics.
 * No live trading, no secrets, no external MEV dependencies.
 */

import { createHash, randomUUID } from "node:crypto";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const OUTPUT_DIR = join(ROOT, "data");
const CARD_PATH = join(OUTPUT_DIR, "last-card.json");

const BRANDING = {
  owner: "✝️🧿🪬",
  bot: "3️⃣🧿5️⃣",
};

const SIGNALS = ["SAFE HOLD", "CLEAR", "SHORT", "HOLD"];

/** Simulated desk metrics — replace with real feeds in production. */
function mockDeskMetrics() {
  const symbols = ["ETH-USD", "BTC-USD", "SOL-USD"];
  const symbol = symbols[Math.floor(Math.random() * symbols.length)];

  return {
    symbol,
    position: ["flat", "long", "short"][Math.floor(Math.random() * 3)],
    exposureUsd: Math.round(Math.random() * 50000),
    pnl24hPct: Number((Math.random() * 4 - 2).toFixed(2)),
    volatilityIndex: Number((Math.random() * 100).toFixed(1)),
    liquidityScore: Number((Math.random()).toFixed(2)),
    openOrders: Math.floor(Math.random() * 5),
    lastFillMs: Date.now() - Math.floor(Math.random() * 3600000),
  };
}

/** Rule-based signal from mock metrics — transparent, not predictive. */
function deriveSignal(metrics) {
  const { pnl24hPct, volatilityIndex, position, liquidityScore } = metrics;

  if (volatilityIndex > 75 && position !== "flat") {
    return {
      action: "CLEAR",
      rationale:
        "Elevated volatility with open exposure — reduce risk before adding size.",
      confidence: 0.72,
    };
  }

  if (pnl24hPct < -1.5 && position === "long") {
    return {
      action: "SHORT",
      rationale:
        "Mock desk shows underwater long with negative 24h PnL — bias to de-risk.",
      confidence: 0.58,
    };
  }

  if (volatilityIndex > 60 || liquidityScore < 0.3) {
    return {
      action: "SAFE HOLD",
      rationale:
        "Conditions uncertain — preserve capital; no new entries until clarity.",
      confidence: 0.65,
    };
  }

  return {
    action: "HOLD",
    rationale: "Mock metrics within normal band — maintain current stance.",
    confidence: 0.55,
  };
}

function computeProvenanceHash(payload) {
  const canonical = JSON.stringify(payload, Object.keys(payload).sort());
  return createHash("sha256").update(canonical).digest("hex");
}

function buildCard() {
  const generatedAt = new Date().toISOString();
  const desk = mockDeskMetrics();
  const signal = deriveSignal(desk);

  const body = {
    cardId: randomUUID(),
    version: "1.0.0",
    project: "Morning Light Desk Sentinel",
    generatedAt,
    branding: BRANDING,
    desk,
    signal: {
      ...signal,
      allowedActions: SIGNALS,
      honesty: {
        disclaimer:
          "This card is generated from mock desk metrics for MVP demonstration only. " +
          "It is not financial advice and must not be used for live execution without " +
          "independent verification.",
        dataSource: "mock",
        aiAssisted: true,
        humanReviewRequired: true,
        limitations: [
          "Metrics are simulated, not exchange-sourced",
          "Signal logic is rule-based, not ML-trained",
          "No on-chain identity attestation in this MVP",
          "Provenance hash covers card body only, not future chain anchors",
        ],
      },
    },
    trust: {
      identityLayer: "stub",
      attestations: [],
      policyVersion: "trust-v0.1",
      metropolisTrack: "Trust / Identity & AI Infrastructure",
    },
  };

  const provenanceHash = computeProvenanceHash(body);

  return { ...body, provenanceHash };
}

function main() {
  mkdirSync(OUTPUT_DIR, { recursive: true });
  const card = buildCard();
  writeFileSync(CARD_PATH, JSON.stringify(card, null, 2) + "\n", "utf8");
  console.log(`[sentinel] Card written → ${CARD_PATH}`);
  console.log(`[sentinel] Signal: ${card.signal.action} | Hash: ${card.provenanceHash.slice(0, 16)}…`);
}

main();
