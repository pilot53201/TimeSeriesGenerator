"""Tests for `core.schemas.scope`.
. module:: core.schemas.scope"""

import pytest
from pydantic import TypeAdapter, ValidationError

from tsgen.core.schemas.scope import (
    Scope,
    ScopeAll,
    ScopeMulti,
    ScopeRandomK,
    ScopeSingle,
)


adapter = TypeAdapter(Scope)



def test_scope_single() -> None:
    scope = adapter.validate_python({'type': 'single', 'channel': 'ch_0'})
    assert isinstance(scope, ScopeSingle)
    assert scope.channel == 'ch_0'


def test_scope_multi() -> None:
    scope = adapter.validate_python({'type': 'multi', 'channels': ['ch_0', 'ch_1', 'a', 'b']})
    assert isinstance(scope, ScopeMulti)
    assert scope.channels == ['ch_0', 'ch_1', 'a', 'b']

def test_scope_all() -> None:
    scope = adapter.validate_python({'type': 'all'})
    assert isinstance(scope, ScopeAll)
    assert scope.model_dump() == {'type': 'all'}


def test_scope_random_k() -> None:
    scope = adapter.validate_python({'type': 'random_k', "k": 3})
    assert isinstance(scope, ScopeRandomK)
    assert scope.k == 3

def test_scope_unknown_type() -> None:
    with pytest.raises(ValidationError, match="does not match any of the expected tags"):
        adapter.validate_python({'type': 'unknown', 'level': 2})


def test_scope_multi_empty_rejected():
    with pytest.raises(ValidationError, match="at least 1 item"):
        adapter.validate_python({"type": "multi", "channels": []})

def test_scope_extra_field_rejected():
    with pytest.raises(ValidationError, match="Extra inputs"):
        adapter.validate_python({"type": "all", "extra": 1})