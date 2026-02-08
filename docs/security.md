# Sécurité - Whisp Assistant

## Vue d'ensemble

Ce document décrit les mesures de sécurité mises en place dans Whisp Assistant v2.0 pour protéger les utilisateurs contre les vulnérabilités courantes.

## Validation des Entrées

### Architecture de Validation

Toutes les entrées utilisateur sont validées avant traitement :

```python
from input_validation import InputValidator, ValidationError

validator = InputValidator()

try:
    command = validator.validate_command(user_input)
    # Traiter la commande
except ValidationError as e:
    return f"Commande non autorisée: {str(e)}"
```

### Patterns Dangereux Détectés

Le module de validation détecte et bloque :

- **Injection de commandes** : `;`, `&&`, `|`, `$()`, backticks
- **Commandes destructrices** : `rm -rf`, `del /s`
- **Traversée de répertoires** : `../`, accès à `/etc`, `/sys`, `/proc`
- **Caractères de contrôle** : Caractères non-imprimables

### Whitelist de Commandes

Seules les commandes autorisées peuvent être exécutées :

```python
ALLOWED_COMMANDS = {
    # Windows
    'notepad', 'calc', 'explorer', 'cmd', 'powershell',
    # Développement
    'code', 'pycharm', 'vim', 'nano',
    # Bureautique
    'winword', 'excel', 'powerpnt', 'outlook',
    # Navigation
    'chrome', 'firefox', 'msedge',
    # ...
}
```

## Stockage des Clés API

### Chiffrement PBKDF2

Les clés API sont chiffrées avec PBKDF2-HMAC-SHA256 (100,000 itérations) :

```python
from api_security import get_secure_api_key, set_secure_api_key

# Stocker une clé de manière sécurisée
set_secure_api_key("openai", "sk-...")

# Récupérer une clé
api_key = get_secure_api_key("openai")
```

### Emplacement de Stockage

Les clés chiffrées sont stockées dans :

- **Windows** : `C:\Users\{User}\.whisp\secure\api_keys.enc`
- **macOS/Linux** : `~/.whisp/secure/api_keys.enc`

### Permissions de Fichiers

Les fichiers de clés ont des permissions restrictives :

- **Unix** : `0600` (lecture/écriture propriétaire uniquement)
- **Windows** : ACL appropriées

### Migration Automatique

Les clés en clair sont automatiquement migrées vers le stockage sécurisé au démarrage :

```python
from api_security import migrate_api_keys
migrate_api_keys()  # Migre api_keys.json vers le stockage chiffré
```

## Opérations sur Fichiers

### Validation des Chemins

Tous les chemins de fichiers sont validés :

```python
from input_validation import InputValidator

validator = InputValidator()
safe_path = validator.validate_file_path(user_path)
```

### Répertoires Autorisés

Par défaut, seuls ces répertoires sont accessibles :

- `~/Documents`
- `~/Desktop`
- `~/Downloads`
- `~/Pictures`
- `~/Music`
- `~/Videos`
- `~/OneDrive`
- Dossiers temporaires (`/tmp`, `%TEMP%`)

### Protection Contre la Traversée

Les chemins avec `..` sont rejetés :

```python
# ❌ BLOQUÉ
validator.validate_file_path("../../../etc/passwd")

# ✅ AUTORISÉ
validator.validate_file_path("~/Documents/mon_fichier.txt")
```

## Exécution de Commandes

### subprocess.run() au lieu de os.system()

Tous les `os.system()` ont été remplacés par `subprocess.run()` :

```python
# ❌ ANCIEN (vulnérable)
os.system("notepad")

# ✅ NOUVEAU (sécurisé)
subprocess.run(["notepad"], shell=False, check=False, capture_output=True)
```

### Avantages de subprocess.run()

1. **Pas d'interprétation shell** : `shell=False` par défaut
2. **Arguments séparés** : Pas d'injection possible
3. **Capture de sortie** : Contrôle complet des I/O
4. **Codes de retour** : Gestion d'erreur robuste

## Requêtes SQL

### Requêtes Paramétrées

Les opérations de base de données utilisent des requêtes paramétrées :

```python
# ❌ VULNÉRABLE
cursor.execute(f"CREATE TABLE {table_name} ...")

# ✅ SÉCURISÉ
cursor.execute("CREATE TABLE IF NOT EXISTS (?)", (table_name,))
```

### Protection Contre l'Injection SQL

- Échappement automatique des paramètres
- Validation des noms de tables/colonnes
- Whitelist des opérations SQL autorisées

## Logging et Audit

### Logging Sécurisé

Les informations sensibles ne sont jamais loguées :

```python
# ❌ À éviter
logger.info(f"API Key: {api_key}")

# ✅ Correct
logger.info(f"API Key configurée: {api_key[:4]}...{api_key[-4:]}")
```

### Logs Structurés

Tous les événements de sécurité sont logués :

```python
logger.warning("Tentative de commande bloquée", extra={
    "command": user_input,
    "reason": "pattern_dangereux",
    "user": "username"
})
```

## Recommendations pour Utilisateurs

### 1. Variables d'Environnement

Privilégiez les variables d'environnement pour les clés API :

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-..."
export MISTRAL_API_KEY="..."

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
$env:MISTRAL_API_KEY="..."
```

### 2. Permissions de Fichiers

Vérifiez les permissions du dossier `.whisp` :

```bash
# Linux/macOS
chmod 700 ~/.whisp
chmod 600 ~/.whisp/secure/*
```

### 3. Mises à Jour

Gardez l'application à jour :

```bash
pip install --upgrade whisp-assistant
```

### 4. Audit Régulier

- Révisez les logs dans `~/.whisp/logs/`
- Vérifiez les commandes exécutées
- Surveillez les tentatives d'injection bloquées

## Menaces Atténuées

| Menace | Statut | Mitigation |
|--------|--------|------------|
| Injection de commandes | ✅ PROTÉGÉ | Validation + subprocess.run() |
| Injection SQL | ✅ PROTÉGÉ | Requêtes paramétrées |
| Traversée de répertoires | ✅ PROTÉGÉ | Validation des chemins |
| Clés API en clair | ✅ PROTÉGÉ | Chiffrement PBKDF2 |
| Commandes destructrices | ✅ PROTÉGÉ | Whitelist + patterns |
| Except clauses nues | 🔄 EN COURS | Remplacement progressif |

## Améliorations Futures

- [ ] Intégration de SELinux/AppArmor
- [ ] Signature de code
- [ ] Sandbox des commandes
- [ ] HSM pour les clés API
- [ ] Audit externe de sécurité

## Signalement de Vulnérabilités

Pour signaler une vulnérabilité de sécurité :

1. **Ne pas créer d'issue publique**
2. Envoyer un email à : security@whisp-assistant.com
3. Inclure :
   - Description de la vulnérabilité
   - Étapes pour reproduire
   - Impact potentiel
   - Suggestion de correction

Les vulnérabilités seront traitées dans les 48h.

## Ressources

- [OWASP Python Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)
- [Cryptography Documentation](https://cryptography.io/)
- [Bandit Security Linter](https://github.com/PyCQA/bandit)
