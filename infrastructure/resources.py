"""Validate versioned runtime resources before gameplay begins."""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from infrastructure.paths import resource_path

MANIFEST_SCHEMA_VERSION = 1
PENDING_LICENSE = "LicenseRef-PendingReview"


class ResourceValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResourceValidationReport:
    checked: int
    optional_missing: tuple[str, ...]
    pending_licenses: tuple[str, ...]


def _validate_relative_path(value: str, *, field: str, resource_id: str) -> None:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ResourceValidationError(f"unsafe {field} for {resource_id}: {value!r}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ResourceValidationError(f"not a valid PNG header: {path}")
    return struct.unpack(">II", header[16:24])


def _validate_font(path: Path) -> None:
    if path.read_bytes()[:4] not in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"}:
        raise ResourceValidationError(f"unsupported font signature: {path}")


def _validate_audio(path: Path, expected: str) -> None:
    header = path.read_bytes()[:12]
    if expected == "ogg" and header[:4] != b"OggS":
        raise ResourceValidationError(f"invalid OGG header: {path}")
    valid_mp3 = header[:3] == b"ID3" or header[:2] in {b"\xff\xfb", b"\xff\xf3"}
    if expected == "mp3" and not valid_mp3:
        raise ResourceValidationError(f"invalid MP3 header: {path}")
    if expected == "wav" and not (header[:4] == b"RIFF" and header[8:12] == b"WAVE"):
        raise ResourceValidationError(f"invalid WAV header: {path}")


def _validate_balance(path: Path, schema_source: str) -> None:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    with resource_path(*schema_source.split("/")).open(encoding="utf-8") as handle:
        schema = json.load(handle)
    if schema.get("type") != "object" or not isinstance(payload, dict):
        raise ResourceValidationError(f"{path} must be an object")
    required_keys = set(schema.get("required", []))
    existing = set(payload) if isinstance(payload, dict) else set()
    if not required_keys.issubset(existing):
        raise ResourceValidationError(
            f"{path} violates {schema_source}; missing {sorted(required_keys - existing)}"
        )
    expected_types: dict[str, type[Any] | tuple[type[Any], ...]] = {
        "array": list,
        "integer": int,
        "number": (int, float),
        "object": dict,
        "string": str,
    }
    for key, rule in schema.get("properties", {}).items():
        if key not in payload or "type" not in rule:
            continue
        expected = expected_types.get(rule["type"])
        if expected is not None and not isinstance(payload[key], expected):
            raise ResourceValidationError(f"{path}: {key} must be {rule['type']}")
        if isinstance(payload[key], list) and len(payload[key]) < int(rule.get("minItems", 0)):
            raise ResourceValidationError(f"{path}: {key} has too few items")


def load_resource_manifest() -> dict[str, Any]:
    with resource_path("resource_manifest.json").open(encoding="utf-8") as handle:
        manifest: dict[str, Any] = json.load(handle)
    return manifest


def validate_resources(*, require_release_licenses: bool = False) -> ResourceValidationReport:
    manifest = load_resource_manifest()
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ResourceValidationError("unsupported resource manifest schema")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ResourceValidationError("resource manifest entries must be a list")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    optional_missing: list[str] = []
    pending_licenses: list[str] = []
    checked = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise ResourceValidationError("resource entry must be an object")
        resource_id = str(entry.get("id", ""))
        source = str(entry.get("source", ""))
        bundle_path = str(entry.get("bundle_path", ""))
        folded = source.casefold()
        if not resource_id or resource_id in seen_ids:
            raise ResourceValidationError(f"duplicate or empty resource id: {resource_id}")
        if not source or folded in seen_paths:
            raise ResourceValidationError(f"duplicate or empty resource path: {source}")
        seen_ids.add(resource_id)
        seen_paths.add(folded)
        _validate_relative_path(source, field="source", resource_id=resource_id)
        _validate_relative_path(bundle_path, field="bundle_path", resource_id=resource_id)

        if not entry.get("license") or not entry.get("credit_ref"):
            raise ResourceValidationError(f"missing license metadata: {resource_id}")
        if entry["license"] == PENDING_LICENSE:
            pending_licenses.append(resource_id)

        path = resource_path(*source.split("/"))
        if not path.is_file():
            if entry.get("required", False):
                raise ResourceValidationError(f"required resource is missing: {source}")
            optional_missing.append(resource_id)
            continue
        if _sha256(path) != entry.get("sha256"):
            raise ResourceValidationError(f"checksum mismatch: {source}")

        kind = entry.get("kind")
        if kind == "image":
            dimensions = tuple(entry.get("dimensions", ()))
            if _png_dimensions(path) != dimensions:
                raise ResourceValidationError(f"image dimensions mismatch: {source}")
            frame_size = entry.get("frame_size")
            if frame_size and (
                dimensions[0] % frame_size[0] != 0 or dimensions[1] % frame_size[1] != 0
            ):
                raise ResourceValidationError(f"sprite frame does not tile image: {source}")
        elif kind == "font":
            _validate_font(path)
        elif kind == "audio":
            _validate_audio(path, str(entry.get("format")))
        elif kind == "balance":
            schema_source = str(entry.get("json_schema", ""))
            if not schema_source:
                raise ResourceValidationError(f"balance schema missing: {resource_id}")
            _validate_relative_path(
                schema_source,
                field="json_schema",
                resource_id=resource_id,
            )
            _validate_balance(path, schema_source)
        checked += 1

    if require_release_licenses and pending_licenses:
        raise ResourceValidationError(
            f"release-blocking license review: {', '.join(sorted(pending_licenses))}"
        )
    return ResourceValidationReport(
        checked=checked,
        optional_missing=tuple(optional_missing),
        pending_licenses=tuple(pending_licenses),
    )
