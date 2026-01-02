"""
THE AI SCAFFOLDER
Outil CLI pour générer des structures de projets et de la documentation.
Auteur: Rayan FOGUE
Date: 02/01/2026
"""

import typer
import json
import time
from pathlib import Path
from typing import Optional
from ai import generate_template_from_prompt, vibe_check
from typing import List

# Configuration de l'application avec des métadonnées
app = typer.Typer(
    name="ai-scaffolder",
    help=" Générateur de projets intelligent propulsé par l'IA.",
    add_completion=False
)

# --- FONCTIONS UTILITAIRES ---

def create_structure_recursive(base_path: Path, structure: dict, level: int = 0):
    """
    Parcourt récursivement le dictionnaire pour créer dossiers et fichiers.
    """
    indent = "  " * level
    
    for name, content in structure.items():
        current_path = base_path / name
        
        # Cas 1 : Liste = Dossier contenant des fichiers
        if isinstance(content, list):
            current_path.mkdir(parents=True, exist_ok=True)
            typer.secho(f"{indent} {name}/", fg=typer.colors.BLUE)
            
            for filename in content:
                file_path = current_path / filename
                if not file_path.exists():
                    file_path.touch()
                    typer.secho(f"{indent}   {filename}", fg=typer.colors.WHITE)
        
        # Cas 2 : Dictionnaire = Sous-dossier (Récursivité)
        elif isinstance(content, dict):
            current_path.mkdir(parents=True, exist_ok=True)
            typer.secho(f"{indent} {name}/", fg=typer.colors.BLUE)
            create_structure_recursive(current_path, content, level + 1)

# --- COMMANDES DU CLI ---

@app.command()
def scaffold(
    template_file: str = typer.Argument(..., help="Chemin vers le fichier JSON de configuration."),
    force: bool = typer.Option(False, "--force", "-f", help="Écrase le dossier s'il existe déjà.")
):
    """
    [ÉTAPE 1] Génère l'arborescence d'un projet à partir d'un fichier JSON.
    """
    json_path = Path(template_file)

    # 1. Validation du fichier d'entrée
    if not json_path.exists():
        typer.secho(f" Erreur : Le fichier '{template_file}' est introuvable.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 2. Parsing du JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        typer.secho(f" Erreur de syntaxe JSON : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # 3. Extraction des données
    project_name = data.get("project_name")
    structure = data.get("structure")

    if not project_name or not structure:
        typer.secho(" Format invalide : 'project_name' et 'structure' sont requis.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    root_path = Path(project_name)

    # 4. Gestion de l'existant
    if root_path.exists() and not force:
        typer.secho(f"  Le projet '{project_name}' existe déjà.", fg=typer.colors.YELLOW)
        if not typer.confirm("Voulez-vous continuer (cela peut écraser des fichiers) ?"):
            typer.secho("Opération annulée.", fg=typer.colors.YELLOW)
            raise typer.Exit()
    
    # 5. Exécution 
    typer.secho(f"\n Initialisation du projet : {project_name}", fg=typer.colors.GREEN, bold=True)
    typer.echo("-" * 40)
    
    root_path.mkdir(exist_ok=True)
    
    # Barre de chargement
    with typer.progressbar(length=100, label="Génération en cours") as progress:
        create_structure_recursive(root_path, structure)
        time.sleep(0.5) 
        progress.update(100)

    typer.echo("-" * 40)
    typer.secho(f" Succès ! Projet disponible dans : ./{project_name}", fg=typer.colors.GREEN)


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
    typer.secho(f" L'IA réfléchit à ton projet : '{description}'...", fg=typer.colors.MAGENTA)
    
    # Appel à l'IA (src/ai.py)
    with typer.progressbar(range(100), label="Génération") as progress:
        template_data = generate_template_from_prompt(description)
        progress.update(100)

    if not template_data:
        typer.secho(" Échec de la génération IA.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Sauvegarde du résultat
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template_data, f, indent=4)

    typer.secho(f"\n Template généré avec succès : {output_path}", fg=typer.colors.GREEN)
    typer.echo("Tu peux maintenant lancer la commande :")
    typer.secho(f"python src/main.py scaffold {output_path}", fg=typer.colors.CYAN, bold=True)


@app.command()
def vibe(
    instructions_file: str = typer.Argument(..., help="Fichier contenant les instructions (ex: refacto.md)"),
    files: List[Path] = typer.Option(..., "--in", "-i", help="Liste des fichiers à traiter"),
    output_file: str = typer.Option("review.md", "--out", "-o", help="Fichier de sortie")
):
    """
    [ÉTAPE 3] Vibe Coding : Analyse ou transforme des fichiers via l'IA.
    """
    # 1. Lecture des instructions
    inst_path = Path(instructions_file)
    if not inst_path.exists():
        typer.secho(f" Erreur : Fichier d'instructions '{instructions_file}' introuvable.", fg=typer.colors.RED)
        raise typer.Exit(1)
    
    with open(inst_path, "r", encoding="utf-8") as f:
        instructions_text = f.read()

    # 2. Lecture des fichiers sources (--in)
    files_content = {}
    typer.secho(f" Lecture de {len(files)} fichier(s)...", fg=typer.colors.CYAN)
    
    for file_path in files:
        if not file_path.exists():
            typer.secho(f"  Attention : Le fichier {file_path} n'existe pas (ignoré).", fg=typer.colors.YELLOW)
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                files_content[file_path.name] = f.read()
        except Exception as e:
            typer.secho(f" Erreur lecture {file_path.name}: {e}", fg=typer.colors.RED)

    if not files_content:
        typer.secho(" Aucun fichier valide à traiter.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # 3. Appel à l'IA
    typer.secho(" Analyse IA en cours (Vibe Check)...", fg=typer.colors.MAGENTA, blink=True)
    
    result = vibe_check(instructions_text, files_content)

    # 4. Écriture du résultat
    out_path = Path(output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)

    typer.secho(f"\n Terminé ! Résultat sauvegardé dans : {out_path}", fg=typer.colors.GREEN, bold=True)


if __name__ == "__main__":
    app()