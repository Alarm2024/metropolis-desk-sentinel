"""Typed signal card schema — validated at emission, auditable by judges."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CARD_SCHEMA_VERSION = "2.0"
AGENT_VERSION = "1.0.0-metropolis"


class Signal(str, Enum):
    CLEAR = "CLEAR"
    SHORT = "SHORT"
    HOLD = "HOLD"


class TrustPosture(str, Enum):
    """Whether the agent acted directionally or refused with honesty."""

    DIRECTIONAL = "DIRECTIONAL"
    REFUSAL = "REFUSAL"


class RefusalCode(str, Enum):
    EXEC_QUALITY = "EXEC_QUALITY"
    NO_EDGE = "NO_EDGE"
    NEUTRAL_BAND = "NEUTRAL_BAND"


REFUSAL_MESSAGES: dict[RefusalCode, str] = {
    RefusalCode.EXEC_QUALITY: "Refused directional action: execution quality below trust threshold",
    RefusalCode.NO_EDGE: "Refused directional action: composite score too weak to trust",
    RefusalCode.NEUTRAL_BAND: "Refused directional action: score inside neutral band — no fake conviction",
}


class DeskMetricsSchema(BaseModel):
    symbol: str
    bid_ask_bps: float = Field(ge=0)
    volume_delta_pct: float
    order_flow_imbalance: float = Field(ge=-1, le=1)
    volatility_1h_pct: float = Field(ge=0)
    liquidity_score: float = Field(ge=0, le=1)
    spread_stability: float = Field(ge=0, le=1)
    timestamp_ms: int = Field(ge=0)
    seed: str


class SignalCardSchema(BaseModel):
    """Canonical desk signal card — every field is auditable."""

    signal: Literal["CLEAR", "SHORT", "HOLD"]
    summary: str = Field(min_length=10)
    safe_hold: bool
    trust_posture: TrustPosture
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(min_length=1)
    reason_codes: list[str] = Field(min_length=1)
    metrics: DeskMetricsSchema
    provenance_hash: str = Field(min_length=64, max_length=64)
    agent_version: str
    schema_version: str
    timestamp_ms: int = Field(ge=0)
    refusal_code: RefusalCode | None = None
    refusal_reason: str | None = None

    @field_validator("provenance_hash")
    @classmethod
    def hex_only(cls, v: str) -> str:
        if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
            raise ValueError("provenance_hash must be 64-char lowercase hex SHA-256")
        return v

    @model_validator(mode="after")
    def enforce_trust_invariants(self) -> SignalCardSchema:
        if self.signal == "HOLD":
            if not self.safe_hold:
                raise ValueError("HOLD must set safe_hold=true")
            if self.trust_posture != TrustPosture.REFUSAL:
                raise ValueError("HOLD must set trust_posture=REFUSAL")
            if self.refusal_code is None or self.refusal_reason is None:
                raise ValueError("HOLD must include refusal_code and refusal_reason")
        else:
            if self.safe_hold:
                raise ValueError(f"{self.signal} must not set safe_hold=true")
            if self.trust_posture != TrustPosture.DIRECTIONAL:
                raise ValueError(f"{self.signal} must set trust_posture=DIRECTIONAL")
            if self.refusal_code is not None or self.refusal_reason is not None:
                raise ValueError(f"{self.signal} must not include refusal fields")
        return self

    def to_dict(self) -> dict[str, Any]:
        out = self.model_dump(mode="json")
        if self.refusal_code is None:
            out.pop("refusal_code", None)
        if self.refusal_reason is None:
            out.pop("refusal_reason", None)
        return out
