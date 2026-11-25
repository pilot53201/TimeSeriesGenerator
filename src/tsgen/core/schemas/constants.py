"""This file contains constants and defaults used in the generator part."""
__author__ = "pilot53201"

SCHEMA_VERSION = "0.1"
DEFAULT_FREQUENCY_SECONDS = 3600
DEFAULT_N_DIMENSIONS = 7


def default_anomaly_weights():
    """Default relative weights for anomaly types."""
    return {
        "level_shift": 0.25,
        "amplitude_change": 0.15,
        "noise_increase": 0.15,
        "stuck_sensor": 0.15,
        "frequency_change": 0.15,
        "phase_change": 0.15,
    }