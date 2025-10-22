"""
Module de gestion de projets et de tâches pour l'assistant Whisp
"""

import os
import datetime
import json
import re
import subprocess
from text_processing import ecrire_texte_avec_accents

try:
    # Essayer d'abord l'import en tant que package
    from whisp_assistant.database_manager import ensure_connection
except ImportError:
    # Sinon, utiliser l'import relatif
    from database_manager import ensure_connection

@ensure_connection
def load_tasks(conn):
    """Charge les tâches depuis la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT
    )
    ''')
    conn.commit()
    
    # Charger les tâches
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    
    tasks_data = {"tasks": []}
    for row in rows:
        tasks_data["tasks"].append({
            "id": row["id"],
            "description": row["description"],
            "status": row["status"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"]
        })
    
    return tasks_data

@ensure_connection
def save_tasks(conn, tasks_data):
    """Enregistre les tâches dans la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed_at TEXT
    )
    ''')
    
    # Supprimer toutes les tâches existantes
    cursor.execute("DELETE FROM tasks")
    
    # Insérer les nouvelles tâches
    for task in tasks_data["tasks"]:
        cursor.execute(
            "INSERT INTO tasks (id, description, status, created_at, completed_at) VALUES (?, ?, ?, ?, ?)",
            (
                task["id"],
                task["description"],
                task["status"],
                task["created_at"],
                task["completed_at"]
            )
        )
    
    conn.commit()

def executer_commande_projet(texte):
    """Exécute des commandes de gestion de projet en fonction du texte transcrit"""
    texte = texte.lower()
    
    # ===== GESTION DES TÂCHES =====
    if "ajoute tâche" in texte or "nouvelle tâche" in texte or "crée tâche" in texte:
        # Extraire la description de la tâche
        match = re.search(r"(?:tâche|todo)\s+(?:nommée|appelée|:)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            task_desc = match.group(1).strip()
            
            # Charger les tâches existantes
            tasks_data = load_tasks()
            
            # Créer une nouvelle tâche
            new_task = {
                "id": len(tasks_data["tasks"]) + 1,
                "description": task_desc,
                "status": "à faire",
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "completed_at": None
            }
            
            # Ajouter la tâche
            tasks_data["tasks"].append(new_task)
            
            # Enregistrer les tâches
            save_tasks(tasks_data)
            
            return f"Tâche ajoutée : {task_desc}"
        else:
            return "Description de tâche non spécifiée"
    
    elif "liste des tâches" in texte or "affiche les tâches" in texte or "montre les tâches" in texte:
        # Charger les tâches
        tasks_data = load_tasks()
        
        if not tasks_data["tasks"]:
            return "Aucune tâche enregistrée"
        
        # Filtrer par statut si spécifié
        status_filter = None
        if "à faire" in texte:
            status_filter = "à faire"
        elif "terminées" in texte or "complétées" in texte:
            status_filter = "terminée"
        
        # Construire la liste des tâches
        tasks_list = []
        for task in tasks_data["tasks"]:
            if status_filter is None or task["status"] == status_filter:
                status_icon = "✓" if task["status"] == "terminée" else "□"
                tasks_list.append(f"{status_icon} {task['id']}. {task['description']}")
        
        if not tasks_list:
            return f"Aucune tâche avec le statut '{status_filter}'"
        
        return "Liste des tâches :\n" + "\n".join(tasks_list)
    
    elif "termine tâche" in texte or "marque tâche comme terminée" in texte or "complète tâche" in texte:
        # Extraire l'ID de la tâche
        match = re.search(r"tâche\s+(?:numéro|id|identifiant)?\s*[:\"]?(\d+)[\"]?", texte)
        if match:
            task_id = int(match.group(1))
            
            # Charger les tâches
            tasks_data = load_tasks()
            
            # Rechercher la tâche par ID
            for task in tasks_data["tasks"]:
                if task["id"] == task_id:
                    task["status"] = "terminée"
                    task["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Enregistrer les tâches
                    save_tasks(tasks_data)
                    
                    return f"Tâche {task_id} marquée comme terminée : {task['description']}"
            
            return f"Tâche {task_id} non trouvée"
        else:
            return "ID de tâche non spécifié"
    
    elif "supprime tâche" in texte or "efface tâche" in texte:
        # Extraire l'ID de la tâche
        match = re.search(r"tâche\s+(?:numéro|id|identifiant)?\s*[:\"]?(\d+)[\"]?", texte)
        if match:
            task_id = int(match.group(1))
            
            # Charger les tâches
            tasks_data = load_tasks()
            
            # Rechercher la tâche par ID
            for i, task in enumerate(tasks_data["tasks"]):
                if task["id"] == task_id:
                    # Supprimer la tâche
                    deleted_task = tasks_data["tasks"].pop(i)
                    
                    # Enregistrer les tâches
                    save_tasks(tasks_data)
                    
                    return f"Tâche {task_id} supprimée : {deleted_task['description']}"
            
            return f"Tâche {task_id} non trouvée"
        else:
            return "ID de tâche non spécifié"
    
    # ===== GESTION DE PROJET =====
    elif "crée structure de projet" in texte or "initialise projet" in texte:
        # Extraire le type de projet
        project_type = "python"  # Par défaut
        if "python" in texte:
            project_type = "python"
        elif "web" in texte or "html" in texte:
            project_type = "web"
        elif "node" in texte or "javascript" in texte or "js" in texte:
            project_type = "node"
        elif "django" in texte:
            project_type = "django"
        elif "flask" in texte:
            project_type = "flask"
        
        # Extraire le nom du projet
        match = re.search(r"projet\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        project_name = "nouveau_projet"
        if match:
            project_name = match.group(1).strip()
        
        # Créer la structure de dossiers selon le type de projet
        try:
            os.makedirs(project_name, exist_ok=True)
            
            if project_type == "python":
                os.makedirs(os.path.join(project_name, "src"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "docs"), exist_ok=True)
                
                # Créer des fichiers de base
                with open(os.path.join(project_name, "README.md"), 'w', encoding='utf-8') as f:
                    f.write(f"# {project_name}\n\nDescription du projet\n")
                
                with open(os.path.join(project_name, "requirements.txt"), 'w', encoding='utf-8') as f:
                    f.write("# Dépendances du projet\n")
                
                with open(os.path.join(project_name, "setup.py"), 'w', encoding='utf-8') as f:
                    f.write(f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
)
""")
                
                with open(os.path.join(project_name, "src", "__init__.py"), 'w', encoding='utf-8') as f:
                    f.write("# Package principal\n")
                
                with open(os.path.join(project_name, "src", "main.py"), 'w', encoding='utf-8') as f:
                    f.write("""def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
""")
                
                with open(os.path.join(project_name, "tests", "__init__.py"), 'w', encoding='utf-8') as f:
                    f.write("# Tests\n")
                
                with open(os.path.join(project_name, "tests", "test_main.py"), 'w', encoding='utf-8') as f:
                    f.write("""import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # TODO: Implement test
        pass

if __name__ == "__main__":
    unittest.main()
""")
                
                return f"Structure de projet Python créée : {project_name}"
                
            elif project_type == "web":
                os.makedirs(os.path.join(project_name, "css"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "js"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "images"), exist_ok=True)
                
                # Créer des fichiers de base
                with open(os.path.join(project_name, "index.html"), 'w', encoding='utf-8') as f:
                    f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <h1>{project_name}</h1>
    <p>Bienvenue sur mon site web.</p>
    
    <script src="js/main.js"></script>
</body>
</html>
""")
                
                with open(os.path.join(project_name, "css", "style.css"), 'w', encoding='utf-8') as f:
                    f.write("""/* Styles principaux */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}

h1 {
    color: #333;
}
""")
                
                with open(os.path.join(project_name, "js", "main.js"), 'w', encoding='utf-8') as f:
                    f.write("""// Script principal
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page chargée');
});
""")
                
                return f"Structure de projet Web créée : {project_name}"
                
            elif project_type == "node":
                os.makedirs(os.path.join(project_name, "src"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "public"), exist_ok=True)
                
                # Créer des fichiers de base
                with open(os.path.join(project_name, "package.json"), 'w', encoding='utf-8') as f:
                    f.write(f"""{{
  "name": "{project_name}",
  "version": "1.0.0",
  "description": "",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "keywords": [],
  "author": "",
  "license": "ISC"
}}
""")
                
                with open(os.path.join(project_name, "src", "index.js"), 'w', encoding='utf-8') as f:
                    f.write("""console.log('Hello, world!');
""")
                
                with open(os.path.join(project_name, "README.md"), 'w', encoding='utf-8') as f:
                    f.write(f"# {project_name}\n\nDescription du projet Node.js\n")
                
                return f"Structure de projet Node.js créée : {project_name}"
                
            elif project_type == "django":
                # Utiliser django-admin pour créer le projet
                try:
                    subprocess.run(["django-admin", "startproject", project_name])
                    return f"Projet Django créé : {project_name}"
                except:
                    return "Erreur lors de la création du projet Django. Django est-il installé ?"
                
            elif project_type == "flask":
                os.makedirs(os.path.join(project_name, "app"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "app", "templates"), exist_ok=True)
                os.makedirs(os.path.join(project_name, "app", "static"), exist_ok=True)
                
                # Créer des fichiers de base
                with open(os.path.join(project_name, "app", "__init__.py"), 'w', encoding='utf-8') as f:
                    f.write("""from flask import Flask

app = Flask(__name__)

from app import routes
""")
                
                with open(os.path.join(project_name, "app", "routes.py"), 'w', encoding='utf-8') as f:
                    f.write("""from app import app
from flask import render_template

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Accueil')
""")
                
                with open(os.path.join(project_name, "app", "templates", "index.html"), 'w', encoding='utf-8') as f:
                    f.write("""<!DOCTYPE html>
<html>
    <head>
        <title>{{ title }}</title>
    </head>
    <body>
        <h1>Bienvenue sur {{ title }}</h1>
    </body>
</html>
""")
                
                with open(os.path.join(project_name, "run.py"), 'w', encoding='utf-8') as f:
                    f.write("""from app import app

if __name__ == '__main__':
    app.run(debug=True)
""")
                
                return f"Structure de projet Flask créée : {project_name}"
        
        except Exception as e:
            return f"Erreur lors de la création de la structure de projet : {str(e)}"
    
    # ===== COMMANDES DE DOCUMENTATION =====
    elif "génère documentation" in texte or "crée documentation" in texte:
        if "sphinx" in texte:
            # Extraire le chemin du projet
            match = re.search(r"(?:projet|dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
            project_path = "."
            if match:
                project_path = match.group(1).strip()
            
            try:
                # Créer le dossier docs s'il n'existe pas
                os.makedirs(os.path.join(project_path, "docs"), exist_ok=True)
                
                # Initialiser Sphinx
                subprocess.run(["sphinx-quickstart", "--quiet", "--sep", 
                               "--project=" + os.path.basename(project_path),
                               "--author=Auteur", os.path.join(project_path, "docs")])
                
                return f"Documentation Sphinx initialisée dans {project_path}/docs"
            except:
                return "Erreur lors de l'initialisation de Sphinx. Sphinx est-il installé ?"
        else:
            # Par défaut, créer un fichier README.md
            try:
                with open("README.md", 'w', encoding='utf-8') as f:
                    f.write(f"""# Projet

## Description
Description du projet

## Installation
Instructions d'installation

## Utilisation
Instructions d'utilisation

## Licence
Licence du projet
""")
                return "Fichier README.md créé"
            except:
                return "Erreur lors de la création du fichier README.md"
    
    # ===== COMMANDES DE PLANIFICATION =====
    elif "planifie sprint" in texte or "crée sprint" in texte:
        # Extraire le nom du sprint
        match = re.search(r"sprint\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        sprint_name = f"Sprint {datetime.datetime.now().strftime('%Y-%m-%d')}"
        if match:
            sprint_name = match.group(1).strip()
        
        # Créer un fichier de planification de sprint
        try:
            with open(f"{sprint_name}.md", 'w', encoding='utf-8') as f:
                f.write(f"""# {sprint_name}

## Objectifs
- Objectif 1
- Objectif 2
- Objectif 3

## Tâches
- [ ] Tâche 1
- [ ] Tâche 2
- [ ] Tâche 3

## Rétrospective
À compléter à la fin du sprint
""")
            return f"Planification de sprint créée : {sprint_name}.md"
        except:
            return f"Erreur lors de la création de la planification de sprint"
    
    return None  # Commande non reconnue
