"""Which reference columns to include in the output.

The following columns are ALWAYS included and cannot be disabled:
  timestamp, split, anomaly_any, event_id, <ch>__observed

They are the detector input and the ground-truth labels; a dataset
without them is not usable for anomaly detection research.

The flags below toggle the *additional* reference columns. Disable them
to shrink the Excel file, enable to get full ground truth for analysis.
"""
from pydantic import BaseModel, ConfigDict, Field


class ReferencesSpec(BaseModel):
    """Which reference columns to include in the output."""

    model_config = ConfigDict(extra="forbid")

    normal: bool = Field(
        default=True,
        description=(
            "Counterfactual normal signal without anomaly effect. "
            "Computed from the same noise realization as ``complete``, "
            "so ``complete - normal`` equals exactly the anomaly effect."
        ),
    )
    complete: bool = Field(
        default=True,
        description=(
            "Signal with anomalies but before applying the missing mask. "
            "Equals ``normal`` outside anomaly events."
        ),
    )
    baseline: bool = Field(
        default=True,
        description=(
            "Baseline without measurement noise and without anomalies: "
            "level + trend + harmonics + shared background only."
        ),
    )
    components: bool = Field(
        default=False,
        description=(
            "Per-component decomposition of the signal: "
            "``<ch>__trend``, ``<ch>__harmonic``, ``<ch>__shared_background``, "
            "``<ch>__measurement_noise``, ``<ch>__anomaly_effect``. "
            "Adds 5 columns per channel — disabled by default to keep "
            "the Excel file compact."
        ),
    )
    missing_mask: bool = Field(
        default=True,
        description=(
            "Binary missing mask per channel: 1 if the cell is missing, "
            "0 otherwise. Needed to distinguish anomalies from gaps."
        ),
    )
    anomaly_labels: bool = Field(
        default=True,
        description=(
            "Per-channel binary anomaly labels. Needed for multi-channel "
            "events: ``anomaly_any`` marks positions, but not which channels "
            "are affected."
        ),
    )


