"""Stream type classes for tap-launchdarkly."""

from __future__ import annotations

import requests
from pathlib import Path
from typing import Dict, Optional, Iterable

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers.jsonpath import extract_jsonpath
from itertools import izip

from tap_launchdarkly.client import LaunchDarklyStream

class ProjectsStream(LaunchDarklyStream):
    """Define custom stream."""

    name = "projects"
    path = "/projects"
    primary_keys = ["_id"]

    records_jsonpath = "$.items[*]"
    replication_key = None
    schema = th.PropertiesList(
        th.Property("_id", th.StringType),
        th.Property("key", th.StringType),
        th.Property("includeInSnippetByDefault", th.BooleanType),
        th.Property("defaultClientSideAvailability", th.ObjectType(
            th.Property("usingMobileKey", th.BooleanType),
            th.Property("usingEnvironmentId", th.BooleanType)
        )),
        th.Property("name", th.StringType),
        th.Property("tags", th.ArrayType(th.StringType))
    ).to_dict()

    def get_child_context(self, record: Dict, context: Optional[Dict]) -> dict:
        return {
            "project_key": record["key"],
        }


class FeatureFlags(LaunchDarklyStream):
    """Define custom stream."""

    name = "feature_flags"
    path = "/flags/{project_key}"
    parent_stream_type = ProjectsStream
    primary_keys = ["project_key", "key"]

    records_jsonpath = "$.items[*]"
    replication_key = None

    @property
    def schema(self):
        return th.PropertiesList(
        th.Property("project_key", th.StringType),
        th.Property("key", th.StringType),
        th.Property("name", th.StringType),
        th.Property("_version", th.IntegerType),
        th.Property("creationDate", th.IntegerType),
        th.Property("includeInSnippet", th.BooleanType),
        th.Property("clientSideAvailability", th.ObjectType(
            th.Property("usingMobileKey", th.BooleanType),
            th.Property("usingEnvironmentId", th.BooleanType)
        )),
        th.Property("variations", th.ArrayType(th.ObjectType(
            th.Property("_id", th.StringType),
            th.Property("value", th.BooleanType)
        ))),
        th.Property("temporary", th.BooleanType),
        th.Property("archived", th.BooleanType),
        th.Property("archivedDate", th.IntegerType),
        th.Property("maintainerId", th.StringType),
        th.Property("maintainerTeamKey", th.StringType),
        th.Property("defaults", th.ObjectType(
            th.Property("onVariation", th.IntegerType),
            th.Property("offVariation", th.IntegerType)
        )),
        th.Property("environments", th.ObjectType(
            th.Property(self.config.get("environment", ""), th.ObjectType(
                th.Property("on", th.BooleanType),
                th.Property("offVariation", th.IntegerType)
            ))
        )),
        th.Property("tags", th.ArrayType(th.StringType))
    ).to_dict()

    def get_child_context(self, record: Dict, context: Optional[Dict]) -> dict:
        return {
            "project_key": context["project_key"] if context else None,
            "feature_flag_key": record["key"],
        }

class FeatureFlagTargets(LaunchDarklyStream):
    """Define custom stream."""

    name = "feature_flag_targets"
    path = "/flags/{project_key}/{feature_flag_key}"
    parent_stream_type = FeatureFlags
    primary_keys = ["project_key", "feature_flag_key", "target"]

    @property
    def records_jsonpath(self):
        environment = self.config.get("environment", "")
        return f"$.environments.{environment}.targets[*]"
    
    @property
    def contextTargets_jsonpath(self):
        environment = self.config.get("environment", "")
        return f"$.environments.{environment}.contextTargets[*]"

    
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        targets = extract_jsonpath(self.records_jsonpath, input=response.json())
        contextTargets = extract_jsonpath(self.contextTargets_jsonpath, input=response.json())
        for target in izip(targets, contextTargets):
            variation = target['variation']
            contextKind = target['contextKind']
            for value in target['values']:
                yield {"variation": variation, "contextKind": contextKind, "target": value}

    replication_key = None
    schema = th.PropertiesList(
        th.Property("project_key", th.StringType),
        th.Property("feature_flag_key", th.StringType),
        th.Property("target", th.StringType),
        th.Property("variation", th.IntegerType),
        th.Property("contextKind", th.StringType)
    ).to_dict()
