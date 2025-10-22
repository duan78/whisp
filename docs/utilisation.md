# 🎤 Guide d'Utilisation de Whisp Assistant

## 🚀 Démarrage Rapide

### Lancement de l'Assistant

```bash
python main.py
```

L'assistant démarrera et sera accessible sur : **http://localhost:5000**

---

## 🎙️ Commandes Vocales de Base

### Commandes Essentielles

| Commande | Description | Exemple |
|----------|------------|--------|
| `"Dis bonjour"` | Saluer l'assistant | `"Dis bonjour Whisp"` |
| `"aide"` | Afficher l'aide principale | `"Quelles sont tes commandes"` |
| `"arrête-toi"` | Arrêter proprement l'assistant | `"Ferme l'assistant"` |
| `"quel est ton nom"` | Demander son identité | `"Comment tu t'appelles"` |

### Contrôle Système

| Commande | Description | Exemple |
|----------|------------|--------|
| `"Ouvre [application]"` | Lancer une application | `"Ouvre Chrome"`, `"Ouvre Bloc-notes"` |
| `"Ferme [application]"` | Fermer application active | `"Ferme la fenêtre"` |
| `"Mets le volume à [1-100]"` | Régler volume audio | `"Mets le volume à 50"` |
| `"Redémarrer l'ordinateur"` | Redémarrage système | `"Reboot PC"` |

### Dictée et Texte

| Commande | Description | Exemple |
|----------|------------|--------|
| `"Commence la dictée"` | Démarrer mode dictée | `"Écris"`, `"Mode dictée"` |
| `"Arrête la dictée"` | Terminer mode dictée | `"Fin de dictée"`, `"Stop la dictée"` |
| `"Efface"` | Effacer dernier texte dicté | `"Supprime le texte"` |

---

## 🔊 Paramètres Vocaux

### Modifier la Voix

```bash
# Configuration rapide du moteur TTS
python -c "
from tts_module import set_voice_rate
set_voice_rate(150)  # Plus lent (50-200)
print('✅ Vitesse de voix modifiée')
"
```

### Changer de Moteur STT

```bash
# Basculer sur Whisper si GPU disponible
python -c "
import os
os.environ['STT_ENGINE'] = 'whisper'
print('✅ Moteur STT changé vers Whisper')
"
```

---

## 🌐 Interface Web

### Accès à l'Interface

- **URL** : http://localhost:5000
- **Dashboard** : Contrôle principal de l'assistant
- **Configuration** : Paramètres STT/TTS et API
- **Historique** : Voir les commandes récentes
- **Aliases** : Créer des raccourcis personnalisés

### Fonctionnalités Web

#### 🎙️ Panneau de Contrôle
- **Microphone** : Activer/désactiver la reconnaissance
- **Synthèse** : Tester les différents moteurs TTS
- **Volume** : Régler le volume de sortie
- **Langue** : Changer la langue de reconnaissance/synthèse

#### 📊 Statistiques en Temps Réel
- **Utilisation CPU/RAM** : Monitoring des ressources
- **Latence STT/TTS** : Temps de réponse des moteurs
- **Historique des Commandes** : Liste des 50 dernières interactions

#### 🔧 Configuration Avancée

##### Moteurs STT Disponibles
- **SpeechRecognition** : Reconnaissance via API Google
- **Whisper** : Reconnaissance offline (nécessite GPU)
- **NeMo** : Reconnaissance NVIDIA (optimisé GPU)

##### Moteurs TTS Disponibles
- **gTTS** : Synthèse en ligne (Google)
- **pyttsx3** : Synthèse offline (système)
- **Piper** : Synthèse offline rapide
- **CoquiTTS** : Synthèse neuronale avancée

---

## ⚡ Commandes d'Automatisation

### Contrôle Applications

```bash
# Ouvrir des applications spécifiques
"Ouvre Spotify"                # Lance Spotify
"Ouvre Word"                    # Lance Microsoft Word
"Ouvre le terminal"               # Ouvre cmd/PowerShell
"Ouvre la calculatrice"           # Lance calc.exe
```

### Raccourcis Personnalisés

#### Créer un Alias

```bash
# Dans l'interface web ou via commande
"Créer un raccourci: check-email"  # Commande pour vérifier emails
"Action: python -c 'import subprocess; subprocess.run([\"python\", \"-c\", \"import smtplib; smtplib.SMTP('localhost').sendmail(\\\"test@email.com\\\", \\\"Test subject\\\", \\\"Test body\\\")')'"  # Action correspondante
```

#### Utiliser les Raccourcis

- **Vérification simple** : `"check-email"` → Vérifie les emails
- **Automatisation complexe** : `"lance-ma-routine-matinale"` → Exécute plusieurs actions

