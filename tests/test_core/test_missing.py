import pytest
from pydantic import ValidationError

from tsgen.core.schemas.missing import MissingSpec


def test_default_missing_spec():
    m = MissingSpec()
    assert m.mode == "none"
    assert m.point_probability  == 0.0
    assert m.n_blocks == 0
    assert m.block_min_len == 10
    assert m.block_max_len == 50
    assert m.channels == []


def test_channels_default_is_fresh_list():
    """default_factory=list, не default=[]."""
    a = MissingSpec()
    b = MissingSpec()
    assert a.channels is not b.channels
    a.channels.append("ch_0")
    assert b.channels == []


def test_pointwise_mode():
    m = MissingSpec(mode="pointwise", point_probability=0.05)
    assert m.mode == "pointwise"
    assert m.point_probability == 0.05


def test_blockwise_mode():
    m = MissingSpec(
        mode="blockwise",
        n_blocks=3,
        block_min_len=2,
        block_max_len=5,
    )
    assert m.n_blocks == 3
    assert m.block_min_len == 2
    assert m.block_max_len == 5


def test_blockwise_requires_n_blocks():
    with pytest.raises(ValidationError, match="requires n_blocks > 0"):
        MissingSpec(mode="blockwise", n_blocks=0)


def test_block_min_exceeds_max():
    with pytest.raises(ValidationError, match="block_min_len.*>"):
        MissingSpec(block_min_len=100, block_max_len=10)


def test_point_probability_bounds():
    with pytest.raises(ValidationError):
        MissingSpec(mode="pointwise", point_probability=-0.1)
    with pytest.raises(ValidationError):
        MissingSpec(mode="pointwise", point_probability=1.5)


def test_point_probability_zero_and_one_valid():
    """0.0 и 1.0 — граничные, но валидные значения (ТЗ п. 14.3)."""
    m0 = MissingSpec(mode="pointwise", point_probability=0.0)
    m1 = MissingSpec(mode="pointwise", point_probability=1.0)
    assert m0.point_probability == 0.0
    assert m1.point_probability == 1.0


def test_unused_fields_allowed():
    """При mode='none' поля других режимов можно задавать — они игнорируются."""
    m = MissingSpec(
        mode="none",
        point_probability=0.5,
        n_blocks=10,
        block_min_len=5,
        block_max_len=10,
        channels=["ch_0"],
    )
    assert m.mode == "none"


def test_block_min_max_checked_even_when_mode_none():
    """Согласованность block_min_len/block_max_len проверяется всегда."""
    with pytest.raises(ValidationError, match="block_min_len.*>"):
        MissingSpec(mode="none", block_min_len=100, block_max_len=10)


def test_unknown_mode_rejected():
    with pytest.raises(ValidationError, match="none.*pointwise.*blockwise|blockwise"):
        MissingSpec(mode="random")


def test_roundtrip():
    m = MissingSpec(
        mode="blockwise",
        n_blocks=3,
        block_min_len=2,
        block_max_len=5,
        channels=["ch_0", "ch_1"],
    )
    dumped = m.model_dump()
    m2 = MissingSpec.model_validate(dumped)
    assert m.model_dump() == m2.model_dump()
