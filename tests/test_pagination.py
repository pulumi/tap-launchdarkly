"""Offline tests for API-version pinning, pagination, and env filtering.

These exist because API version 20240415 paginates the list-flags endpoint
(default limit 20) and only returns `environments` when an `env` filter is
passed; a regression here silently truncates the warehouse to 20 flags.
"""

from unittest import mock
from urllib.parse import urlparse

from tap_launchdarkly.client import LD_API_VERSION, LaunchDarklyPaginator
from tap_launchdarkly.tap import TapLaunchDarkly


def _streams():
    tap = TapLaunchDarkly(
        config={"auth_token": "test-token", "environment": "production"},
        validate_config=False,
    )
    return {s.name: s for s in tap.discover_streams()}


def test_all_streams_pin_api_version():
    for stream in _streams().values():
        assert stream.http_headers["LD-API-Version"] == LD_API_VERSION


def test_paginator_follows_next_link_and_stops_without_one():
    paginator = LaunchDarklyPaginator()
    response = mock.Mock()

    response.json.return_value = {
        "_links": {"next": {"href": "/api/v2/flags/default?limit=100&offset=100"}}
    }
    assert paginator.get_next_url(response) == "/api/v2/flags/default?limit=100&offset=100"

    response.json.return_value = {"_links": {"self": {"href": "/api/v2/flags/default"}}}
    assert paginator.get_next_url(response) is None


def test_feature_flags_params_request_env_full_config_and_big_pages():
    ff = _streams()["feature_flags"]
    assert ff.get_url_params({"project_key": "default"}, None) == {
        "env": "production",
        "summary": 0,
        "limit": 100,
    }


def test_feature_flags_params_carry_pagination_continuation():
    ff = _streams()["feature_flags"]
    token = urlparse("/api/v2/flags/default?env=production&limit=100&offset=100&summary=0")
    params = ff.get_url_params({"project_key": "default"}, token)
    assert params["offset"] == "100"
    assert params["env"] == "production"
    assert params["summary"] == 0
    assert params["limit"] == 100


def test_feature_flag_targets_params_filter_environment():
    tg = _streams()["feature_flag_targets"]
    assert tg.get_url_params({}, None) == {"env": "production"}
