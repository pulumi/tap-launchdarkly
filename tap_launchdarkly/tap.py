"""LaunchDarkly tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_launchdarkly import streams


class TapLaunchDarkly(Tap):
    """LaunchDarkly tap class."""

    name = "tap-launchdarkly"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "environment",
            th.StringType,
            required=True,
            default='production',
            description="Which environment to get activation data for (Usually a production environment)",
        )
    ).to_dict()

    def discover_streams(self) -> list[streams.LaunchDarklyStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.ProjectsStream(self),
            streams.FeatureFlags(self),
            streams.FeatureFlagTargets(self)
        ]


if __name__ == "__main__":
    TapLaunchDarkly.cli()
