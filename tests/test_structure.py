import sys
from pathlib import Path

# make sure src is importable
sys.path.insert(0, str((Path(__file__).parents[1] / "src").resolve()))

from main import create_structure_recursive

def test_create_structure(tmp_path):
    struct = {
        "app": ["__init__.py", {"main.py": "print(\"ok\")"}],
        "docs": {"README.md": "# docs"},
    }
    base = tmp_path / "project"
    base.mkdir()
    create_structure_recursive(base, struct)

    assert (base / "app" / "__init__.py").exists()
    assert (base / "app" / "main.py").exists()
    assert (base / "docs" / "README.md").exists()