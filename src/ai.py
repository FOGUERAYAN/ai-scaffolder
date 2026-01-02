import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_ai_client():
    """Récupère le client OpenAI de manière sécurisée."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def generate_template_from_prompt(user_description: str) -> dict:
    """
    Envoie la description à l'IA et retourne un dictionnaire (JSON) structuré.
    """
    client = get_ai_client()
    
    # Mode MOCK (Si pas de clé API détectée)
    if not client:
        print("  Aucune clé API trouvée (.env). Mode simulation activé.")
        return {
            "project_name": "mock-project",
            "structure": {
                "src": ["main.mock.py", "utils.mock.py"],
                "README.md": []
            }
        }

    # Le Prompt Système
    system_prompt = """
    Tu es un architecte logiciel expert. Ton rôle est de générer une structure de projet JSON basée sur la demande de l'utilisateur.
    
    Règles strictes :
    1. Tu dois répondre UNIQUEMENT avec un objet JSON valide. Pas de texte avant, pas de texte après (pas de ```json).
    2. Le JSON doit suivre exactement ce format :
    {
        "project_name": "nom-du-projet-pertinent",
        "structure": {
            "nom_dossier": ["fichier1.ext", "fichier2.ext"],
            "autre_dossier": { "sous_dossier": ["fichier.ext"] }
        }
    }
    3. Choisis des technologies modernes et adaptées à la demande.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Génère un projet pour : {user_description}"}
            ],
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        
        # Nettoyage au cas où l'IA ajoute des backticks ```json ... ```
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "")
            
        return json.loads(content)

    except Exception as e:
        print(f" Erreur OpenAI : {e}")
        return None