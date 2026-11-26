"""Root experiment configuration — composes all schema models."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tsgen.core.schemas.anomaly import AnomalySpec
from tsgen.core.schemas.channel import ChannelSpec
from tsgen.core.schemas.constants import (
    DEFAULT_FREQUENCY_SECONDS,
    DEFAULT_N_DIMENSIONS,
    SCHEMA_VERSION,
)
from tsgen.core.schemas.missing import MissingSpec
from tsgen.core.schemas.references import ReferencesSpec
from tsgen.core.schemas.scope import ScopeMulti, ScopeRandomK, ScopeSingle
from tsgen.core.schemas.shared_process import SharedProcessSpec
from tsgen.core.schemas.split import SplitSet


class Config(BaseModel):
    """Root experiment configuration (the single source of truth per run).

    ``model_dump(mode='json')`` is the canonical form used for config_hash
    and for storing in the CONFIG sheet / database.

    Note: if ``channels`` is empty and ``profile`` is None or 'generic',
    the validator fills it with ``n_dimensions`` default channels. The
    resolved config is what gets hashed for reproducibility.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = Field(
        default=SCHEMA_VERSION,
        description="Config schema version (used for migrations).",
    )
    generator: Literal["timeseries"] = Field(
        default="timeseries",
        description="Generator plugin name. Future: 'tabular', etc.",
    )
    profile: Literal["generic", "meteo", "engine"] | None = Field(
        default=None,
        description=(
            "Optional domain profile. If set and channels is empty, the "
            "profile supplies default channels. If channels is non-empty, "
            "they override profile defaults."
        ),
    )
    seed: int = Field(
        description="Root seed for the deterministic seed tree.",
        examples=[42],
    )
    start_iso: datetime = Field(
        default=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        description=(
            "Timestamp of the first sample. Naive datetimes are interpreted "
            "as UTC. Non-UTC timezones are normalized to UTC."
        ),
    )
    frequency_seconds: int = Field(
        default=DEFAULT_FREQUENCY_SECONDS,
        gt=0,
        description="Sampling step in seconds.",
    )
    n_series: int = Field(
        default=1,
        ge=1,
        description="Number of generated objects (one Excel sheet each).",
    )
    n_dimensions: int = Field(
        default=DEFAULT_N_DIMENSIONS,
        ge=1,
        description=(
            "Number of channels if channels is empty and no profile is set. "
            "Ignored otherwise."
        ),
    )
    channels: list[ChannelSpec] = Field(
        default_factory=list,
        description="Channel definitions. If empty, derived from n_dimensions.",
    )
    shared_processes: list[SharedProcessSpec] = Field(
        default_factory=list,
        description="Shared AR(1) background processes for inter-channel coupling.",
    )

    splits: SplitSet
    anomalies: AnomalySpec = Field(default_factory=AnomalySpec)
    missing: MissingSpec = Field(default_factory=MissingSpec)
    references: ReferencesSpec = Field(default_factory=ReferencesSpec)

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Free-form annotations (author, purpose, ticket). "
            "Excluded from config_hash — does not affect generation."
        ),
    )

    # ─────────────────────── validators ───────────────────────

    @field_validator("start_iso")
    @classmethod
    def _normalize_start(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @model_validator(mode="before")
    @classmethod
    def _fill_default_channels(cls, data: Any) -> Any:
        """Fill ``channels`` with default definitions when omitted.

        Runs in ``mode="before"`` so pydantic constructs nested models
        (Harmonic, NoiseSpec) from plain dicts, and so channels is populated
        before ANY ``mode='after'`` validator runs — regardless of declaration
        order below.
        """
        if not isinstance(data, dict):
            return data
        if data.get("channels"):
            return data
        if data.get("profile") not in (None, "generic"):
            raise ValueError(
                f"profile {data.get('profile')!r} is not implemented yet; "
                f"set profile=None or 'generic', or provide explicit channels"
            )
        n = data.get("n_dimensions", DEFAULT_N_DIMENSIONS)
        if not isinstance(n, int) or n < 1:
            return data  # let pydantic report the n_dimensions error itself
        has_shared = bool(data.get("shared_processes"))
        return {
            **data,
            "channels": [
                {
                    "name": f"ch_{i}",
                    "level": 10.0,
                    "harmonics": [{"period_seconds": 86400.0, "amplitude": 2.0}],
                    "noise": {"type": "gaussian", "sigma": 0.5},
                    "shared_weights": [1.0] if has_shared else [],
                }
                for i in range(n)
            ],
        }

    @model_validator(mode="after")
    def _check_unique_names(self) -> "Config":
        names = [c.name for c in self.channels]
        if len(names) != len(set(names)):
            dupes = sorted({n for n in names if names.count(n) > 1})
            raise ValueError(f"duplicate channel names: {dupes}")
        return self

    @model_validator(mode="after")
    def _check_shared_weights(self) -> "Config":
        q = len(self.shared_processes)
        for ch in self.channels:
            if ch.shared_weights and len(ch.shared_weights) != q:
                raise ValueError(
                    f"channel {ch.name!r}: shared_weights has "
                    f"{len(ch.shared_weights)} entries, expected {q} "
                    f"(number of shared_processes)"
                )
        return self

    @model_validator(mode="after")
    def _check_missing_channels(self) -> "Config":
        known = {c.name for c in self.channels}
        for name in self.missing.channels:
            if name not in known:
                raise ValueError(
                    f"missing.channels references unknown channel {name!r}; "
                    f"known: {sorted(known)}"
                )
        return self

    @model_validator(mode="after")
    def _check_scope_channels(self) -> "Config":
        known = {c.name for c in self.channels}
        scope = self.anomalies.scope
        if isinstance(scope, ScopeSingle):
            if scope.channel not in known:
                raise ValueError(
                    f"anomalies.scope.channel references unknown channel "
                    f"{scope.channel!r}; known: {sorted(known)}"
                )
        elif isinstance(scope, ScopeMulti):
            for name in scope.channels:
                if name not in known:
                    raise ValueError(
                        f"anomalies.scope.channels references unknown channel "
                        f"{name!r}; known: {sorted(known)}"
                    )
        elif isinstance(scope, ScopeRandomK):
            if scope.k > len(known):
                raise ValueError(
                    f"anomalies.scope.k={scope.k} exceeds number of channels "
                    f"({len(known)})"
                )
        return self

    # ───────────────────────────── helpers ─────────────────────────────

    @property
    def channel_names(self) -> list[str]:
        return [c.name for c in self.channels]

    @property
    def total_size(self) -> int:
        return self.splits.total_size

    @property
    def total_normal(self) -> int:
        return self.splits.total_normal

    @property
    def total_anomaly(self) -> int:
        return self.total_size - self.total_normal

    @property
    def total_length(self) -> int:
        return self.splits.total_length

    def config_hash(self, exclude: set[str] | None = None) -> str:
        data = self.model_dump(
            mode="json",
            exclude=exclude if exclude is not None else {"metadata"},
        )
        canonical = json.dumps(
            data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()