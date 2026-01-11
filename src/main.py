"""
THE AI SCAFFOLDER - Version améliorée 
Auteur: Rayan FOGUE 
Date: 2026-01-11
"""
import shutil
import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Union

import typer

from ai import generate_template_from_prompt, vibe_check

app = typer.Typer(
    name="ai-scaffolder",
    help="Générateur de projets intelligent propulsé par l'IA.",
    add_completion=False
)


def create_structure_recursive(base_path: Path, structure: dict, level: int = 0):
    """
    Parcourt récursivement le dictionnaire pour créer dossiers et fichiers.
    Accepts structure values:
      - list[str] -> create files with those names (empty)
      - dict -> subdirectory
      - dict where file name maps to string content -> writes the file with that content
    Example structure:
    {
      "src": ["__init__.py", "main.py"],
      "docs": {
         "README.md": "# Docs",
         "examples": ["ex1.py"]
      }
    }
    """
    indent = "  " * level

    for name, content in structure.items():
        current_path = base_path / name

        # Si content est une liste de noms de fichiers (ou d'objets simples)
        if isinstance(content, list):
            try:
                current_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                typer.secho(f"{indent}Erreur création dossier {current_path}: {e}", fg=typer.colors.RED)
                continue

            typer.secho(f"{indent}{name}/", fg=typer.colors.BLUE)
            for item in content:
                # item peut être un str (nom de fichier) ou un dict {filename: content}
                if isinstance(item, str):
                    file_path = current_path / item
                    try:
                        if not file_path.exists():
                            file_path.write_text("", encoding="utf-8")
                            typer.secho(f"{indent}  {item}", fg=typer.colors.WHITE)
                        else:
                            typer.secho(f"{indent}  {item} (existe)", fg=typer.colors.YELLOW)
                    except Exception as e:
                        typer.secho(f"{indent}  Erreur création {item}: {e}", fg=typer.colors.RED)
                elif isinstance(item, dict):
                    # dict dans une liste -> créer fichiers avec contenu
                    for fname, fcontent in item.items():
                        file_path = current_path / fname
                        try:
                            file_path.write_text(str(fcontent), encoding="utf-8")
                            typer.secho(f"{indent}  {fname}", fg=typer.colors.WHITE)
                        except Exception as e:
                            typer.secho(f"{indent}  Erreur écriture {fname}: {e}", fg=typer.colors.RED)

        elif isinstance(content, dict):
            # Peut s'agir d'un sous-dossier ou d'un mapping nom_fichier -> contenu
            # Détecter si le dict est un mapping de fichiers (tous les clés contiennent un point)
            if all("." in k or k.startswith(".") for k in content.keys()):
                # Considérer current_path comme dossier ; créer et écrire fichiers selon les valeurs
                try:
                    current_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    typer.secho(f"{indent}Erreur création dossier {current_path}: {e}", fg=typer.colors.RED)
                    continue

                typer.secho(f"{indent}{name}/", fg=typer.colors.BLUE)
                for fname, fcontent in content.items():
                    file_path = current_path / fname
                    try:
                        file_path.write_text(str(fcontent), encoding="utf-8")
                        typer.secho(f"{indent}  {fname}", fg=typer.colors.WHITE)
                    except Exception as e:
                        typer.secho(f"{indent}  Erreur écriture {fname}: {e}", fg=typer.colors.RED)
            else:
                # Sous-dossier classique (récursivité)
                try:
                    current_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    typer.secho(f"{indent}Erreur création dossier {current_path}: {e}", fg=typer.colors.RED)
                    continue
                typer.secho(f"{indent}{name}/", fg=typer.colors.BLUE)
                create_structure_recursive(current_path, content, level + 1)
        else:
            # Cas inattendu
            typer.secho(f"{indent}Type inattendu pour {name}: {type(content)}", fg=typer.colors.YELLOW)


