"""Noise models for channel measurement noise.

    To add a new noise type:
        1. Define a new model below with a unique ``type`` literal.
        2. Add it to the ``NoiseSpec`` union.
        3. Add a branch to ``sample_noise``.
"""


from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class GaussianNoise(BaseModel):
    """Additive white Gaussian noise, N(0, sigma^2)."""

    model_config = ConfigDict(extra="forbid")
    type: Literal["gaussian"] = "gaussian"
    sigma: float = Field(gt=0, description="Standard deviation.", examples=[1.0])


class UniformNoise(BaseModel):
    """Uniform noise on [-half_width, +half_width].

    Bounded support — no values outside the range. Useful for testing
    detectors whose assumptions rely on tail behavior.
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["uniform"] = "uniform"
    half_width: float = Field(
        gt=0,
        description="Half-width of the support (std = half_width / sqrt(3)).",
        examples=[1.0],
    )


class LaplaceNoise(BaseModel):
    """Laplace (double-exponential) noise, heavier tails than Gaussian.

    P(|x| > t) ~ exp(-t/scale). Finite variance (std = sqrt(2) * scale).
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["laplace"] = "laplace"
    scale: float = Field(
        gt=0,
        description="Scale parameter (std = sqrt(2) * scale).",
        examples=[0.5],
    )


class StudentTNoise(BaseModel):
    """Student-t noise, heavy tails controlled by degrees of freedom.

    df -> inf: converges to Gaussian. df = 3..5: realistic outliers.
    df <= 2: infinite variance (warn user; useful for adversarial tests).
    """

    model_config = ConfigDict(extra="forbid")
    type: Literal["student_t"] = "student_t"
    df: float = Field(gt=0, description="Degrees of freedom.", examples=[3.0])
    scale: float = Field(default=1.0, gt=0, description="Scale parameter.")


NoiseSpec = Annotated[
    GaussianNoise | UniformNoise | LaplaceNoise | StudentTNoise,
    Field(discriminator="type"),
]

def sample_noise(
    spec: NoiseSpec,
    rng: np.random.Generator,
    n: int,
) -> np.ndarray:
    """Sample ``n`` noise values from the specified distribution.

    All distributions are symmetric around zero with a scale parameter,
    which guarantees that ``sample * k`` has the same distribution as
    sampling from ``spec`` with the scale parameter multiplied by ``k``.
    This property is used by ``noise_increase`` anomaly (see anomalies.py).
    """
    if isinstance(spec, GaussianNoise):
        return rng.normal(0.0, spec.sigma, n)
    if isinstance(spec, UniformNoise):
        return rng.uniform(-spec.half_width, spec.half_width, n)
    if isinstance(spec, LaplaceNoise):
        return rng.laplace(0.0, spec.scale, n)
    if isinstance(spec, StudentTNoise):
        return rng.standard_t(spec.df, n) * spec.scale
    raise TypeError(f"unknown noise type: {type(spec).__name__}")