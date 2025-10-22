/**
 * Gestion des paramètres de reconnaissance vocale
 */

// Fonction pour charger les paramètres STT
function loadSTTSettings() {
    const container = document.getElementById('stt-settings-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement des paramètres STT...</div>';
    
    fetch('/get_stt_settings')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySTTSettings(data.settings, data.default_settings);
            } else {
                showToast('Erreur lors du chargement des paramètres STT: ' + data.error, 'error');
                container.innerHTML = '<div class="config-error">Erreur lors du chargement des paramètres STT</div>';
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur de communication avec le serveur', 'error');
            container.innerHTML = '<div class="config-error">Erreur de communication avec le serveur</div>';
        });
}

// Fonction pour afficher les paramètres STT dans l'interface
function displaySTTSettings(settings, defaultSettings) {
    const container = document.getElementById('stt-settings-container');
    if (!container) return;
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Créer une structure de carte pour les paramètres (style WhispUI)
    const settingsTable = document.createElement('table');
    settingsTable.className = 'config-table';
    settingsTable.innerHTML = `
        <thead>
            <tr>
                <th>Paramètre</th>
                <th>Valeur</th>
                <th>Par défaut</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="stt-settings-tbody"></tbody>
    `;
    
    container.appendChild(settingsTable);
    const tbody = document.getElementById('stt-settings-tbody');
    
    // Descriptions des paramètres
    const descriptions = {
        'pause_threshold': 'Seuil de pause (secondes) - Durée de silence pour considérer la fin d\'une phrase',
        'energy_threshold': 'Seuil d\'énergie - Niveau sonore minimum pour détecter la parole',
        'non_speaking_duration': 'Durée de non-parole (secondes) - Durée de silence pour considérer la fin d\'une phrase',
        'phrase_timeout': 'Timeout de phrase (secondes) - Durée maximale d\'une phrase',
        'speechrecognition_silence_threshold': 'Seuil de silence SpeechRecognition - Niveau d\'énergie pour détecter le silence',
        'whisper_silence_threshold': 'Seuil de silence Whisper - Niveau d\'énergie pour détecter le silence',
        'whisper_silence_chunks': 'Chunks de silence Whisper - Nombre de chunks silencieux pour terminer l\'enregistrement',
        'vosk_silence_threshold': 'Seuil de silence Vosk - Niveau d\'énergie pour détecter le silence',
        'vosk_silence_chunks': 'Chunks de silence Vosk - Nombre de chunks silencieux pour terminer l\'enregistrement',
        'whisper_ct2_silence_threshold': 'Seuil de silence Whisper CT2 - Niveau d\'énergie pour détecter le silence',
        'whisper_ct2_silence_chunks': 'Chunks de silence Whisper CT2 - Nombre de chunks silencieux pour terminer l\'enregistrement'
    };
    
    // Groupes de paramètres
    const groups = [
        {
            title: 'Paramètres généraux',
            params: ['pause_threshold', 'energy_threshold', 'non_speaking_duration', 'phrase_timeout']
        },
        {
            title: 'Paramètres SpeechRecognition',
            params: ['speechrecognition_silence_threshold']
        },
        {
            title: 'Paramètres Whisper API',
            params: ['whisper_silence_threshold', 'whisper_silence_chunks']
        },
        {
            title: 'Paramètres Vosk',
            params: ['vosk_silence_threshold', 'vosk_silence_chunks']
        },
        {
            title: 'Paramètres Whisper CT2',
            params: ['whisper_ct2_silence_threshold', 'whisper_ct2_silence_chunks']
        }
    ];
    
    // Créer les rangées pour chaque groupe
    groups.forEach(group => {
        // Ajouter un en-tête de groupe
        const groupRow = document.createElement('tr');
        groupRow.className = 'group-header';
        groupRow.innerHTML = `<td colspan="4"><strong>${group.title}</strong></td>`;
        tbody.appendChild(groupRow);
        
        // Ajouter les paramètres du groupe
        group.params.forEach(param => {
            if (param in settings) {
                const row = document.createElement('tr');
                
                // Description du paramètre
                const descCell = document.createElement('td');
                descCell.innerHTML = `<span title="${descriptions[param] || param}">${param}</span>`;
                
                // Valeur actuelle (éditable)
                const valueCell = document.createElement('td');
                const input = document.createElement('input');
                input.type = 'number';
                input.id = `stt-${param}`;
                input.className = 'config-input';
                input.value = settings[param];
                input.step = typeof settings[param] === 'number' && Number.isInteger(settings[param]) ? '1' : '0.01';
                input.min = '0';
                
                // Attributs spécifiques selon le paramètre
                if (param.includes('threshold')) {
                    if (param === 'energy_threshold') {
                        input.min = '50';
                        input.max = '4000';
                    } else {
                        input.min = '0.01';
                        input.max = '1';
                    }
                } else if (param.includes('duration') || param.includes('timeout')) {
                    input.min = '0.1';
                    input.max = '10';
                } else if (param.includes('chunks')) {
                    input.min = '1';
                    input.max = '100';
                }
                
                valueCell.appendChild(input);
                
                // Valeur par défaut
                const defaultCell = document.createElement('td');
                defaultCell.textContent = defaultSettings && param in defaultSettings ? defaultSettings[param] : 'N/A';
                
                // Actions
                const actionsCell = document.createElement('td');
                
                // Bouton de sauvegarde
                const saveBtn = document.createElement('button');
                saveBtn.type = 'button';
                saveBtn.className = 'config-card-button primary';
                saveBtn.innerHTML = '<i class="fas fa-save"></i>';
                saveBtn.title = 'Sauvegarder';
                saveBtn.onclick = function() {
                    updateSingleSetting(param, input.value);
                };
                
                // Bouton de réinitialisation
                const resetBtn = document.createElement('button');
                resetBtn.type = 'button';
                resetBtn.className = 'config-card-button';
                resetBtn.innerHTML = '<i class="fas fa-undo"></i>';
                resetBtn.title = 'Réinitialiser';
                resetBtn.onclick = function() {
                    resetSTTSetting(param);
                };
                
                actionsCell.appendChild(saveBtn);
                actionsCell.appendChild(resetBtn);
                
                // Ajouter les cellules à la ligne
                row.appendChild(descCell);
                row.appendChild(valueCell);
                row.appendChild(defaultCell);
                row.appendChild(actionsCell);
                
                // Ajouter la ligne au tableau
                tbody.appendChild(row);
            }
        });
    });
    
    // Ajouter un bouton pour réinitialiser tous les paramètres
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'config-card-footer';
    
    const resetAllBtn = document.createElement('button');
    resetAllBtn.type = 'button';
    resetAllBtn.className = 'config-card-button danger';
    resetAllBtn.innerHTML = '<i class="fas fa-redo"></i> Réinitialiser tous les paramètres';
    resetAllBtn.onclick = resetAllSTTSettings;
    
    actionsDiv.appendChild(resetAllBtn);
    container.appendChild(actionsDiv);
}

