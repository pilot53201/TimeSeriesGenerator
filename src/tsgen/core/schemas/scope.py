"""Anomaly scopes (extensible via discriminated union).

To add a new scope type (e.g. by_level, by_prefix):
  1. Define a new class below with a unique ``type`` literal.
  2. Add it to the ``Scope`` union.
  3. Handle it in ``core/anomalies.resolve_scope``.
  4. (Optional) Add validation in ``Config._check_scope_channels``.
"""

from pydantic import BaseModel


class ScopeSingle(BaseModel):
    pass