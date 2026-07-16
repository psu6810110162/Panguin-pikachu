"""CLI wrapper for CI/startup resource validation."""

import argparse

from infrastructure.resources import validate_resources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    report = validate_resources(require_release_licenses=args.release)
    print(
        f"validated {report.checked} resources; "
        f"optional missing={len(report.optional_missing)}; "
        f"pending licenses={len(report.pending_licenses)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
