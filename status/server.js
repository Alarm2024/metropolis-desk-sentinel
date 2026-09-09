#!/usr/bin/env node
/**
 * Morning Light Desk Sentinel — status page server.
 * Serves last JSON card + provenance hash for local inspection.
 */

import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const CARD_PATH = join(ROOT, "data", "last-card.json");
const PUBLIC_DIR = join(__dirname, "public");
const PORT = Number(process.env.PORT) || 3847;

function loadCard() {
  if (!existsSync(CARD_PATH)) return null;
  try {
    return JSON.parse(readFileSync(CARD_PATH, "utf8"));
  } catch {
    return null;
  }
}

function serveStatic(path) {
  const file = join(PUBLIC_DIR, path === "/" ? "index.html" : path);
  if (!existsSync(file)) return null;
  const ext = file.split(".").pop();
  const types = { html: "text/html", css: "text/css", js: "application/javascript" };
  return { body: readFileSync(file), type: types[ext] || "text/plain" };
}

const server = createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (url.pathname === "/api/card") {
    const card = loadCard();
    res.writeHead(card ? 200 : 404, { "Content-Type": "application/json" });
    res.end(card ? JSON.stringify(card, null, 2) : JSON.stringify({ error: "No card yet. Run npm run agent." }));
    return;
  }

  if (url.pathname === "/api/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ ok: true, service: "desk-sentinel-status" }));
    return;
  }

  const staticFile = serveStatic(url.pathname);
  if (staticFile) {
    res.writeHead(200, { "Content-Type": staticFile.type });
    res.end(staticFile.body);
    return;
  }

  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("Not found");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[status] Morning Light Desk Sentinel → http://localhost:${PORT}`);
  console.log(`[status] API card → http://localhost:${PORT}/api/card`);
});
