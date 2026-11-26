"""This file contains the main anomaly generation parameters.

Intensity semantics per kind (see docs/CONFIG.md):
  level_shift       — absolute offset in channel units
  amplitude_change  — relative change: A_new = A * (1 + intensity)
  noise_increase    — relative increase of noise sigma
  stuck_sensor      — unused
  frequency_change  — percent: f_new = f * (1 + intensity / 100)
  phase_change      — quarter-pi units: delta_phi = intensity * pi / 4
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tsgen.core.schemas.constants import default_anomaly_weights
from tsgen.core.schemas.scope import Scope, ScopeRandomK

AnomalyKind = Literal[
    "level_shift",
    "amplitude_change",
    "noise_increase",
    "stuck_sensor",
    "frequency_change",
    "phase_change",
]


PhaseTermination = Literal["keep_phase", "smooth_return", "jump"]

class AnomalySpec(BaseModel):
    """Parameters for anomaly generation.

    See module docstring for intensity semantics per kind.
    """

    model_config = ConfigDict(extra="forbid")

    kinds: dict[AnomalyKind, float] = Field(
        default_factory=default_anomaly_weights,
        description=(
            "Relative weights per anomaly kind. Normalized to probabilities "
            "before sampling. Keys must be known anomaly kinds."
        ),
    )
    min_duration: int = Field(
        default=10,
        ge=1,
        description="Minimum duration of anomaly to be considered.",
    )
    max_duration: int = Field(
        default=100,
        ge=1,
        description="Maximum duration of anomaly to be considered.",
    )
    min_gap: int = Field(
        default=5,
        ge=0,
        description="Minimum gap between consecutive events, in samples.",
    )
    intensity: float = Field(
        default=2.0,
        gt=0,
        description=(
            "Intensity of the anomaly. Units depend on kind — "
            "see module docstring."
        ),
    )
    scope: Scope = Field(
        default_factory=lambda: ScopeRandomK(k=1),
        description="Which channels an event affects.",
    )
    termination: PhaseTermination = Field(
        default="keep_phase",
        description=(
            "How frequency/phase anomalies terminate: "
            "keep_phase — accumulated phase persists after the event; "
            "smooth_return — phase smoothly returns over sync_length; "
            "jump — abrupt return to ideal phase at event end."
        ),
    )
    sync_length: int = Field(
        default=0,
        ge=0,
        description="Length of smooth-return window (used with smooth_return).",
    )

    @model_validator(mode="after")
    def _validate(self) -> "AnomalySpec":
        if self.min_duration > self.max_duration:
            raise ValueError(
                f"min_duration ({self.min_duration}) > "
                f"max_duration ({self.max_duration})"
            )
        if not self.kinds:
            raise ValueError("kinds must not be empty")
        if any(w < 0 for w in self.kinds.values()):
            raise ValueError("kinds weights must be non-negative")
        if sum(self.kinds.values()) <= 0:
            raise ValueError("sum of kinds weights must be positive")
        if self.termination == "smooth_return" and self.sync_length <= 0:
            raise ValueError(
                "termination='smooth_return' requires sync_length > 0"
            )
        return self
