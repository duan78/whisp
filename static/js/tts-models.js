/**
 * Gestion des modèles TTS Coqui
 */

// Fonction pour charger les modèles Coqui disponibles
function loadCoquiModels() {
    fetch('/get_coqui_models')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCoquiModelsUI(data.models, data.current_model);
            } else {
                console.error('Erreur lors du chargement des modèles Coqui:', data.error);
                showNotification('Erreur lors du chargement des modèles Coqui: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la requête pour les modèles Coqui:', error);
            showNotification('Erreur lors de la requête pour les modèles Coqui', 'error');
        });
}

// Fonction pour mettre à jour l'interface utilisateur avec les modèles disponibles
function updateCoquiModelsUI(models, currentModel) {
    const container = document.getElementById('coqui-models-container');
    if (!container) return;
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Créer le titre
    const title = document.createElement('h4');
    title.textContent = 'Modèles Coqui TTS';
    title.className = 'coqui-models-title';
    container.appendChild(title);
    
    // Créer le groupe de boutons
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'coqui-models-buttons';
    
    // Créer les boutons pour chaque modèle
    models.forEach(model => {
        const button = document.createElement('button');
        button.className = 'model-button ' + (model.id === currentModel ? 'active' : '');
        button.textContent = model.description;
        button.setAttribute('data-model-id', model.id);
        button.setAttribute('aria-pressed', model.id === currentModel ? 'true' : 'false');
        button.onclick = function() {
            changeCoquiModel(model.id);
        };
        
        buttonGroup.appendChild(button);
    });
    
    container.appendChild(buttonGroup);
    
    // Afficher le conteneur uniquement si le moteur TTS actuel est Coqui
    const ttsEngine = document.getElementById('tts-engine').value;
    container.style.display = ttsEngine === 'coqui' ? 'block' : 'none';
}

// Fonction pour changer de modèle Coqui
function changeCoquiModel(modelId) {
    // Mettre à jour l'interface utilisateur immédiatement pour un feedback rapide
    document.querySelectorAll('#coqui-models-container .model-button').forEach(button => {
        if (button.getAttribute('data-model-id') === modelId) {
            button.classList.add('active');
            button.setAttribute('aria-pressed', 'true');
        } else {
            button.classList.remove('active');
            button.setAttribute('aria-pressed', 'false');
        }
    });
    
    // Afficher un indicateur de chargement
    showNotification('Chargement du modèle Coqui...', 'info');
    
    // Envoyer la requête au serveur
    fetch('/change_coqui_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Modèle Coqui changé pour: ${modelId}`);
            // Ajouter un log
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Modèle Coqui changé pour: ${modelId}`,
                type: 'info'
            });
            showNotification(`Modèle Coqui changé avec succès`, 'success');
        } else {
            console.error('Erreur lors du changement de modèle Coqui:', data.error);
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Erreur lors du changement de modèle Coqui: ${data.error}`,
                type: 'error'
            });
            showNotification(`Erreur: ${data.error}`, 'error');
            // Recharger les modèles pour rétablir l'état correct
            loadCoquiModels();
        }
    })
    .catch(error => {
        console.error('Erreur lors de la requête pour changer de modèle Coqui:', error);
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: `Erreur lors de la requête pour changer de modèle Coqui`,
            type: 'error'
        });
        showNotification('Erreur de communication avec le serveur', 'error');
        // Recharger les modèles pour rétablir l'état correct
        loadCoquiModels();
    });
}

// Fonction pour afficher/masquer les options de modèles Coqui selon le moteur TTS sélectionné
function toggleCoquiModelsVisibility(ttsEngine) {
    const container = document.getElementById('coqui-models-container');
    if (container) {
        container.style.display = ttsEngine === 'coqui' ? 'block' : 'none';
        
        // Si on passe à Coqui, charger les modèles disponibles
        if (ttsEngine === 'coqui') {
            loadCoquiModels();
        }
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier l'état initial
    const currentTTSEngine = document.getElementById('tts-engine')?.value;
    if (currentTTSEngine === 'coqui') {
        loadCoquiModels();
    }
    
    // Ajouter un écouteur d'événements pour les changements de moteur TTS
    if (document.getElementById('tts-engine')) {
        document.getElementById('tts-engine').addEventListener('change', function() {
            toggleCoquiModelsVisibility(this.value);
        });
    }
});

// Fonction pour mettre à jour l'interface lors de la réception de mises à jour SSE
function updateCoquiModelFromStatus(status) {
    if (status.tts_engine === 'coqui' && status.coqui_model) {
        // Mettre à jour l'interface utilisateur
        document.querySelectorAll('#coqui-models-container .model-button').forEach(button => {
            if (button.getAttribute('data-model-id') === status.coqui_model) {
                button.classList.add('active');
                button.setAttribute('aria-pressed', 'true');
            } else {
                button.classList.remove('active');
                button.setAttribute('aria-pressed', 'false');
            }
        });
    }
}
/**
 * Gestion des modèles TTS Coqui
 */

