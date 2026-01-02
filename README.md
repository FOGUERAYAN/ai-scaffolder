# The AI Scaffolder

**The AI Scaffolder** est un outil en ligne de commande (CLI) conçu pour accélérer l'initialisation de projets logiciels et automatiser les tâches de maintenance de code grâce à l'Intelligence Artificielle.

![Status](https://img.shields.io/badge/Status-Stable-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)
![OpenAI](https://img.shields.io/badge/AI-OpenAI_API-green?style=flat-square)

---

## Présentation

Ce projet répond à une problématique d'efficacité dans les workflows de développement :
1.  **Standardisation :** Génération déterministe de structures de projets via des fichiers de configuration JSON.
2.  **Assistance IA :** Traduction de besoins fonctionnels (ex: "Je veux une API Flask") en configuration technique.
3.  **Refactoring Automatisé ("Vibe Coding") :** Pipeline de traitement de fichiers pour appliquer des modifications de code ou générer de la documentation technique de manière contextuelle.

---

## Fonctionnalités Principales

### 1. Moteur de Scaffolding
Génération récursive d'arborescences de fichiers (dossiers et fichiers vides) basée sur un schéma JSON strict.

*Commande :*

python src/main.py scaffold template.json

### 2. Générateur de Templates(AI-Driven)
Utilisation du modèle GPT pour convertir une description en langage naturel en un fichier de configuration template.json valide et exploitable par le moteur.

*Commande :*

python src/main.py suggest "Description_de_ce_que_vous_voulez"

### 3. Pipeline de Transformation ("Vibe Coding")
Analyse et modification de code source existant. L'outil injecte le contexte de plusieurs fichiers et des instructions spécifiques dans le LLM pour produire un résultat consolidé (Code refactorisé, Tests unitaires, Documentation).

*Commande :*

python src/main.py vibe instructions.md --in src/main.py --out audit_result.md

## Installation et Configuration

### Prérequis : 
Python 3.8 ou supérieur.

Une clé API OpenAI active (Optionnel : un mode "Mock" est intégré pour les tests sans clé).

### Procédure de déploiement

*Cloner le dépôt :*

1 : git clone [https://github.com/VOTRE_USERNAME/ai-scaffolder.git](https://github.com/VOTRE_USERNAME/ai-scaffolder.git)
2 : cd ai-scaffolder

*Configurer l'environnement virtuel :*

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac

*Installer les dépendances :*

pip install -r requirements.txt

*Configuration des variables d'environnement :*

Créez un fichier .env à la racine du projet :
collez cette ligne en remplacent avec votre clé d'API
OPENAI_API_KEY=sk-votre-cle-api-ici

### Architecture du projet
Le projet respecte une séparation claire des responsabilités : 
ai-scaffolder/
├── ai-meta/            # Documentation des prompts système
├── assets/             # Ressources visuelles pour la documentation
├── src/
│   ├── ai.py           # Module d'interface avec l'API OpenAI 
│   ├── main.py         # Point d'entrée CLI et orchestration 
├── .env                # Variables sensibles (Car contient ma clé d'API privé). Ignoré par Git
├── template.json       # Modèle de configuration par défaut
└── requirements.txt    # Liste des dépendances Python

## Conception Technique
*CLI Robustness :* Utilisation de Typer pour une gestion stricte des arguments et des types.

*Sécurité :* Gestion des clés API via variables d'environnement (python-dotenv) pour éviter toute fuite dans le code source.

*Algorithmique :* Implémentation récursive pour la gestion de la profondeur infinie des dossiers lors du scaffolding.

*Auteur :* Rayan FOGUE Développé dans le cadre d'un test technique d'ingénierie logicielle.