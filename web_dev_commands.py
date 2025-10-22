"""
Module de commandes pour le développement web
"""

import subprocess
import os
import pyautogui
import re
import webbrowser
import json
import datetime
from text_processing import ecrire_texte_avec_accents

def executer_commande_web_dev(texte):
    """Exécute des commandes liées au développement web"""
    texte = texte.lower()
    
    # ===== COMMANDES SERVEUR DE DÉVELOPPEMENT =====
    if "lance serveur http" in texte or "démarre serveur http" in texte:
        port = "8000"  # Port par défaut
        
        # Extraire le port si spécifié
        match = re.search(r"port\s+(\d+)", texte)
        if match:
            port = match.group(1)
        
        try:
            # Utiliser le module http.server de Python
            subprocess.Popen(["python", "-m", "http.server", port])
            return f"Serveur HTTP démarré sur le port {port}"
        except:
            return f"Erreur lors du démarrage du serveur HTTP"
    
    elif "lance serveur flask" in texte or "démarre serveur flask" in texte:
        try:
            # Chercher le fichier app.py ou run.py
            if os.path.exists("app.py"):
                subprocess.Popen(["python", "app.py"])
                return "Serveur Flask démarré avec app.py"
            elif os.path.exists("run.py"):
                subprocess.Popen(["python", "run.py"])
                return "Serveur Flask démarré avec run.py"
            else:
                return "Fichier app.py ou run.py non trouvé"
        except:
            return "Erreur lors du démarrage du serveur Flask"
    
    elif "lance serveur django" in texte or "démarre serveur django" in texte:
        port = "8000"  # Port par défaut
        
        # Extraire le port si spécifié
        match = re.search(r"port\s+(\d+)", texte)
        if match:
            port = match.group(1)
        
        try:
            subprocess.Popen(["python", "manage.py", "runserver", f"0.0.0.0:{port}"])
            return f"Serveur Django démarré sur le port {port}"
        except:
            return "Erreur lors du démarrage du serveur Django"
    
    # ===== COMMANDES FRONTEND =====
    elif "crée composant react" in texte or "nouveau composant react" in texte:
        # Extraire le nom du composant
        match = re.search(r"composant\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            component_name = match.group(1).strip()
            # Capitaliser la première lettre pour suivre la convention React
            component_name = component_name[0].upper() + component_name[1:]
            
            try:
                # Créer le dossier components s'il n'existe pas
                os.makedirs("components", exist_ok=True)
                
                # Créer le fichier du composant
                with open(f"components/{component_name}.js", 'w', encoding='utf-8') as f:
                    f.write(f"""import React from 'react';

function {component_name}() {{
  return (
    <div className="{component_name.lower()}-container">
      <h2>{component_name}</h2>
    </div>
  );
}}

export default {component_name};
""")
                
                # Créer le fichier CSS associé
                with open(f"components/{component_name}.css", 'w', encoding='utf-8') as f:
                    f.write(f""".{component_name.lower()}-container {{
  padding: 20px;
  margin: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
}}
""")
                
                return f"Composant React '{component_name}' créé"
            except:
                return f"Erreur lors de la création du composant React"
        else:
            return "Nom de composant non spécifié"
    
    elif "crée page html" in texte or "nouvelle page html" in texte:
        # Extraire le nom de la page
        match = re.search(r"page\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            page_name = match.group(1).strip()
            file_name = f"{page_name.lower().replace(' ', '_')}.html"
            
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_name}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>{page_name}</h1>
        <nav>
            <ul>
                <li><a href="index.html">Accueil</a></li>
                <li><a href="#">À propos</a></li>
                <li><a href="#">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section>
            <h2>Section principale</h2>
            <p>Contenu de la page.</p>
        </section>
    </main>
    
    <footer>
        <p>&copy; {datetime.datetime.now().year} - Tous droits réservés</p>
    </footer>
    
    <script src="js/main.js"></script>
</body>
</html>
""")
                
                return f"Page HTML '{page_name}' créée : {file_name}"
            except:
                return f"Erreur lors de la création de la page HTML"
        else:
            return "Nom de page non spécifié"
    
    # ===== COMMANDES CSS =====
    elif "crée style css" in texte or "nouveau fichier css" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:style|fichier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            style_name = match.group(1).strip()
            file_name = f"{style_name.lower().replace(' ', '_')}.css"
            
            try:
                # Créer le dossier css s'il n'existe pas
                os.makedirs("css", exist_ok=True)
                
                with open(f"css/{file_name}", 'w', encoding='utf-8') as f:
                    f.write("""/* Réinitialisation des styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}

header {
    background-color: #35424a;
    color: white;
    padding: 20px;
    text-align: center;
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    margin-top: 10px;
}

nav ul li {
    margin: 0 15px;
}

nav ul li a {
    color: white;
    text-decoration: none;
}

main {
    max-width: 1200px;
    margin: 20px auto;
    padding: 0 20px;
}

section {
    background-color: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

h1, h2, h3 {
    margin-bottom: 15px;
}

p {
    margin-bottom: 10px;
}

footer {
    background-color: #35424a;
    color: white;
    text-align: center;
    padding: 20px;
    margin-top: 20px;
}

/* Media Queries pour la responsivité */
@media (max-width: 768px) {
    nav ul {
        flex-direction: column;
        align-items: center;
    }
    
    nav ul li {
        margin: 5px 0;
    }
}
""")
                
                return f"Fichier CSS '{style_name}' créé : css/{file_name}"
            except:
                return f"Erreur lors de la création du fichier CSS"
        else:
            return "Nom de fichier CSS non spécifié"
    
    # ===== COMMANDES JAVASCRIPT =====
    elif "crée script javascript" in texte or "nouveau fichier javascript" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:script|fichier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            script_name = match.group(1).strip()
            file_name = f"{script_name.lower().replace(' ', '_')}.js"
            
            try:
                # Créer le dossier js s'il n'existe pas
                os.makedirs("js", exist_ok=True)
                
                with open(f"js/{file_name}", 'w', encoding='utf-8') as f:
                    f.write("""// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('Script chargé');
    
    // Sélectionner des éléments
    const header = document.querySelector('header');
    const sections = document.querySelectorAll('section');
    
    // Exemple d'événement
    if (header) {
        header.addEventListener('click', function() {
            console.log('Header cliqué');
        });
    }
    
    // Exemple de fonction
    function toggleVisibility(element) {
        if (element.style.display === 'none') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
    
    // Exemple d'animation
    function fadeIn(element, duration = 1000) {
        element.style.opacity = 0;
        element.style.display = 'block';
        
        let start = null;
        function step(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            element.style.opacity = Math.min(progress / duration, 1);
            if (progress < duration) {
                window.requestAnimationFrame(step);
            }
        }
        window.requestAnimationFrame(step);
    }
    
    // Exemple d'utilisation de fetch pour les API
    function fetchData(url) {
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau');
                }
                return response.json();
            })
            .then(data => {
                console.log('Données reçues:', data);
            })
            .catch(error => {
                console.error('Erreur:', error);
            });
    }
});
""")
                
                return f"Fichier JavaScript '{script_name}' créé : js/{file_name}"
            except:
                return f"Erreur lors de la création du fichier JavaScript"
        else:
            return "Nom de fichier JavaScript non spécifié"
    
    # ===== COMMANDES API =====
    elif "crée api rest" in texte or "nouvelle api rest" in texte:
        # Extraire le nom de l'API
        match = re.search(r"api\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            api_name = match.group(1).strip()
            folder_name = f"{api_name.lower().replace(' ', '_')}_api"
            
            try:
                # Créer la structure de dossiers
                os.makedirs(folder_name, exist_ok=True)
                os.makedirs(os.path.join(folder_name, "routes"), exist_ok=True)
                os.makedirs(os.path.join(folder_name, "models"), exist_ok=True)
                os.makedirs(os.path.join(folder_name, "controllers"), exist_ok=True)
                
                # Créer le fichier principal
                with open(os.path.join(folder_name, "server.js"), 'w', encoding='utf-8') as f:
                    f.write("""const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Routes