// Fonction pour sauvegarder les paramètres STT
function saveSTTSettings() {
    const form = document.getElementById('stt-settings-form');
    if (!form) return;
    
    // Récupérer tous les champs du formulaire
    const formData = new FormData(form);
    const settings = {};
    
    // Convertir les valeurs en nombres
    for (const [key, value] of formData.entries()) {
        settings[key] = parseFloat(value);
    }
    
    // Sauvegarder chaque paramètre individuellement
    const savePromises = Object.entries(settings).map(([key, value]) => {
        return fetch('/update_stt_setting', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key, value })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error(`Erreur lors de la mise à jour du paramètre ${key}:`, data.error);
                return false;
            }
            return true;
        })
        .catch(error => {
            console.error(`Erreur lors de la mise à jour du paramètre ${key}:`, error);
            return false;
        });
    });
    
    // Attendre que toutes les sauvegardes soient terminées
    Promise.all(savePromises)
        .then(results => {
            const allSuccess = results.every(result => result);
            if (allSuccess) {
                showToast('Paramètres STT sauvegardés avec succès', 'success');
            } else {
                showToast('Certains paramètres n\'ont pas pu être sauvegardés', 'warning');
            }
        });
}

// Fonction pour mettre à jour un seul paramètre STT
function updateSingleSetting(param, value) {
    // Convertir la valeur au type approprié
    if (typeof value === 'string') {
        if (value.includes('.')) {
            value = parseFloat(value);
        } else {
            value = parseInt(value);
        }
    }
    
    // Vérifier que la valeur est valide
    if (isNaN(value)) {
        showToast(`Valeur invalide pour le paramètre "${param}"`, 'error');
        return;
    }
    
    // Envoyer la requête
    fetch('/update_stt_setting', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key: param, value: value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Paramètre "${param}" mis à jour avec succès`, 'success');
        } else {
            showToast(`Erreur lors de la mise à jour du paramètre: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur de communication avec le serveur', 'error');
    });
}

