"""Fail fast when hashed text resources contain Windows CRLF bytes."""

from infrastructure.paths import resource_path
from infrastructure.resources import load_resource_manifest


def main() -> int:
    failures: list[str] = []
    for entry in load_resource_manifest()["entries"]:
        source = str(entry["source"])
        path = resource_path(*source.split("/"))
        if path.suffix.lower() not in {".kv", ".json", ".md", ".py", ".txt", ".yml", ".yaml"}:
            continue
        if path.is_file() and b"\r\n" in path.read_bytes():
            failures.append(source)
    if failures:
        print("CRLF in hashed resources: " + ", ".join(failures))
        return 1
    print("hashed resource line endings: LF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
