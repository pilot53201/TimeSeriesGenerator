"""Tests for `core.schemas.references`.
. module:: core.schemas.references"""

import pytest
from pydantic import ValidationError

from tsgen.core.schemas.references import ReferencesSpec


def test_defaults():
    ref = ReferencesSpec()
    assert ref.normal is True
    assert ref.complete is True
    assert ref.baseline is True
    assert ref.components is False
    assert ref.missing_mask is True
    assert ref.anomaly_labels is True


def test_all_false_valid():
    ref = ReferencesSpec(
        normal=False, complete=False, baseline=False,
        components=False, missing_mask=False, anomaly_labels=False
    )
    assert all(v is False for v in ref.model_dump().values())


def test_all_true_valid():
    ref = ReferencesSpec(
        normal=True, complete=True, baseline=True,
        components=True, missing_mask=True, anomaly_labels=True
    )
    assert all(v is True for v in ref.model_dump().values())


def test_extra_field_rejected():
    with pytest.raises(ValidationError, match="Extra inputs"):
        ReferencesSpec()
        ref = ReferencesSpec(diagnostics=True)


def test_round_trip():
    ref = ReferencesSpec(
        normal=True, baseline=False,
    )
    dumped = ref.model_dump()
    another_ref = ReferencesSpec.model_validate(dumped)
    assert ref.model_dump() == another_ref.model_dump()