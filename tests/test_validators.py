import pytest
import sys
from pathlib import Path

# make sure src is importable
sys.path.insert(0, str((Path(__file__).parents[1] / "src").resolve()))

from validators import validate_template

def test_validate_ok_simple():
    data = {
        "project_name": "demo",
        "structure": {
            "src": ["main.py", {"readme.md": "# Hello"}],
            "tests": ["test_main.py"]
        }
    }
    validated = validate_template(data)
    assert validated["project_name"] == "demo"

def test_validate_nested_folder_ok():
    data = {
        "project_name": "demo2",
        "structure": {
            "pkg": {
                "module": ["__init__.py", {"impl.py": "print(1)"}]
            }
        }
    }
    validated = validate_template(data)
    assert "pkg" in validated["structure"]

def test_validate_bad_project_name():
    with pytest.raises(ValueError):
        validate_template({"structure": {}})

def test_validate_bad_structure_type():
    with pytest.raises(ValueError):
        validate_template({"project_name": "x", "structure": []})