// Fonction pour réinitialiser un paramètre STT spécifique
function resetSTTSetting(param) {
    fetch('/reset_stt_settings', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour uniquement le champ spécifique
            const input = document.getElementById(`stt-${param}`);
            if (input && data.settings[param] !== undefined) {
                input.value = data.settings[param];
                showToast(`Paramètre "${param}" réinitialisé`, 'success');
            }
        } else {
            showToast('Erreur lors de la réinitialisation du paramètre', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur de communication avec le serveur', 'error');
    });
}

// Fonction pour réinitialiser tous les paramètres STT
function resetAllSTTSettings() {
    if (confirm('Êtes-vous sûr de vouloir réinitialiser tous les paramètres de reconnaissance vocale ?')) {
        fetch('/reset_stt_settings', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Tous les paramètres STT ont été réinitialisés', 'success');
                displaySTTSettings(data.settings);
            } else {
                showToast('Erreur lors de la réinitialisation des paramètres', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur de communication avec le serveur', 'error');
        });
    }
}

// Fonction pour réinitialiser les métriques STT
function resetSTTMetrics() {
    if (confirm('Êtes-vous sûr de vouloir réinitialiser les métriques de reconnaissance vocale ?')) {
        fetch('/reset_stt_metrics', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Les métriques STT ont été réinitialisées', 'success');
                // Recharger la page pour afficher les métriques mises à jour
                location.reload();
            } else {
                showToast('Erreur lors de la réinitialisation des métriques', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur de communication avec le serveur', 'error');
        });
    }
}

// Fonction utilitaire pour afficher un toast
function showToast(message, type = 'info') {
    // Vérifier si la fonction existe déjà dans la page
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }
    
    // Créer un élément toast si la fonction n'existe pas
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Ajouter le toast au document
    document.body.appendChild(toast);
    
    // Afficher le toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Masquer et supprimer le toast après 3 secondes
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Charger les paramètres STT au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur la page de configuration
    if (document.getElementById('stt-settings-container')) {
        loadSTTSettings();
    }
    
    // Vérifier si nous sommes dans l'onglet Speech
    if (document.querySelector('.config-tab[data-tab="speech"]')) {
        // Ajouter un écouteur d'événements pour le changement d'onglet
        document.querySelectorAll('.config-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                if (this.dataset.tab === 'speech' && document.getElementById('stt-settings-container')) {
                    // Rafraîchir les paramètres STT quand on active l'onglet
                    setTimeout(loadSTTSettings, 100);
                }
            });
        });
    }
    
    // Attacher l'événement au bouton de réinitialisation des métriques
    const resetMetricsBtn = document.getElementById('reset-stt-metrics-btn');
    if (resetMetricsBtn) {
        resetMetricsBtn.addEventListener('click', resetSTTMetrics);
    }
    
    // Supprimer le bouton "détail" des métriques STT s'il existe
    const detailsButtons = document.querySelectorAll('.metrics-details-btn');
    detailsButtons.forEach(btn => {
        btn.style.display = 'none';
    });
});
