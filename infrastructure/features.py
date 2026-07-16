"""Typed feature flags created once at the client composition root."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlags:
    classroom_enabled: bool = False
    sync_enabled: bool = False
    stealth_assessment_enabled: bool = False

    @classmethod
    def local_release(cls) -> "FeatureFlags":
        return cls()
