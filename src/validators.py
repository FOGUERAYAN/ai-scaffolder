"""Simple template validator used by src/main.py
This avoids adding a runtime dependency (jsonschema/pydantic). It performs
minimal shape checks and raises ValueError with a clear message on failure.
"""
from typing import Any, Dict

def _validate_structure(structure: Any, path: str = "structure") -> None:
    if not isinstance(structure, dict):
        raise ValueError(f"{path} doit être un dictionnaire.")

    for key, value in structure.items():
        if not isinstance(key, str):
            raise ValueError(f"Clé de {path} invalide: {key} (doit être string)")

        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str):
                    continue
                if isinstance(item, dict):
                    # each dict should map filename->content
                    for fname in item.keys():
                        if not isinstance(fname, str):
                            raise ValueError(f"Nom de fichier invalide dans {path}.{key}[{i}]: {fname}")
                else:
                    raise ValueError(f"Element invalide dans la liste {path}.{key}[{i}]: {type(item)}")

        elif isinstance(value, dict):
            # could be a mapping file->content OR a nested folder
            for subkey in value.keys():
                if not isinstance(subkey, str):
                    raise ValueError(f"Clé invalide dans {path}.{key}: {subkey}")
            # Heuristic: if keys look like filenames (contain a dot) consider as files mapping
            if all(("." in k or k.startswith('.')) for k in value.keys()):
                # fine, values can be any primitive
                continue
            else:
                # nested folder
                _validate_structure(value, path=f"{path}.{key}")
        else:
            raise ValueError(f"Valeur invalide pour {path}.{key} : {type(value)}")

def validate_template(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Le template doit être un objet JSON.")

    project_name = data.get("project_name")
    structure = data.get("structure")

    if not project_name or not isinstance(project_name, str):
        raise ValueError("'project_name' est requis et doit être une chaîne.")

    if structure is None:
        raise ValueError("'structure' est requis.")

    _validate_structure(structure)

    return {"project_name": project_name, "structure": structure}