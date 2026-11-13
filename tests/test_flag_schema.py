"""Offline tests that the flag schema keeps the rollout config and variation values."""

import logging

from singer_sdk.helpers._typing import TypeConformanceLevel, conform_record_data_types

from tap_launchdarkly.tap import TapLaunchDarkly


def _conform(record):
    tap = TapLaunchDarkly(
        config={"auth_token": "test-token", "environment": "production"},
        validate_config=False,
    )
    stream = {s.name: s for s in tap.discover_streams()}["feature_flags"]
    return conform_record_data_types(
        stream.name, record, stream.schema, TypeConformanceLevel.RECURSIVE, logging.getLogger()
    )


def test_multivariate_values_are_kept():
    record = {
        "key": "f",
        "variations": [
            {"_id": "a", "value": 1048576},
            {"_id": "b", "value": "blue"},
            {"_id": "c", "value": {"limit": 5}},
            {"_id": "d", "value": False},
        ],
    }
    values = [v["value"] for v in _conform(record)["variations"]]
    assert values == [1048576, "blue", {"limit": 5}, False]


def test_production_rollout_config_is_kept():
    production = {
        "on": True,
        "archived": False,
        "offVariation": 1,
        "version": 12,
        "lastModified": 1794530006000,
        "fallthrough": {
            "rollout": {
                "variations": [{"variation": 0, "weight": 25000}, {"variation": 1, "weight": 75000}],
                "bucketBy": "key",
            }
        },
        "rules": [
            {
                "_id": "r1",
                "variation": 0,
                "trackEvents": False,
                "clauses": [{"attribute": "key", "op": "in", "values": ["org-1"], "negate": False}],
            }
        ],
        "prerequisites": [{"key": "other", "variation": 0}],
        "_summary": {"variations": {"0": {"rules": 1, "targets": 2}}, "prerequisites": 0},
    }
    out = _conform({"key": "f", "environments": {"production": dict(production, targets=[1])}})
    # `targets` stays out: the feature_flag_targets stream loads them.
    assert out["environments"]["production"] == production
