"""Temporal splits: train / validation / test.

Order in the dataset:
  [<split>_prefix] [<split>] for each split in ordered()

`initial_normal` in each SplitSpec is the number of leading positions
of that split which are labeled '<split>_prefix' and contain no anomalies.

If you want a fully normal split, omit `normal` (it defaults to `size`).
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SplitSpec(BaseModel):
    """One time slice (train, validation, or test)."""

    model_config = ConfigDict(extra="forbid")

    size: int = Field(
        gt=0,
        description="Total number of time positions in the split itself.",
        examples=[5000],
    )
    normal: int = Field(
        ge=0,
        description=(
            "Exact number of normal positions WITHIN the split "
            "(excluding initial_normal prefix). If omitted in JSON, "
            "defaults to size (fully normal split). The rest "
            "(size - normal) is covered by anomalies. "
            "normal=0 means fully anomalous split (valid edge case)."
        ),
        examples=[4500],
    )
    initial_normal: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of consecutive positions at the START of the split "
            "that are labeled '<split>_prefix' and contain no anomalies. "
            "For train this is the burn-in segment. "
            "Total generated length = sum(initial_normal + size)."
        ),
        examples=[500],
    )

    @model_validator(mode="before")
    @classmethod
    def _default_normal(cls, data: Any) -> Any:
        """If `normal` is omitted, default to `size` (fully normal split)."""
        if isinstance(data, dict) and "normal" not in data and "size" in data:
            return {**data, "normal": data["size"]}
        return data

    @model_validator(mode="after")
    def _validate(self) -> "SplitSpec":
        if self.normal > self.size:
            raise ValueError(
                f"normal ({self.normal}) must be <= size ({self.size})"
            )
        return self


class SplitSet(BaseModel):
    """Ordered set of splits, each with an optional burn-in prefix."""

    model_config = ConfigDict(extra="forbid")

    train: SplitSpec
    validation: SplitSpec | None = None
    test: SplitSpec | None = None

    def ordered(self) -> list[tuple[str, SplitSpec]]:
        """Splits in temporal order."""
        result: list[tuple[str, SplitSpec]] = [("train", self.train)]
        if self.validation is not None:
            result.append(("validation", self.validation))
        if self.test is not None:
            result.append(("test", self.test))
        return result

    @property
    def total_size(self) -> int:
        """Sum of split sizes (excluding initial_normal prefixes)."""
        return sum(s.size for _, s in self.ordered())

    @property
    def total_normal(self) -> int:
        """Sum of normal counts in splits (excluding prefixes)."""
        return sum(s.normal for _, s in self.ordered())

    @property
    def total_prefix(self) -> int:
        """Sum of initial_normal across all splits."""
        return sum(s.initial_normal for _, s in self.ordered())

    @property
    def total_length(self) -> int:
        """Total generated length: prefixes + splits."""
        return self.total_prefix + self.total_size