// Fonction pour charger les modèles Coqui disponibles
function loadCoquiModels() {
    fetch('/get_coqui_models')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCoquiModelsUI(data.models, data.current_model);
            } else {
                console.error('Erreur lors du chargement des modèles Coqui:', data.error);
                showNotification('Erreur lors du chargement des modèles Coqui: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la requête pour les modèles Coqui:', error);
            showNotification('Erreur lors de la requête pour les modèles Coqui', 'error');
        });
}

// Fonction pour mettre à jour l'interface utilisateur avec les modèles disponibles
function updateCoquiModelsUI(models, currentModel) {
    const container = document.getElementById('coqui-models-container');
    if (!container) return;
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Créer le titre
    const title = document.createElement('h4');
    title.textContent = 'Modèles Coqui TTS';
    title.className = 'coqui-models-title';
    container.appendChild(title);
    
    // Créer le groupe de boutons
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'coqui-models-buttons';
    
    // Créer les boutons pour chaque modèle
    models.forEach(model => {
        const button = document.createElement('button');
        button.className = 'model-button ' + (model.id === currentModel ? 'active' : '');
        button.textContent = model.description;
        button.setAttribute('data-model-id', model.id);
        button.setAttribute('aria-pressed', model.id === currentModel ? 'true' : 'false');
        button.onclick = function() {
            changeCoquiModel(model.id);
        };
        
        buttonGroup.appendChild(button);
    });
    
    container.appendChild(buttonGroup);
    
    // Afficher le conteneur uniquement si le moteur TTS actuel est Coqui
    const ttsEngine = document.getElementById('tts-engine').value;
    container.style.display = ttsEngine === 'coqui' ? 'block' : 'none';
}

// Fonction pour changer de modèle Coqui
function changeCoquiModel(modelId) {
    // Mettre à jour l'interface utilisateur immédiatement pour un feedback rapide
    document.querySelectorAll('#coqui-models-container .model-button').forEach(button => {
        if (button.getAttribute('data-model-id') === modelId) {
            button.classList.add('active');
            button.setAttribute('aria-pressed', 'true');
        } else {
            button.classList.remove('active');
            button.setAttribute('aria-pressed', 'false');
        }
    });
    
    // Afficher un indicateur de chargement
    showNotification('Chargement du modèle Coqui...', 'info');
    
    // Envoyer la requête au serveur
    fetch('/change_coqui_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Modèle Coqui changé pour: ${modelId}`);
            // Ajouter un log
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Modèle Coqui changé pour: ${modelId}`,
                type: 'info'
            });
            showNotification(`Modèle Coqui changé avec succès`, 'success');
        } else {
            console.error('Erreur lors du changement de modèle Coqui:', data.error);
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Erreur lors du changement de modèle Coqui: ${data.error}`,
                type: 'error'
            });
            showNotification(`Erreur: ${data.error}`, 'error');
            // Recharger les modèles pour rétablir l'état correct
            loadCoquiModels();
        }
    })
    .catch(error => {
        console.error('Erreur lors de la requête pour changer de modèle Coqui:', error);
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: `Erreur lors de la requête pour changer de modèle Coqui`,
            type: 'error'
        });
        showNotification('Erreur de communication avec le serveur', 'error');
        // Recharger les modèles pour rétablir l'état correct
        loadCoquiModels();
    });
}

// Fonction pour afficher/masquer les options de modèles Coqui selon le moteur TTS sélectionné
function toggleCoquiModelsVisibility(ttsEngine) {
    const container = document.getElementById('coqui-models-container');
    if (container) {
        container.style.display = ttsEngine === 'coqui' ? 'block' : 'none';
        
        // Si on passe à Coqui, charger les modèles disponibles
        if (ttsEngine === 'coqui') {
            loadCoquiModels();
        }
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier l'état initial
    const currentTTSEngine = document.getElementById('tts-engine')?.value;
    if (currentTTSEngine === 'coqui') {
        loadCoquiModels();
    }
    
    // Ajouter un écouteur d'événements pour les changements de moteur TTS
    if (document.getElementById('tts-engine')) {
        document.getElementById('tts-engine').addEventListener('change', function() {
            toggleCoquiModelsVisibility(this.value);
        });
    }
});

// Fonction pour mettre à jour l'interface lors de la réception de mises à jour SSE
function updateCoquiModelFromStatus(status) {
    if (status.tts_engine === 'coqui' && status.coqui_model) {
        // Mettre à jour l'interface utilisateur
        document.querySelectorAll('#coqui-models-container .model-button').forEach(button => {
            if (button.getAttribute('data-model-id') === status.coqui_model) {
                button.classList.add('active');
                button.setAttribute('aria-pressed', 'true');
            } else {
                button.classList.remove('active');
                button.setAttribute('aria-pressed', 'false');
            }
        });
    }
}
