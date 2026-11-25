"""This file contains the model of harmonic periodic data."""
from pydantic import BaseModel, ConfigDict, Field


class Harmonic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_seconds: float = Field(
        gt=0,
        description="Period in seconds (not in samples).",
        examples=[86400.0],
    )
    amplitude: float = Field(
        description="Amplitude of the harmonic period in channel units.",
        examples=[5.0],
    )
    phase: float = Field(
        default=0.0,
        description="Phase of the harmonic period in radians.",
        examples=[0.0, 1.5708],
    )
