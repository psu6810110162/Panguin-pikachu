import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_controller_has_no_framework_persistence_or_server_dependency():
    imports = _imports(ROOT / "game" / "controller.py")
    forbidden = ("kivy", "sqlite3", "server", "infrastructure", "flask", "game.grid")
    assert not {name for name in imports if name.startswith(forbidden)}


def test_client_entry_point_does_not_import_server():
    assert not {name for name in _imports(ROOT / "main.py") if name.startswith("server")}


def test_ui_components_do_not_import_mutable_domain_objects():
    forbidden = {"core.session", "core.schema", "core.state", "core.items", "game.grid"}
    for path in (ROOT / "ui").rglob("*.py"):
        assert not (_imports(path) & forbidden), path


def test_run_record_event_list_has_one_production_append_site():
    offenders = []
    for folder in ("core", "game", "screens", "ui"):
        for path in (ROOT / folder).rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if ".events.append(" in source and path != ROOT / "core" / "schema.py":
                offenders.append(path.relative_to(ROOT))
    assert offenders == []


def test_release_game_code_contains_no_debt_markers():
    markers = ("TODO", "FIXME", "HACK", "XXX")
    offenders = []
    for target in ("main.py", "core", "game", "screens", "ui"):
        path = ROOT / target
        files = [path] if path.is_file() else path.rglob("*.py")
        for file in files:
            if any(marker in file.read_text(encoding="utf-8") for marker in markers):
                offenders.append(file.relative_to(ROOT))
    assert offenders == []
