"""Missing value generation parameters.

Three modes:
  none      — no missing values (default)
  pointwise — independent per-cell misses with point_probability
  blockwise — n_blocks contiguous gaps of length [block_min_len, block_max_len]
              per target channel

Fields unrelated to the active mode are allowed and ignored. This lets
users keep a single config and toggle ``mode`` without rewriting JSON.

Channel references (``channels``) are validated at the Config level,
not here — MissingSpec does not know about the available channels.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator, ValidationError


class MissingSpec(BaseModel):
    """Parameters controlling missing-value generation."""
    model_config = ConfigDict(extra="forbid")

    mode: Literal["none", "pointwise", "blockwise"] = Field(
        default="none",
        description=(
             "none — no missing values; "
            "pointwise — independent per-cell misses with point_probability; "
            "blockwise — n_blocks contiguous gaps per target channel."
        ),
    )
    point_probability: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description=(
            "Probability of an independent miss (pointwise mode). "
            "0.0 means no misses, 1.0 means all cells missing."
        )
    )
    n_blocks: int = Field(
        default=0,
        ge=0,
        description="Number of contiguous gaps per channel (blockwise mode)."
    )
    block_min_len: int = Field(
        default=10,
        gt=0,
        description="Minimum block length in samples (blockwise mode)."
    )
    block_max_len: int = Field(
        default=50,
        gt=0,
        description="Maximum block length in samples (blockwise mode)."
    )
    channels: list[str] = Field(
        default_factory=list,
        description=(
            "Target channels. Empty list means all channels. "
            "Must reference existing channel names (validated in Config)."
        ),
    )

    @model_validator(mode="after")
    def _validate(self) -> "MissingSpec":
        if self.block_min_len > self.block_max_len:
            raise ValueError(
                f"block_min_len ({self.block_min_len}) > "
                f"block_max_len ({self.block_max_len})"
            )
        if self.mode == "blockwise" and self.n_blocks == 0:
            raise ValueError(
                "mode='blockwise' requires n_blocks > 0"
            )
        return self
