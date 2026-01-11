"""THE AI SCAFFOLDER - Improved
Auteur: Rayan FOGUE (bases) + improvements
Date: 2026-01-11
"""

import shutil
import json
import time
import logging
from pathlib import Path
from typing import List, Union, Dict, Any

import typer

from ai import generate_template_from_prompt, vibe_check
from validators import validate_template

app = typer.Typer(
    name="ai-scaffolder",
    help="Générateur de projets intelligent propulsé par l'IA.",
    add_completion=False
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context, verbose: bool = typer.Option(False, "--verbose", "-v", help="Activer le logging verbeux")):
    """Global callback to setup logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# --- UTILS ---

def count_structure_items(structure: Dict[str, Any]) -> int:
    """Compte approximativement le nombre total d'éléments (fichiers) à créer pour la barre de progression."""
    count = 0
    for _, content in structure.items():
        if isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    count += 1
                elif isinstance(item, dict):
                    count += len(item)
        elif isinstance(content, dict):
            # si le dict ressemble à un mapping fichier->contenu
            if all(("." in k or k.startswith(".")) for k in content.keys()):
                count += len(content)
            else:
                count += count_structure_items(content)
    return count

def create_structure_recursive(base_path: Path, structure: Dict[str, Any], progress: Union[None, typer.models.ProgressBar] = None):
    """Parcourt récursivement le dictionnaire pour créer dossiers et fichiers.

    Le schema accepté est flexible :
      - valeur list[str] -> crée des fichiers vides
      - valeur list[dict] -> crée fichier(s) avec contenu: [{"file.py": "content"}]
      - valeur dict -> soit sous-dossier, soit mapping fichier->contenu
    """
    for name, content in structure.items():
        current_path = base_path / name
        try:
            current_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error("Échec création dossier %s: %s", current_path, e)
            continue

        logging.info("Création dossier: %s/", current_path)

        if isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    file_path = current_path / item
                    try:
                        if not file_path.exists():
                            file_path.write_text("", encoding="utf-8")
                            logging.debug("Créé fichier: %s", file_path)
                        else:
                            logging.debug("Fichier existe: %s", file_path)
                    except Exception as e:
                        logging.error("Erreur écriture %s: %s", file_path, e)
                    if progress:
                        progress.update(1)
                elif isinstance(item, dict):
                    for fname, fcontent in item.items():
                        file_path = current_path / fname
                        try:
                            file_path.write_text(str(fcontent), encoding="utf-8")
                            logging.debug("Écrit fichier: %s", file_path)
                        except Exception as e:
                            logging.error("Erreur écriture %s: %s", file_path, e)
                        if progress:
                            progress.update(1)
                else:
                    logging.warning("Item inattendu dans la liste pour %s: %s", name, type(item))

        elif isinstance(content, dict):
            # determine if dict maps filenames -> contents
            if all(("." in k or k.startswith(".")) for k in content.keys()):
                # mapping de fichiers
                for fname, fcontent in content.items():
                    file_path = current_path / fname
                    try:
                        file_path.write_text(str(fcontent), encoding="utf-8")
                        logging.debug("Écrit fichier: %s", file_path)
                    except Exception as e:
                        logging.error("Erreur écriture %s: %s", file_path, e)
                    if progress:
                        progress.update(1)
            else:
                # sous-dossier -> récursivité
                create_structure_recursive(current_path, content, progress)
        else:
            logging.warning("Type inattendu pour %s: %s", name, type(content))


@app.command()
def scaffold(
    template_file: str = typer.Argument(..., help="Chemin vers le fichier JSON de configuration."),
    force: bool = typer.Option(False, "--force", "-f", help="Supprime le dossier cible s'il existe déjà."),
):
    """[ÉTAPE 1] Génère l'arborescence d'un projet à partir d'un fichier JSON."""
    json_path = Path(template_file)

    if not json_path.exists():
        typer.secho(f"Erreur : Le fichier '{template_file}' est introuvable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        typer.secho(f"Erreur de syntaxe JSON : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Erreur lecture {json_path}: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # validation
    try:
        validated = validate_template(data)
    except ValueError as e:
        typer.secho(f"Template invalide : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    project_name = validated["project_name"]
    structure = validated["structure"]

    root_path = Path(project_name).resolve()

    # sécurité : empêcher d'écrire en dehors du cwd
    cwd = Path.cwd().resolve()
    try:
        if not str(root_path).startswith(str(cwd)):
            typer.secho("Chemin projet invalide : sortie hors du répertoire courant non autorisée.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    except Exception:
        pass

    if root_path.exists():
        if force:
            try:
                shutil.rmtree(root_path)
                logging.warning("Ancien dossier '%s' supprimé (--force).", root_path)
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

        total = max(1, count_structure_items(structure))
        with typer.progressbar(length=total, label="Génération") as progress:
            create_structure_recursive(root_path, structure, progress)
            # ensure progress is complete
            remaining = total - progress.current
            if remaining > 0:
                progress.update(remaining)

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
    """[ÉTAPE 2] Génère un template JSON de projet basé sur une description utilisateur via l'IA."""
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
    """[ÉTAPE 3] Vibe Coding : Analyse ou transforme des fichiers via l'IA."""
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
        p = Path(file_path)
        if not p.exists():
            typer.secho(f"Attention : Le fichier {p} n'existe pas (ignoré).", fg=typer.colors.YELLOW)
            continue
        try:
            files_content[p.name] = p.read_text(encoding="utf-8")
        except Exception as e:
            typer.secho(f"Erreur lecture {p}: {e}", fg=typer.colors.RED)

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