@app.command()
def scaffold(
    template_file: str = typer.Argument(..., help="Chemin vers le fichier JSON de configuration."),
    force: bool = typer.Option(False, "--force", "-f", help="Supprime le dossier cible s'il existe déjà.")
):
    """[ÉTAPE 1] Génère l'arborescence d'un projet à partir d'un fichier JSON."""
    json_path = Path(template_file)

    if not json_path.exists():
        typer.secho(f"Erreur : Le fichier '{template_file}' est introuvable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        typer.secho(f"Erreur de syntaxe JSON : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Erreur lecture {json_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    project_name = data.get("project_name")
    structure = data.get("structure")

    if not project_name or not isinstance(structure, dict):
        typer.secho("Format invalide : 'project_name' (string) et 'structure' (dict) sont requis.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    root_path = Path(project_name).resolve()

    # Sécurité : éviter d'écrire en dehors du cwd
    try:
        cwd = Path.cwd().resolve()
        if not str(root_path).startswith(str(cwd)):
            # autoriser si c'est explicitement ce que l'utilisateur veut ? pour l'instant, refuser
            typer.secho("Chemin projet invalide : sortie hors du répertoire courant non autorisée.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    except Exception:
        # fallback : continuer mais avertir
        pass

    if root_path.exists():
        if force:
            try:
                shutil.rmtree(root_path)
                typer.secho(f"Ancien dossier '{root_path}' supprimé (--force).", fg=typer.colors.YELLOW)
            except Exception as e:
                typer.secho(f"Erreur suppression {root_path}: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
        else:
            typer.secho(f"Le projet '{project_name}' existe déjà.", fg=typer.colors.YELLOW)
            if not typer.confirm("Voulez-vous continuer (cela peut écraser des fichiers) ?"):
                typer.secho("Opération annulée.", fg=typer.colors.YELLOW)
                raise typer.Exit()

    typer.secho(f"\nInitialisation du projet : {project_name}", fg=typer.colors.GREEN, bold=True)
    typer.echo("-" * 40)

    try:
        root_path.mkdir(parents=True, exist_ok=True)
        # Simple progress indicator for the long operation
        with typer.progressbar(length=1, label="Génération") as progress:
            create_structure_recursive(root_path, structure)
            time.sleep(0.2)
            progress.update(1)
    except Exception as e:
        typer.secho(f"Erreur durant la génération : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("-" * 40)
    typer.secho(f"Succès ! Projet disponible dans : {root_path}", fg=typer.colors.GREEN)


@app.command()
def version():
    """Affiche la version de l'outil."""
    typer.echo("AI Scaffolder v1.0.0 - (c) 2026 Rayan FOGUE")


@app.command()
def suggest(
    description: str = typer.Argument(..., help="Description du projet souhaité (ex: 'Site React avec Tailwind')"),
    output: str = typer.Option("template.json", "--output", "-o", help="Fichier de sortie pour le template")
):
    """
    [ÉTAPE 2] Génère un template JSON de projet basé sur une description utilisateur via l'IA.
    """
    typer.secho(f"L'IA réfléchit à ton projet : '{description}'...", fg=typer.colors.MAGENTA)

    try:
        with typer.progressbar(length=1, label="Génération IA") as progress:
            template_data = generate_template_from_prompt(description)
            progress.update(1)
    except Exception as e:
        typer.secho(f"Erreur appel IA : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not isinstance(template_data, dict):
        typer.secho("Échec de la génération IA : format inattendu.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # S'assurer que c'est sérialisable
    try:
        json.dumps(template_data)
    except TypeError as e:
        typer.secho(f"Le template généré n'est pas sérialisable en JSON : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    output_path = Path(output)
    try:
        output_path.write_text(json.dumps(template_data, indent=4, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        typer.secho(f"Erreur écriture {output_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"\nTemplate généré avec succès : {output_path}", fg=typer.colors.GREEN)
    typer.echo("Tu peux maintenant lancer la commande :")
    typer.secho(f"python src/main.py scaffold {output_path}", fg=typer.colors.CYAN, bold=True)


@app.command()
def vibe(
    instructions_file: str = typer.Argument(..., help="Fichier contenant les instructions (ex: refacto.md)"),
    files: List[Path] = typer.Option(..., "--files", "-i", help="Liste des fichiers à traiter (ex: --files a.py --files b.py)"),
    output_file: str = typer.Option("review.md", "--out", "-o", help="Fichier de sortie")
):
    """
    [ÉTAPE 3] Vibe Coding : Analyse ou transforme des fichiers via l'IA.
    """
    inst_path = Path(instructions_file)
    if not inst_path.exists():
        typer.secho(f"Erreur : Fichier d'instructions '{instructions_file}' introuvable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        instructions_text = inst_path.read_text(encoding="utf-8")
    except Exception as e:
        typer.secho(f"Erreur lecture {inst_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    files_content = {}
    typer.secho(f"Lecture de {len(files)} fichier(s)...", fg=typer.colors.CYAN)

    for file_path in files:
        try:
            p = Path(file_path)
            if not p.exists():
                typer.secho(f"Attention : Le fichier {p} n'existe pas (ignoré).", fg=typer.colors.YELLOW)
                continue
            files_content[p.name] = p.read_text(encoding="utf-8")
        except Exception as e:
            typer.secho(f"Erreur lecture {file_path}: {e}", fg=typer.colors.RED)

    if not files_content:
        typer.secho("Aucun fichier valide à traiter.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho("Analyse IA en cours (Vibe Check)...", fg=typer.colors.MAGENTA)
    try:
        result = vibe_check(instructions_text, files_content)
    except Exception as e:
        typer.secho(f"Erreur appel IA : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    out_path = Path(output_file)
    try:
        out_path.write_text(str(result), encoding="utf-8")
    except Exception as e:
        typer.secho(f"Erreur écriture résultat {out_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"\nTerminé ! Résultat sauvegardé dans : {out_path}", fg=typer.colors.GREEN, bold=True)


if __name__ == "__main__":
    app()