---

## 🛠️ Outils de Développement

### Mode Développeur

```bash
# Activer les fonctionnalités développeur
python main.py --dev-mode
```

#### Commandes Développeur

| Commande | Description |
|----------|------------|
| `"test API"` | Teste la connexion aux APIs |
| `"debug on"` | Active les logs détaillés |
| `"mode verbose"` | Affiche toutes les informations système |

### Intégration avec des Outils Externes

#### VS Code
```bash
# Envoyer du code à VS Code
"Envoie ce code à VS Code"
# Action: ouvre VS Code avec le code actuel comme base
```

#### Git Intégré
```bash
# Commandes Git natives
"Git status"                 # État du repository
"Git add ."                  # Ajouter tous les fichiers
"Git commit 'message'"          # Créer un commit
"Git push"                    # Pousser vers le repository
"Git pull"                    # Récupérer les changements
```

---

## 🔧 Personnalisation Avancée

### Scripts Personnalisés

#### Créer un Script Personnalisé

```python
# Créer un script custom_commands.py
# Dans custom_commands.py :
from base_command_module import BaseCommandModule

class MonModulePersonnalisé(BaseCommandModule):
    def executer_commande(self, commande):
        if "ma commande spéciale" in commande.lower():
            # Logique personnalisée ici
            return "Action personnalisée exécutée"

# Ajouter au système de commandes
```

#### Intégration des Modules

```python
# Importer un module personnalisé dans main.py
from custom_commands import MonModulePersonnalisé

# Enregistrement automatique
command_processor.ajouter_module('personnalisé', MonModulePersonnalisé)
```

---

## 📝 Historique des Commandes

### Consulter l'Historique

#### Interface Web
- Naviguez vers **Historique** dans le menu latéral
- Les commandes sont classées par date et heure
- Possibilité de filtrer par type (STT, TTS, système)

#### Recherche dans l'Historique

```bash
# Rechercher une commande spécifique
python -c "
from database_manager import DatabaseManager
db = DatabaseManager()
resultats = db.rechercher_historique('recherche')
for resultat in resultats:
    print(f'{resultat[\"timestamp\"]} - {resultat[\"commande\"]}')
"
```

---

## 🌍 Multilinguisme

### Changer de Langue

#### Configuration Rapide

```bash
# Via variable d'environnement
export LANGUAGE=en-US
python main.py
```

#### Via Interface Web

1. Allez dans **Configuration** > **Langue**
2. Sélectionnez la langue désirée
3. Cliquez sur **Appliquer**

### Langues Disponibles

- **Français (fr-FR)** : Support natif optimal
- **Anglais (en-US)** : Reconnaissance et synthèse complètes
- **Espagnol (es-ES)** : Reconnaissance de base
- **Allemand (de-DE)** : Reconnaissance de base
- **Italien (it-IT)** : Reconnaissance de base

---

## 🔐 Sécurité et Configuration

### Variables d'Environnement

#### Configuration Complète

```bash
# Afficher toutes les variables
python -c "
import os
print('Variables d'environnement actuelles :')
for key, value in os.environ.items():
    if 'API' in key.upper() or 'KEY' in key.upper():
        print(f'{key}=***MASQUÉ***')
    else:
        print(f'{key}={value}')
"
```

### Configuration des API

```bash
# Tester la configuration des clés API
python -c "
import json
from api_security import verifier_cles_api

try:
    with open('api_keys.json', 'r') as f:
        config = json.load(f)
    if verifier_cles_api(config):
        print('✅ Configuration API valide')
    else:
        print('❌ Configuration API invalide')
except FileNotFoundError:
    print('❌ Fichier api_keys.json non trouvé')
except json.JSONDecodeError:
    print('❌ Fichier api_keys.json invalide')
"
```

---

## 🎯 Scénarios d'Utilisation

### Scénario 1 : Assistant Personnel

**Objectif** : Utiliser Whisp comme assistant personnel quotidien

**Configuration requise** : Microphone et haut-parleurs

**Commandes utiles** :
```bash
# Routine du matin
"Dis bonjour Whisp, quelle heure est-il ?"
"Quel temps fait-il ?"
"Rappelle-moi d'aller au travail dans 10 minutes"

# Gestion des rappels
"Crée un rappel pour 15h00 : préparer la réunion"
"Quels sont mes rappels aujourd'hui ?"

# Informations personnelles
"Quel temps fait-il demain ?"
"Ajoute ceci à mon calendrier"
```

### Scénario 2 : Développeur Productif

**Objectif** : Automatisation des tâches de développement

**Configuration requise** : VS Code, Git, navigateurs

