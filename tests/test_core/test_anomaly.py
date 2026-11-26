import pytest
from pydantic import ValidationError

from tsgen.core.schemas.anomaly import AnomalySpec
from tsgen.core.schemas.scope import ScopeMulti, ScopeRandomK


def test_default_anomaly_spec():
    a = AnomalySpec()
    assert a.min_duration == 10
    assert a.max_duration == 100
    assert a.min_gap == 5
    assert a.intensity == 2.0
    assert a.termination == "keep_phase"
    assert a.sync_length == 0
    assert isinstance(a.scope, ScopeRandomK)
    assert a.scope.k == 1
    assert set(a.kinds.keys()) == {
        "level_shift", "amplitude_change", "noise_increase",
        "stuck_sensor", "frequency_change", "phase_change",
    }


def test_kinds_default_is_fresh_dict():
    """default_factory должен создавать новый dict на каждый инстанс."""
    a = AnomalySpec()
    b = AnomalySpec()
    assert a.kinds is not b.kinds
    a.kinds["level_shift"] = 999.0
    assert b.kinds["level_shift"] != 999.0


def test_unknown_kind_rejected():
    with pytest.raises(ValidationError, match="level_shift"):
        AnomalySpec(kinds={"spike": 1.0})


def test_empty_kinds_rejected():
    with pytest.raises(ValidationError, match="kinds must not be empty"):
        AnomalySpec(kinds={})


def test_negative_weight_rejected():
    with pytest.raises(ValidationError, match="non-negative"):
        AnomalySpec(kinds={"level_shift": -0.5})


def test_zero_weights_rejected():
    with pytest.raises(ValidationError, match="must be positive"):
        AnomalySpec(kinds={"level_shift": 0.0})


def test_min_duration_exceeds_max():
    with pytest.raises(ValidationError, match="min_duration.*>.*max_duration"):
        AnomalySpec(min_duration=100, max_duration=10)


def test_smooth_return_requires_sync_length():
    with pytest.raises(ValidationError, match="smooth_return"):
        AnomalySpec(termination="smooth_return", sync_length=0)


def test_smooth_return_with_sync_length_ok():
    a = AnomalySpec(termination="smooth_return", sync_length=50)
    assert a.termination == "smooth_return"
    assert a.sync_length == 50


def test_scope_multi_inside_anomaly():
    a = AnomalySpec(scope={"type": "multi", "channels": ["a", "b"]})
    assert isinstance(a.scope, ScopeMulti)


def test_scope_unknown_type_rejected():
    with pytest.raises(ValidationError, match="does not match"):
        AnomalySpec(scope={"type": "by_level"})


def test_negative_intensity_rejected():
    with pytest.raises(ValidationError):
        AnomalySpec(intensity=-1.0)


def test_roundtrip():
    a = AnomalySpec(
        kinds={"level_shift": 1.0},
        intensity=3.5,
        scope={"type": "all"},
    )
    dumped = a.model_dump()
    b = AnomalySpec.model_validate(dumped)
    assert a.model_dump() == b.model_dump()