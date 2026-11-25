"""This file contains AR(1) background process shared across channels of one object."""
from pydantic import BaseModel, Field


class SharedProcessSpec(BaseModel):
    """
    AR(1) background process shared across channels of one object.

    z(t) = ρ · z(t-1) + σ · √(1-ρ²) · ξ(t)
    """
    rho: float = Field(gt=0, lt=1,  description="Memory correlation coefficient.")
    sigma: float = Field(default=1.0, description="Standard deviation of the random process.")