**Commandes utiles** :
```bash
# Gestion de projet
"Ouvre le projet du client"
"Compile le projet en mode debug"
"Teste les unités du module X"
"Vérifie la couverture de code"

# Intégration continue
"Lance les tests automatisés"
"Envoie le rapport de test par email"
"Mets à jour la documentation"
"Crée un nouveau ticket JIRA"
```

### Scénario 3 : Accessibilité

**Objectif** : Utiliser Whisp comme outil d'accessibilité

**Configuration requise** : Voice synths et lecteur d'écran

**Commandes utiles** :
```bash
# Lecture d'écran
"Lis cet écran"
"Décris la fenêtre active"
"Quel est le titre de cette fenêtre ?"

# Navigation vocale
"Va au menu suivant"
"Ouvre le menu principal"
"Retour à la page précédente"
"Ferme cette application"
```

---

## 🚨 Résolution de Problèmes

### Dépannage Courant

#### Problèmes Audio

**Symptôme** : Pas de réponse vocale
**Causes possibles** :
- Microphone désactivé ou muet
- Volume au minimum ou coupé
- Moteur STT/TTS mal configuré

**Solutions** :
```bash
# Tester le microphone
python -c "import speech_recognition_module; speech_recognition_module.tester_microphone()"

# Tester la synthèse vocale
python -c "import tts_module; tts_module.test_all_engines()"

# Vérifier la configuration audio
python -c "
import os
print('FFmpeg disponible :', os.system('ffmpeg -version') == 0)
print('Audio config :', 'AUDIO_ENABLED' in os.environ)
"
```

#### Problèmes de Performance

**Symptômes** : Réponses lentes, utilisation CPU élevée
**Solutions** :
```bash
# Activer le support GPU si disponible
export CUDA_VISIBLE_DEVICES=0
python main.py

# Utiliser des modèles plus légers
export WHISPER_MODEL=tiny
export STT_ENGINE=whisper

# Optimiser les threads
export COMMAND_THREADS=2
```

#### Problèmes d'Interface Web

**Symptôme** : Interface web inaccessible
**Causes possibles** :
- Port déjà utilisé
- Firewall bloquant l'accès
- Service pas démarré

**Solutions** :
```bash
# Changer le port
export WEB_PORT=5001
python main.py

# Redémarrer le service
python -c "
import subprocess
subprocess.run(['taskkill', '/f', '/im', 'python.exe'], shell=True)
import time
time.sleep(2)
subprocess.Popen(['python', 'main.py'])
"
```

---

## 📊 Monitoring et Statistiques

### Surveiller les Performances

#### Utilisation CPU/Mémoire

```bash
# Script de monitoring
python -c "
import psutil
import time
while True:
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    print(f'CPU: {cpu_percent}%, RAM: {memory.percent}% utilisée')
    time.sleep(5)
"
```

#### Journalisation Complete

```bash
# Activer le logging détaillé
export LOG_LEVEL=DEBUG
python main.py > whisp.log 2>&1

# Analyser les logs après utilisation
tail -f whisp.log | grep ERROR
tail -f whisp.log | grep WARNING
```

---

## 🔮 Conseils d'Utilisation Avancée

### Optimisations

#### Améliorer la Vitesse de Réponse

1. **Utiliser pyttsx3 pour les réponses courtes**
2. **Mettre en cache les réponses fréquentes**
3. **Réduire la qualité audio si nécessaire**
4. **Optimiser les paramètres GPU**

#### Personnalisation Maximale

1. **Créer des aliases pour les commandes complexes**
2. **Utiliser les scripts personnalisés**
3. **Configurer les raccourcis clavier-souris**
4. **Exploiter les intégrations avec outils externes**

---

## 📞 Formation et Ressources

### Documentation Complète

- **Guide principal** : Ce document
- **Référence API** : Documentation complète des modules
- **Exemples de code** : Dans les modules Python respectifs
- **Tutoriels vidéo** : À venir sur la chaîne YouTube
- **Wiki communautaire** : https://github.com/duan78/whisp/wiki

### Communauté et Support

- **Issues GitHub** : https://github.com/duan78/whisp/issues
- **Discussions** : https://github.com/duan78/whisp/discussions
- **Discord** : https://discord.gg/whisp-assistant
- **Email support** : support@whisp-assistant.com

### Contribution au Projet

- **Code source** : Disponible sur GitHub
- **Rapports de bugs** : Via les issues GitHub
- **Améliorations** : Pull requests bienvenues
- **Documentation** : Contributions au wiki bienvenues

---

*Ce guide couvre l'essentiel des fonctionnalités de Whisp Assistant. Pour plus d'informations, consultez la [documentation complète](../README.md) et les [guides spécifiques](../configuration.md).*