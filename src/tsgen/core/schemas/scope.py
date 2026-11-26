"""Anomaly scopes (extensible via discriminated union).

To add a new scope type (e.g. by_level, by_prefix):
  1. Define a new class below with a unique ``type`` literal.
  2. Add it to the ``Scope`` union.
  3. Handle it in ``core/anomalies.resolve_scope``.
  4. (Optional) Add validation in ``Config._check_scope_channels``.
"""
from typing import Literal, Union, Annotated

from pydantic import BaseModel, ConfigDict, Field


class ScopeSingle(BaseModel):
    """One specific channel is invalid."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["single"] = "single"
    channel: str = Field(min_length=1, description="Invalid channel.")


class ScopeMulti(BaseModel):
    """Fixed set of channels are invalid."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["multi"] = "multi"
    channels: list[str] = Field(min_length=1, description="List of channels invalid.")

class ScopeAll(BaseModel):
    """All channels are invalid."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["all"] = "all"

class ScopeRandomK(BaseModel):
    """K random (uniform distribution without repeats) channels are invalid."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["random_k"] = "random_k"
    k: int = Field(ge=1, description="Number of random channels invalid.")

Scope = Annotated[
    Union[ScopeSingle, ScopeMulti, ScopeAll, ScopeRandomK],
    Field(discriminator="type"),
]