const apiRoutes = require('./routes/api');
app.use('/api', apiRoutes);

// Route racine
app.get('/', (req, res) => {
    res.json({ message: 'Bienvenue sur l\\'API' });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`Serveur en cours d'exécution sur le port ${PORT}`);
});
""")
                
                # Créer le fichier de routes
                with open(os.path.join(folder_name, "routes", "api.js"), 'w', encoding='utf-8') as f:
                    f.write("""const express = require('express');
const router = express.Router();
const itemController = require('../controllers/itemController');

// Routes pour les items
router.get('/items', itemController.getAllItems);
router.get('/items/:id', itemController.getItemById);
router.post('/items', itemController.createItem);
router.put('/items/:id', itemController.updateItem);
router.delete('/items/:id', itemController.deleteItem);

module.exports = router;
""")
                
                # Créer le fichier de modèle
                with open(os.path.join(folder_name, "models", "Item.js"), 'w', encoding='utf-8') as f:
                    f.write("""// Exemple de modèle (à adapter selon votre base de données)
class Item {
    constructor(id, name, description) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.createdAt = new Date();
    }
    
    // Méthodes statiques pour simuler une base de données
    static items = [];
    
    static getAll() {
        return this.items;
    }
    
    static getById(id) {
        return this.items.find(item => item.id === id);
    }
    
    static create(name, description) {
        const id = this.items.length + 1;
        const newItem = new Item(id, name, description);
        this.items.push(newItem);
        return newItem;
    }
    
    static update(id, data) {
        const index = this.items.findIndex(item => item.id === id);
        if (index !== -1) {
            this.items[index] = { ...this.items[index], ...data };
            return this.items[index];
        }
        return null;
    }
    
    static delete(id) {
        const index = this.items.findIndex(item => item.id === id);
        if (index !== -1) {
            const deletedItem = this.items[index];
            this.items.splice(index, 1);
            return deletedItem;
        }
        return null;
    }
}

module.exports = Item;
""")
                
                # Créer le fichier de contrôleur
                with open(os.path.join(folder_name, "controllers", "itemController.js"), 'w', encoding='utf-8') as f:
                    f.write("""const Item = require('../models/Item');

// Contrôleur pour les items
exports.getAllItems = (req, res) => {
    try {
        const items = Item.getAll();
        res.status(200).json(items);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.getItemById = (req, res) => {
    try {
        const id = parseInt(req.params.id);
        const item = Item.getById(id);
        
        if (!item) {
            return res.status(404).json({ message: 'Item non trouvé' });
        }
        
        res.status(200).json(item);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.createItem = (req, res) => {
    try {
        const { name, description } = req.body;
        
        if (!name || !description) {
            return res.status(400).json({ message: 'Nom et description requis' });
        }
        
        const newItem = Item.create(name, description);
        res.status(201).json(newItem);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.updateItem = (req, res) => {
    try {
        const id = parseInt(req.params.id);
        const updatedItem = Item.update(id, req.body);
        
        if (!updatedItem) {
            return res.status(404).json({ message: 'Item non trouvé' });
        }
        
        res.status(200).json(updatedItem);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

exports.deleteItem = (req, res) => {
    try {
        const id = parseInt(req.params.id);
        const deletedItem = Item.delete(id);
        
        if (!deletedItem) {
            return res.status(404).json({ message: 'Item non trouvé' });
        }
        
        res.status(200).json({ message: 'Item supprimé avec succès' });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
""")
                
                # Créer le package.json
                with open(os.path.join(folder_name, "package.json"), 'w', encoding='utf-8') as f:
                    f.write(f"""{{
  "name": "{api_name.lower().replace(' ', '-')}-api",
  "version": "1.0.0",
  "description": "API REST pour {api_name}",
  "main": "server.js",
  "scripts": {{
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  }},
  "dependencies": {{
    "express": "^4.17.1",
    "body-parser": "^1.19.0",
    "cors": "^2.8.5"
  }},
  "devDependencies": {{
    "nodemon": "^2.0.7"
  }}
}}
""")
                
                return f"API REST '{api_name}' créée dans le dossier {folder_name}"
            except:
                return f"Erreur lors de la création de l'API REST"
        else:
            return "Nom d'API non spécifié"
    
    # ===== COMMANDES VALIDATION =====
    elif "valide html" in texte or "vérifie html" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:fichier|page)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            file_name = match.group(1).strip()
            
            # Ouvrir le validateur W3C
            webbrowser.open(f"https://validator.w3.org/#validate_by_upload")
            return f"Validateur HTML W3C ouvert. Veuillez téléverser le fichier {file_name}"
        else:
            # Ouvrir le validateur W3C
            webbrowser.open(f"https://validator.w3.org/")
            return "Validateur HTML W3C ouvert"
    
    elif "valide css" in texte or "vérifie css" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:fichier|style)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            file_name = match.group(1).strip()
            
            # Ouvrir le validateur W3C CSS
            webbrowser.open(f"https://jigsaw.w3.org/css-validator/#validate_by_upload")
            return f"Validateur CSS W3C ouvert. Veuillez téléverser le fichier {file_name}"
        else:
            # Ouvrir le validateur W3C CSS
            webbrowser.open(f"https://jigsaw.w3.org/css-validator/")
            return "Validateur CSS W3C ouvert"
    
    return None  # Commande non reconnue
