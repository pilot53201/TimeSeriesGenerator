"""This file contains measured channel within an object."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.tsgen.core.schemas.harmonic import Harmonic
from src.tsgen.core.schemas.noise import GaussianNoise, NoiseSpec


class ChannelSpec(BaseModel):
    """One measured channel within an object."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        description="Unique channel name within the object.",
        examples = ["temperature", "humidity", "T_2m", "CO2_50m"],
    )
    unit: str = Field(
        default="",
        description="Physical unit for docks and excel.",
        examples = ["°C", "%", "M", "G", "T"],
    )
    level: float = Field(
        default=0.0,
        description="constant level (c_ij)."
    )
    trend_per_second: float = Field(
        default=0.0,
        description="Linear trend in channel units per second (b_ij).",
        examples=[0.5 / 86400],
    )
    harmonics: list[Harmonic] = Field(
        default_factory=list,
        description="Harmonic components.",
    )
    noise: NoiseSpec = Field(
        default_factory=lambda: GaussianNoise(sigma=1.0),
        description=(
            "Noise model for this channel. Default: Gaussian Noise sigma=1.0."
            "All noise types are symmetric around zero."
        ),
    )
    shared_weights: list[float] = Field(
        default_factory=list,
        description=(
            "Weights for each shared process. Empty list means the channel "
            "does not depend on any shared process. If non-empty, its length "
            "must equal len(shared_processes)."
        ),
    )

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if "__" in v:
            raise ValueError(
                "channel name must not contain '__' "
                "(used as separator in Excel column names like '<ch>__observed')"
            )
        if not (v[0].isalpha() or v[0] == "_"):
            raise ValueError("channel name must start with a letter or underscore")
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError(
                "channel name may contain only letters, digits, and underscores"
            )
        return v