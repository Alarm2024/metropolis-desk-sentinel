"""Mock desk metrics for local MVP — no live feeds, no secrets."""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DeskMetrics:
    """Synthetic desk snapshot used by the sentinel agent."""

    symbol: str
    bid_ask_bps: float
    volume_delta_pct: float
    order_flow_imbalance: float  # -1 sell-heavy .. +1 buy-heavy
    volatility_1h_pct: float
    liquidity_score: float  # 0 thin .. 1 deep
    spread_stability: float  # 0 unstable .. 1 stable
    timestamp_ms: int
    seed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _derive_seed(symbol: str, bucket_ms: int) -> str:
    raw = f"{symbol}:{bucket_ms // 60_000}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_mock_metrics(symbol: str = "MLDS-MOCK") -> DeskMetrics:
    """Deterministic-per-minute mock metrics for repeatable local demos."""
    now_ms = int(time.time() * 1000)
    seed = _derive_seed(symbol, now_ms)
    rng = random.Random(seed)

    return DeskMetrics(
        symbol=symbol,
        bid_ask_bps=round(rng.uniform(0.8, 12.0), 2),
        volume_delta_pct=round(rng.uniform(-18.0, 18.0), 2),
        order_flow_imbalance=round(rng.uniform(-1.0, 1.0), 3),
        volatility_1h_pct=round(rng.uniform(0.3, 4.5), 2),
        liquidity_score=round(rng.uniform(0.15, 0.95), 3),
        spread_stability=round(rng.uniform(0.2, 0.98), 3),
        timestamp_ms=now_ms,
        seed=seed,
    )
