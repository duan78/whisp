// Variables globales
let isRunning = true;
let eventSource = null;
let currentSTTEngine = 'speechrecognition';
let currentTTSEngine = 'pyttsx3';
let lastLogTimestamp = null;
let isFirstLoad = true;
let animationsEnabled = true;
let darkMode = false;
let sttMetrics = {
    speechrecognition: {
        requests: 0,
        success: 0,
        errors: 0,
        latencies: [],
        avg_latency: 0,
        min_latency: 0,
        max_latency: 0,
        last_latency: 0,
        audio_durations: [],
        avg_audio_duration: 0,
        last_audio_duration: 0,
        last_request_time: null,
        word_count: 0,
        char_count: 0,
        words_per_minute: 0
    },
    whisper: {
        requests: 0,
        success: 0,
        errors: 0,
        latencies: [],
        avg_latency: 0,
        min_latency: 0,
        max_latency: 0,
        last_latency: 0,
        audio_durations: [],
        avg_audio_duration: 0,
        last_audio_duration: 0,
        last_request_time: null,
        word_count: 0,
        char_count: 0,
        words_per_minute: 0,
        cost: 0.0
    },
    vosk: {
        requests: 0,
        success: 0,
        errors: 0,
        latencies: [],
        avg_latency: 0,
        min_latency: 0,
        max_latency: 0,
        last_latency: 0,
        audio_durations: [],
        avg_audio_duration: 0,
        last_audio_duration: 0,
        last_request_time: null,
        word_count: 0,
        char_count: 0,
        words_per_minute: 0
    },
    whisper_ct2: {
        requests: 0,
        success: 0,
        errors: 0,
        latencies: [],
        avg_latency: 0,
        min_latency: 0,
        max_latency: 0,
        last_latency: 0,
        audio_durations: [],
        avg_audio_duration: 0,
        last_audio_duration: 0,
        last_request_time: null,
        word_count: 0,
        char_count: 0,
        words_per_minute: 0
    }
};

// Variables pour les clés API
let apiKeys = {
    openai: "",
    mistral: ""
};

// Éléments DOM
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const toggleButton = document.getElementById('toggle-button');
const lastCommand = document.getElementById('last-command');
const lastResponse = document.getElementById('last-response');
const logsContainer = document.getElementById('logs-container');
const helpButton = document.getElementById('help-button');
const helpModal = document.getElementById('help-modal');
const closeModal = document.querySelector('#help-modal .close');
const apiSettingsButton = document.getElementById('api-settings-button');
const apiSettingsModal = document.getElementById('api-settings-modal');
const closeApiSettings = document.getElementById('close-api-settings');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    // Afficher un indicateur de chargement
    showLoadingIndicator();
    
    // Vérifier les préférences utilisateur
    checkUserPreferences();
    
    // Charger l'état initial
    fetchStatus()
        .then(() => {
            // Charger les clés API
            return fetchApiKeys();
        })
        .then(() => {
            // Configurer les événements SSE
            setupEventSource();
            
            // Configurer les gestionnaires d'événements
            setupEventHandlers();
            
            // Configurer les onglets
            setupTabs();
            
            // Configurer les variations de commandes
            setupCommandVariations();
            
            // Configurer les gestionnaires pour les clés API
            setupApiKeyHandlers();
            
            // Ajouter des valeurs aux barres de comparaison
            setupComparisonBars();
            
            // Masquer l'indicateur de chargement
            hideLoadingIndicator();
            
            // Afficher une notification de bienvenue avec animation
            setTimeout(() => {
                showNotification('Bienvenue sur Whisp Assistant Vocal', 'info');
            }, 500);
        })
        .catch(error => {
            console.error('Erreur lors de l\'initialisation:', error);
            hideLoadingIndicator();
            showNotification('Erreur lors du chargement de l\'application', 'error');
        });
});

// Vérifier les préférences utilisateur
function checkUserPreferences() {
    // Vérifier le mode sombre
    if (localStorage.getItem('darkMode') === 'true') {
        darkMode = true;
        document.body.classList.add('dark-mode');
    }
    
    // Vérifier si les animations sont désactivées
    if (localStorage.getItem('animationsDisabled') === 'true') {
        animationsEnabled = false;
        document.body.classList.add('reduced-motion');
    }
}

// Configurer les barres de comparaison
function setupComparisonBars() {
    const comparisonBars = document.querySelectorAll('.comparison-bar');
    comparisonBars.forEach(bar => {
        // Ajouter l'attribut data-value pour l'affichage au survol
        const width = bar.style.width || '0%';
        bar.setAttribute('data-value', width);
    });
}

// Fonctions d'indicateur de chargement
function showLoadingIndicator() {
    // Créer un élément de chargement s'il n'existe pas déjà
    if (!document.getElementById('loading-indicator')) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Chargement de Whisp Assistant...</p>
        `;
        document.body.appendChild(loadingIndicator);
        
        // Ajouter les styles nécessaires
        const style = document.createElement('style');
        style.textContent = `
            .loading-indicator {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.9);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                font-family: 'Inter', sans-serif;
            }
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 5px solid rgba(67, 97, 238, 0.2);
                border-radius: 50%;
                border-top-color: #4361ee;
                animation: spin 1s ease-in-out infinite;
                margin-bottom: 20px;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.opacity = '0';
        loadingIndicator.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            loadingIndicator.remove();
        }, 500);
    }
}

// Fonction de notification
function showNotification(message, type = 'info') {
    // Créer un élément de notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Ajouter une icône en fonction du type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas fa-${icon}"></i>
        </div>
        <span>${message}</span>
        <button class="close-notification" aria-label="Fermer">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Ajouter les styles nécessaires si ce n'est pas déjà fait
    if (!document.getElementById('notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 16px;
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 1000;
                max-width: 350px;
                animation: slideIn 0.3s ease, fadeOut 0.5s ease 4.5s forwards;
                font-family: 'Inter', sans-serif;
                border: 1px solid rgba(0, 0, 0, 0.05);
                backdrop-filter: blur(10px);
            }
            .notification.info { border-left: 4px solid #3498db; }
            .notification.success { border-left: 4px solid #2ecc71; }
            .notification.error { border-left: 4px solid #e74c3c; }
            .notification.warning { border-left: 4px solid #f39c12; }
            
            .notification-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background-color: rgba(52, 152, 219, 0.1);
            }
            .notification.info .notification-icon { background-color: rgba(52, 152, 219, 0.1); }
            .notification.success .notification-icon { background-color: rgba(46, 204, 113, 0.1); }
            .notification.error .notification-icon { background-color: rgba(231, 76, 60, 0.1); }
            .notification.warning .notification-icon { background-color: rgba(243, 156, 18, 0.1); }
            
            .notification i.fa-info-circle { color: #3498db; }
            .notification i.fa-check-circle { color: #2ecc71; }
            .notification i.fa-exclamation-circle { color: #e74c3c; }
            .notification i.fa-exclamation-triangle { color: #f39c12; }
            
            .notification span {
                flex: 1;
                font-size: 14px;
                font-weight: 500;
            }
            
            .close-notification {
                background: none;
                border: none;
                cursor: pointer;
                color: #6c757d;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                transition: background-color 0.2s;
            }
            
            .close-notification:hover {
                background-color: #f8f9fa;
                color: #212529;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; visibility: hidden; }
            }
            
            .dark-mode .notification {
                background-color: #2d3748;
                color: #e2e8f0;
                border-color: rgba(255, 255, 255, 0.1);
            }
            
            .dark-mode .close-notification:hover {
                background-color: #4a5568;
                color: #e2e8f0;
            }
            
            .reduced-motion .notification {
                animation: none;
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Ajouter la notification au document
    document.body.appendChild(notification);
    
    // Configurer le bouton de fermeture
    const closeButton = notification.querySelector('.close-notification');
    closeButton.addEventListener('click', () => {
        notification.classList.add('closing');
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
            }
        }, 300);
    });
    
    // Supprimer la notification après 5 secondes
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.classList.add('closing');
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            notification.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// Fonctions
function fetchStatus() {
    return new Promise((resolve, reject) => {
        fetch('/status')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau lors de la récupération du statut');
                }
                return response.json();
            })
            .then(data => {
                updateUI(data);
                resolve(data);
            })
            .catch(error => {
                console.error('Erreur lors de la récupération du statut:', error);
                addLogEntry({
                    timestamp: new Date().toLocaleTimeString(),
                    message: `Erreur de connexion au serveur: ${error.message}`,
                    type: 'error'
                });
                reject(error);
            });
    });
}

function updateUI(data) {
    isRunning = data.running;
    
    // Mettre à jour l'indicateur de statut
    if (isRunning) {
        statusIndicator.className = 'status-indicator active';
        statusText.textContent = 'Actif';
    } else {
        statusIndicator.className = 'status-indicator inactive';
        statusText.textContent = 'Inactif';
    }
    
    // Mettre à jour les dernières interactions
    if (data.last_command) {
        lastCommand.textContent = data.last_command;
    }
    
    if (data.last_response) {
        lastResponse.textContent = data.last_response;
    }
    
    // Mettre à jour les logs
    if (data.logs && data.logs.length > 0) {
        // Vider le conteneur de logs si c'est le premier chargement
        if (logsContainer.children.length === 0) {
            updateLogs(data.logs);
        }
    }
    
    // Mettre à jour le sélecteur de moteur STT
    if (data.stt_engine) {
        currentSTTEngine = data.stt_engine;
        document.getElementById('stt-engine').value = data.stt_engine;
    }
    
    // Mettre à jour le sélecteur de moteur TTS
    if (data.tts_engine) {
        currentTTSEngine = data.tts_engine;
        document.getElementById('tts-engine').value = data.tts_engine;
    }
    
    // Mettre à jour les métriques STT
    if (data.stt_metrics) {
        sttMetrics = data.stt_metrics;
        updateSTTMetricsUI();
    }
}

function fetchApiKeys() {
    return new Promise((resolve, reject) => {
        fetch('/get_api_keys')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erreur réseau lors de la récupération des clés API');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Mettre à jour les champs de saisie
                    if (data.openai) {
                        document.getElementById('openai-api-key').value = data.openai;
                        document.getElementById('openai-key-status').innerHTML = '<span class="status-ok">Clé configurée</span>';
                        apiKeys.openai = "configured";
                    }
                    
                    if (data.mistral) {
                        document.getElementById('mistral-api-key').value = data.mistral;
                        document.getElementById('mistral-key-status').innerHTML = '<span class="status-ok">Clé configurée</span>';
                        apiKeys.mistral = "configured";
                    }
                    
                    resolve(data);
                } else {
                    reject(new Error(data.error || 'Erreur inconnue'));
                }
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des clés API:', error);
                reject(error);
            });
    });
}

function setupApiKeyHandlers() {
    // Gestionnaire pour le bouton de configuration des clés API
    apiSettingsButton.addEventListener('click', function() {
        apiSettingsModal.style.display = 'block';
    });
    
    // Gestionnaire pour fermer le modal
    closeApiSettings.addEventListener('click', function() {
        apiSettingsModal.style.display = 'none';
    });
    
    // Fermer le modal en cliquant en dehors
    window.addEventListener('click', function(e) {
        if (e.target === apiSettingsModal) {
            apiSettingsModal.style.display = 'none';
        }
    });
    
    // Gestionnaire pour le bouton de sauvegarde des clés API
    document.getElementById('save-api-keys').addEventListener('click', saveApiKeys);
    
    // Gestionnaires pour les boutons de visibilité
    document.getElementById('toggle-openai-visibility').addEventListener('click', function() {
        togglePasswordVisibility('openai-api-key', 'toggle-openai-visibility');
    });
    
    document.getElementById('toggle-mistral-visibility').addEventListener('click', function() {
        togglePasswordVisibility('mistral-api-key', 'toggle-mistral-visibility');
    });
}

function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

function saveApiKeys() {
    const openaiKey = document.getElementById('openai-api-key').value.trim();
    const mistralKey = document.getElementById('mistral-api-key').value.trim();
    
    // Sauvegarder la clé OpenAI si elle a été modifiée
    if (openaiKey && openaiKey !== '•••••••••••••••••••••••') {
        saveApiKey('openai', openaiKey);
    }
    
    // Sauvegarder la clé Mistral si elle a été modifiée
    if (mistralKey && mistralKey !== '•••••••••••••••••••••••') {
        saveApiKey('mistral', mistralKey);
    }
}

function saveApiKey(type, key) {
    fetch('/set_api_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ type: type, key: key })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mettre à jour le statut
            document.getElementById(`${type}-key-status`).innerHTML = '<span class="status-ok">Clé enregistrée avec succès</span>';
            
            // Masquer la clé après quelques secondes
            setTimeout(() => {
                document.getElementById(`${type}-api-key`).value = '•••••••••••••••••••••••';
            }, 2000);
            
            // Ajouter un log
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Clé API ${type === 'openai' ? 'OpenAI' : 'Mistral'} configurée`,
                type: 'info'
            });
            
            // Si c'est la clé OpenAI et que le moteur actuel est Whisper, proposer de redémarrer
            if (type === 'openai' && currentSTTEngine === 'whisper') {
                addLogEntry({
                    timestamp: new Date().toLocaleTimeString(),
                    message: 'Redémarrage de la reconnaissance vocale avec la nouvelle clé API',
                    type: 'info'
                });
                
                // Redémarrer le moteur Whisper
                changeSTTEngine('whisper');
            }
        } else {
            document.getElementById(`${type}-key-status`).innerHTML = `<span class="status-error">Erreur: ${data.error}</span>`;
        }
    })
    .catch(error => {
        console.error(`Erreur lors de la sauvegarde de la clé API ${type}:`, error);
        document.getElementById(`${type}-key-status`).innerHTML = '<span class="status-error">Erreur de connexion</span>';
    });
}

function updateSTTMetricsUI() {
    // Mettre à jour les métriques pour SpeechRecognition
    const srMetrics = sttMetrics.speechrecognition;
    document.getElementById('sr-requests').textContent = srMetrics.requests;
    document.getElementById('sr-success').textContent = srMetrics.success;
    document.getElementById('sr-errors').textContent = srMetrics.errors;
    document.getElementById('sr-success-rate').textContent = 
        srMetrics.requests > 0 ? `${Math.round((srMetrics.success / srMetrics.requests) * 100)}%` : '0%';
    document.getElementById('sr-avg-latency').textContent = `${Math.round(srMetrics.avg_latency)} ms`;
    document.getElementById('sr-min-latency').textContent = `${Math.round(srMetrics.min_latency)} ms`;
    document.getElementById('sr-max-latency').textContent = `${Math.round(srMetrics.max_latency)} ms`;
    document.getElementById('sr-last-latency').textContent = `${Math.round(srMetrics.last_latency)} ms`;
    document.getElementById('sr-avg-audio-duration').textContent = `${srMetrics.avg_audio_duration.toFixed(2)} s`;
    document.getElementById('sr-last-audio-duration').textContent = `${srMetrics.last_audio_duration.toFixed(2)} s`;
    document.getElementById('sr-words-per-minute').textContent = Math.round(srMetrics.words_per_minute);
    document.getElementById('sr-last-request-time').textContent = srMetrics.last_request_time || '-';
    
    
    // Mettre à jour les métriques pour Whisper
    if (sttMetrics.whisper) {
        const whisperMetrics = sttMetrics.whisper;
        document.getElementById('whisper-requests').textContent = whisperMetrics.requests;
        document.getElementById('whisper-success').textContent = whisperMetrics.success;
        document.getElementById('whisper-errors').textContent = whisperMetrics.errors;
        document.getElementById('whisper-success-rate').textContent = 
            whisperMetrics.requests > 0 ? `${Math.round((whisperMetrics.success / whisperMetrics.requests) * 100)}%` : '0%';
        document.getElementById('whisper-avg-latency').textContent = `${Math.round(whisperMetrics.avg_latency)} ms`;
        document.getElementById('whisper-min-latency').textContent = `${Math.round(whisperMetrics.min_latency)} ms`;
        document.getElementById('whisper-max-latency').textContent = `${Math.round(whisperMetrics.max_latency)} ms`;
        document.getElementById('whisper-last-latency').textContent = `${Math.round(whisperMetrics.last_latency)} ms`;
        document.getElementById('whisper-avg-audio-duration').textContent = `${whisperMetrics.avg_audio_duration.toFixed(2)} s`;
        document.getElementById('whisper-last-audio-duration').textContent = `${whisperMetrics.last_audio_duration.toFixed(2)} s`;
        document.getElementById('whisper-words-per-minute').textContent = Math.round(whisperMetrics.words_per_minute);
        document.getElementById('whisper-cost').textContent = `$${whisperMetrics.cost.toFixed(4)}`;
        document.getElementById('whisper-last-request-time').textContent = whisperMetrics.last_request_time || '-';
    }
    
    // Mettre à jour les métriques pour Vosk
    if (sttMetrics.vosk) {
        const voskMetrics = sttMetrics.vosk;
        document.getElementById('vosk-requests').textContent = voskMetrics.requests;
        document.getElementById('vosk-success').textContent = voskMetrics.success;
        document.getElementById('vosk-errors').textContent = voskMetrics.errors;
        document.getElementById('vosk-success-rate').textContent = 
            voskMetrics.requests > 0 ? `${Math.round((voskMetrics.success / voskMetrics.requests) * 100)}%` : '0%';
        document.getElementById('vosk-avg-latency').textContent = `${Math.round(voskMetrics.avg_latency)} ms`;
        document.getElementById('vosk-min-latency').textContent = `${Math.round(voskMetrics.min_latency)} ms`;
        document.getElementById('vosk-max-latency').textContent = `${Math.round(voskMetrics.max_latency)} ms`;
        document.getElementById('vosk-last-latency').textContent = `${Math.round(voskMetrics.last_latency)} ms`;
        document.getElementById('vosk-avg-audio-duration').textContent = `${voskMetrics.avg_audio_duration.toFixed(2)} s`;
        document.getElementById('vosk-last-audio-duration').textContent = `${voskMetrics.last_audio_duration.toFixed(2)} s`;
        document.getElementById('vosk-words-per-minute').textContent = Math.round(voskMetrics.words_per_minute);
        document.getElementById('vosk-last-request-time').textContent = voskMetrics.last_request_time || '-';
    }
    
    // Mettre à jour les métriques pour Whisper CT2
    if (sttMetrics.whisper_ct2) {
        const whisperCt2Metrics = sttMetrics.whisper_ct2;
        
        // Vérifier que les éléments DOM existent avant de les mettre à jour
        if (document.getElementById('whisper-ct2-requests')) {
            document.getElementById('whisper-ct2-requests').textContent = whisperCt2Metrics.requests;
            document.getElementById('whisper-ct2-success').textContent = whisperCt2Metrics.success;
            document.getElementById('whisper-ct2-errors').textContent = whisperCt2Metrics.errors;
            document.getElementById('whisper-ct2-success-rate').textContent = 
                whisperCt2Metrics.requests > 0 ? `${Math.round((whisperCt2Metrics.success / whisperCt2Metrics.requests) * 100)}%` : '0%';
            document.getElementById('whisper-ct2-avg-latency').textContent = `${Math.round(whisperCt2Metrics.avg_latency)} ms`;
            document.getElementById('whisper-ct2-min-latency').textContent = 
                whisperCt2Metrics.min_latency !== Infinity ? `${Math.round(whisperCt2Metrics.min_latency)} ms` : '0 ms';
            document.getElementById('whisper-ct2-max-latency').textContent = `${Math.round(whisperCt2Metrics.max_latency)} ms`;
            document.getElementById('whisper-ct2-last-latency').textContent = `${Math.round(whisperCt2Metrics.last_latency)} ms`;
            document.getElementById('whisper-ct2-avg-audio-duration').textContent = `${whisperCt2Metrics.avg_audio_duration.toFixed(2)} s`;
            document.getElementById('whisper-ct2-last-audio-duration').textContent = `${whisperCt2Metrics.last_audio_duration.toFixed(2)} s`;
            document.getElementById('whisper-ct2-words-per-minute').textContent = Math.round(whisperCt2Metrics.words_per_minute);
            document.getElementById('whisper-ct2-last-request-time').textContent = whisperCt2Metrics.last_request_time || '-';
        }
    }
    
    
    // Mettre à jour les métriques pour Vosk
    if (sttMetrics.vosk) {
        const voskMetrics = sttMetrics.vosk;
        document.getElementById('vosk-requests').textContent = voskMetrics.requests;
        document.getElementById('vosk-success').textContent = voskMetrics.success;
        document.getElementById('vosk-errors').textContent = voskMetrics.errors;
        document.getElementById('vosk-success-rate').textContent = 
            voskMetrics.requests > 0 ? `${Math.round((voskMetrics.success / voskMetrics.requests) * 100)}%` : '0%';
        document.getElementById('vosk-avg-latency').textContent = `${Math.round(voskMetrics.avg_latency)} ms`;
        document.getElementById('vosk-min-latency').textContent = `${Math.round(voskMetrics.min_latency)} ms`;
        document.getElementById('vosk-max-latency').textContent = `${Math.round(voskMetrics.max_latency)} ms`;
        document.getElementById('vosk-last-latency').textContent = `${Math.round(voskMetrics.last_latency)} ms`;
        document.getElementById('vosk-avg-audio-duration').textContent = `${voskMetrics.avg_audio_duration.toFixed(2)} s`;
        document.getElementById('vosk-last-audio-duration').textContent = `${voskMetrics.last_audio_duration.toFixed(2)} s`;
        document.getElementById('vosk-words-per-minute').textContent = Math.round(voskMetrics.words_per_minute);
        document.getElementById('vosk-last-request-time').textContent = voskMetrics.last_request_time || '-';
    }
    
    // Mettre à jour les barres de comparaison
    updateComparisonBars();
}

function updateComparisonBars() {
    const srMetrics = sttMetrics.speechrecognition;
    const whisperMetrics = sttMetrics.whisper;
    const voskMetrics = sttMetrics.vosk;
    const whisperCt2Metrics = sttMetrics.whisper_ct2 || { avg_latency: 0, requests: 0, success: 0, words_per_minute: 0 };
    
    // Latence (plus petite est meilleure)
    let srLatencyWidth = 0;
    let whisperLatencyWidth = 0;
    let voskLatencyWidth = 0;
    let sherpaLatencyWidth = 0;
    let whisperCt2LatencyWidth = 0;
    
    // Calculer les valeurs pour la comparaison de latence
    if (srMetrics.avg_latency > 0 || whisperMetrics.avg_latency > 0 || voskMetrics.avg_latency > 0 || 
        whisperCt2Metrics.avg_latency > 0) {
        // Trouver la latence maximale pour normaliser
        const maxLatency = Math.max(
            srMetrics.avg_latency > 0 ? srMetrics.avg_latency : 0,
            whisperMetrics.avg_latency > 0 ? whisperMetrics.avg_latency : 0,
            voskMetrics.avg_latency > 0 ? voskMetrics.avg_latency : 0,
            whisperCt2Metrics.avg_latency > 0 ? whisperCt2Metrics.avg_latency : 0
        );
        
        // Inverser les pourcentages car une latence plus faible est meilleure
        if (srMetrics.avg_latency > 0) {
            srLatencyWidth = 100 - ((srMetrics.avg_latency / maxLatency) * 100);
        }
        
        if (whisperMetrics.avg_latency > 0) {
            whisperLatencyWidth = 100 - ((whisperMetrics.avg_latency / maxLatency) * 100);
        }
        
        if (voskMetrics.avg_latency > 0) {
            voskLatencyWidth = 100 - ((voskMetrics.avg_latency / maxLatency) * 100);
        }
        
        
        if (whisperCt2Metrics.avg_latency > 0) {
            whisperCt2LatencyWidth = 100 - ((whisperCt2Metrics.avg_latency / maxLatency) * 100);
        }
    }
    
    const srLatencyBar = document.getElementById('sr-latency-bar');
    const whisperLatencyBar = document.getElementById('whisper-latency-bar');
    const voskLatencyBar = document.getElementById('vosk-latency-bar');
    const whisperCt2LatencyBar = document.getElementById('whisper-ct2-latency-bar');
    
    srLatencyBar.style.width = `${srLatencyWidth}%`;
    whisperLatencyBar.style.width = `${whisperLatencyWidth}%`;
    voskLatencyBar.style.width = `${voskLatencyWidth}%`;
    whisperCt2LatencyBar.style.width = `${whisperCt2LatencyWidth}%`;
    
    // Mettre à jour les attributs data-value pour l'affichage au survol
    srLatencyBar.setAttribute('data-value', `${Math.round(srLatencyWidth)}%`);
    whisperLatencyBar.setAttribute('data-value', `${Math.round(whisperLatencyWidth)}%`);
    voskLatencyBar.setAttribute('data-value', `${Math.round(voskLatencyWidth)}%`);
    whisperCt2LatencyBar.setAttribute('data-value', `${Math.round(whisperCt2LatencyWidth)}%`);
    
    // Taux de succès
    const srSuccessRate = srMetrics.requests > 0 ? (srMetrics.success / srMetrics.requests) * 100 : 0;
    const whisperSuccessRate = whisperMetrics.requests > 0 ? (whisperMetrics.success / whisperMetrics.requests) * 100 : 0;
    const voskSuccessRate = voskMetrics.requests > 0 ? (voskMetrics.success / voskMetrics.requests) * 100 : 0;
    const whisperCt2SuccessRate = whisperCt2Metrics.requests > 0 ? (whisperCt2Metrics.success / whisperCt2Metrics.requests) * 100 : 0;
    
    const srSuccessBar = document.getElementById('sr-success-bar');
    const whisperSuccessBar = document.getElementById('whisper-success-bar');
    const voskSuccessBar = document.getElementById('vosk-success-bar');
    const whisperCt2SuccessBar = document.getElementById('whisper-ct2-success-bar');
    
    srSuccessBar.style.width = `${srSuccessRate}%`;
    whisperSuccessBar.style.width = `${whisperSuccessRate}%`;
    voskSuccessBar.style.width = `${voskSuccessRate}%`;
    whisperCt2SuccessBar.style.width = `${whisperCt2SuccessRate}%`;
    
    // Mettre à jour les attributs data-value pour l'affichage au survol
    srSuccessBar.setAttribute('data-value', `${Math.round(srSuccessRate)}%`);
    whisperSuccessBar.setAttribute('data-value', `${Math.round(whisperSuccessRate)}%`);
    voskSuccessBar.setAttribute('data-value', `${Math.round(voskSuccessRate)}%`);
    whisperCt2SuccessBar.setAttribute('data-value', `${Math.round(whisperCt2SuccessRate)}%`);
    
    // Mots par minute
    let srWpmWidth = 0;
    let whisperWpmWidth = 0;
    let voskWpmWidth = 0;
    let sherpaWpmWidth = 0;
    let whisperCt2WpmWidth = 0;
    
    // Calculer les valeurs pour la comparaison de WPM
    const totalWpm = srMetrics.words_per_minute + whisperMetrics.words_per_minute + 
                     voskMetrics.words_per_minute + whisperCt2Metrics.words_per_minute;
    
    if (totalWpm > 0) {
        srWpmWidth = (srMetrics.words_per_minute / totalWpm) * 100;
        whisperWpmWidth = (whisperMetrics.words_per_minute / totalWpm) * 100;
        voskWpmWidth = (voskMetrics.words_per_minute / totalWpm) * 100;
        whisperCt2WpmWidth = (whisperCt2Metrics.words_per_minute / totalWpm) * 100;
    }
    
    const srWpmBar = document.getElementById('sr-wpm-bar');
    const whisperWpmBar = document.getElementById('whisper-wpm-bar');
    const voskWpmBar = document.getElementById('vosk-wpm-bar');
    const whisperCt2WpmBar = document.getElementById('whisper-ct2-wpm-bar');
    
    srWpmBar.style.width = `${srWpmWidth}%`;
    whisperWpmBar.style.width = `${whisperWpmWidth}%`;
    voskWpmBar.style.width = `${voskWpmWidth}%`;
    whisperCt2WpmBar.style.width = `${whisperCt2WpmWidth}%`;
    
    // Mettre à jour les attributs data-value pour l'affichage au survol
    srWpmBar.setAttribute('data-value', `${Math.round(srWpmWidth)}%`);
    whisperWpmBar.setAttribute('data-value', `${Math.round(whisperWpmWidth)}%`);
    voskWpmBar.setAttribute('data-value', `${Math.round(voskWpmWidth)}%`);
    whisperCt2WpmBar.setAttribute('data-value', `${Math.round(whisperCt2WpmWidth)}%`);
    
    // Ajouter une animation subtile aux barres
    if (animationsEnabled) {
        const allBars = document.querySelectorAll('.comparison-bar');
        allBars.forEach(bar => {
            bar.classList.remove('animated');
            void bar.offsetWidth; // Force reflow
            bar.classList.add('animated');
        });
    }
}

function updateLogs(logs) {
    // Ajouter chaque log au conteneur
    logs.forEach(log => {
        addLogEntry(log);
    });
    
    // Faire défiler vers le bas
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function addLogEntry(log) {
    // Vérifier si c'est un doublon (même timestamp et message)
    if (lastLogTimestamp === log.timestamp && 
        logsContainer.lastChild && 
        logsContainer.lastChild.querySelector('.log-message').textContent === log.message) {
        return;
    }
    
    lastLogTimestamp = log.timestamp;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${log.type}`;
    
    const timestamp = document.createElement('span');
    timestamp.className = 'log-timestamp';
    timestamp.textContent = log.timestamp;
    
    const message = document.createElement('span');
    message.className = 'log-message';
    message.textContent = log.message;
    
    // Ajouter une icône en fonction du type de log
    let iconClass = 'info-circle';
    if (log.type === 'command') iconClass = 'terminal';
    if (log.type === 'response') iconClass = 'comment-dots';
    if (log.type === 'error') iconClass = 'exclamation-circle';
    if (log.type === 'warning') iconClass = 'exclamation-triangle';
    
    const icon = document.createElement('i');
    icon.className = `fas fa-${iconClass} log-icon`;
    
    logEntry.appendChild(timestamp);
    logEntry.appendChild(icon);
    logEntry.appendChild(message);
    
    // Ajouter une animation d'entrée si les animations sont activées
    if (animationsEnabled) {
        logEntry.style.opacity = '0';
        logEntry.style.transform = 'translateY(10px)';
    }
    
    logsContainer.appendChild(logEntry);
    
    // Déclencher l'animation
    if (animationsEnabled) {
        setTimeout(() => {
            logEntry.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            logEntry.style.opacity = '1';
            logEntry.style.transform = 'translateY(0)';
        }, 10);
    } else {
        logEntry.style.opacity = '1';
    }
    
    // Limiter le nombre de logs affichés (garder les 100 derniers)
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
    
    // Faire défiler vers le bas
    logsContainer.scrollTop = logsContainer.scrollHeight;
    
    // Si c'est une erreur, afficher une notification
    if (log.type === 'error' && !isFirstLoad) {
        showNotification(log.message, 'error');
    }
    
    // Ajouter un effet de surbrillance pour les nouveaux logs
    if (!isFirstLoad) {
        logEntry.classList.add('new-log');
        setTimeout(() => {
            logEntry.classList.remove('new-log');
        }, 2000);
    }
}

function toggleAssistant() {
    // Ajouter une animation au bouton
    toggleButton.classList.add('animating');
    
    fetch('/toggle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erreur réseau lors du basculement de l\'assistant');
        }
        return response.json();
    })
    .then(data => {
        isRunning = data.running;
        
        // Mettre à jour l'interface
        if (isRunning) {
            statusIndicator.className = 'status-indicator active';
            statusText.textContent = 'Actif';
            showNotification('Assistant vocal activé', 'success');
        } else {
            statusIndicator.className = 'status-indicator inactive';
            statusText.textContent = 'Inactif';
            showNotification('Assistant vocal désactivé', 'info');
        }
    })
    .catch(error => {
        console.error('Erreur lors du basculement de l\'assistant:', error);
        showNotification('Erreur lors du basculement de l\'assistant', 'error');
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: `Erreur: ${error.message}`,
            type: 'error'
        });
    })
    .finally(() => {
        // Retirer l'animation du bouton
        setTimeout(() => {
            toggleButton.classList.remove('animating');
        }, 300);
    });
}

function setupEventSource() {
    // Fermer la connexion existante si elle existe
    if (eventSource) {
        eventSource.close();
    }
    
    // Créer une nouvelle connexion SSE
    eventSource = new EventSource('/events');
    
    // Gestionnaire d'événements pour les messages
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // Ignorer les pings
        if (data.ping) {
            return;
        }
        
        // Marquer la fin du chargement initial
        if (data.initial) {
            isFirstLoad = false;
            return;
        }
        
        // Ajouter le log à l'interface
        addLogEntry(data);
        
        // Mettre à jour les dernières interactions si nécessaire
        if (data.type === 'command') {
            const commandText = data.message.replace('Commande: ', '');
            lastCommand.textContent = commandText;
            
            // Ajouter une animation
            lastCommand.classList.add('highlight');
            setTimeout(() => {
                lastCommand.classList.remove('highlight');
            }, 1000);
        } else if (data.type === 'response') {
            const responseText = data.message.replace('Réponse: ', '');
            lastResponse.textContent = responseText;
            
            // Ajouter une animation
            lastResponse.classList.add('highlight');
            setTimeout(() => {
                lastResponse.classList.remove('highlight');
            }, 1000);
        }
        
        // Mettre à jour les métriques si on est sur l'onglet métriques
        if (document.querySelector('.tab-button[data-tab="metrics"]').classList.contains('active')) {
            fetchStatus();
        }
    };
    
    // Gestionnaire d'ouverture
    eventSource.onopen = function() {
        console.log('Connexion SSE établie');
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: 'Connexion au serveur établie',
            type: 'info'
        });
    };
    
    // Gestionnaire d'erreurs
    eventSource.onerror = function() {
        console.error('Erreur de connexion SSE. Tentative de reconnexion...');
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: 'Erreur de connexion au serveur. Tentative de reconnexion...',
            type: 'error'
        });
        
        eventSource.close();
        
        // Tenter de se reconnecter après un délai
        setTimeout(setupEventSource, 5000);
    };
}

function setupEventHandlers() {
    // Gestionnaire pour le bouton de basculement
    toggleButton.addEventListener('click', toggleAssistant);
    
    // Gestionnaire pour le sélecteur de moteur STT
    document.getElementById('stt-engine').addEventListener('change', function(e) {
        const newEngine = e.target.value;
        if (newEngine !== currentSTTEngine) {
            changeSTTEngine(newEngine);
        }
    });
    
    // Gestionnaire pour le sélecteur de moteur TTS
    document.getElementById('tts-engine').addEventListener('change', function(e) {
        const newEngine = e.target.value;
        if (newEngine !== currentTTSEngine) {
            changeTTSEngine(newEngine);
        }
    });
    
    // Gestionnaire pour le bouton de réinitialisation des métriques
    document.getElementById('reset-metrics-button').addEventListener('click', resetSTTMetrics);
    
    // Gestionnaires pour le modal d'aide
    helpButton.addEventListener('click', function(e) {
        e.preventDefault();
        helpModal.style.display = 'block';
    });
    
    closeModal.addEventListener('click', function() {
        helpModal.style.display = 'none';
    });
    
    window.addEventListener('click', function(e) {
        if (e.target === helpModal) {
            helpModal.style.display = 'none';
        }
    });
}

function resetSTTMetrics() {
    fetch('/reset_stt_metrics', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: 'Métriques STT réinitialisées',
                type: 'info'
            });
            
            // Mettre à jour l'interface
            fetchStatus();
        } else {
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Erreur lors de la réinitialisation des métriques: ${data.error}`,
                type: 'error'
            });
        }
    })
    .catch(error => {
        console.error('Erreur lors de la réinitialisation des métriques:', error);
    });
}

function changeSTTEngine(engine) {
    // Vérifier si la clé API OpenAI est configurée pour Whisper
    if (engine === 'whisper' && !apiKeys.openai) {
        addLogEntry({
            timestamp: new Date().toLocaleTimeString(),
            message: "Clé API OpenAI non configurée. Veuillez la configurer dans les paramètres.",
            type: 'error'
        });
        
        // Ouvrir automatiquement le modal de configuration
        apiSettingsModal.style.display = 'block';
        
        // Réinitialiser le sélecteur à la valeur actuelle
        document.getElementById('stt-engine').value = currentSTTEngine;
        return;
    }
    
    
    fetch('/change_stt_engine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ engine: engine })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentSTTEngine = engine;
            
            // Déterminer le nom à afficher
            let engineName;
            switch(engine) {
                case 'speechrecognition':
                    engineName = 'SpeechRecognition (par lot)';
                    break;
                case 'whisper':
                    engineName = 'OpenAI Whisper API (continu)';
                    break;
                case 'vosk':
                    engineName = 'Vosk (continu, hors ligne)';
                    break;
                default:
                    engineName = engine;
            }
            
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Moteur STT changé pour: ${engineName}`,
                type: 'info'
            });
        } else {
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Erreur lors du changement de moteur STT: ${data.error}`,
                type: 'error'
            });
            // Réinitialiser le sélecteur à la valeur actuelle
            document.getElementById('stt-engine').value = currentSTTEngine;
        }
    })
    .catch(error => {
        console.error('Erreur lors du changement de moteur STT:', error);
        // Réinitialiser le sélecteur à la valeur actuelle
        document.getElementById('stt-engine').value = currentSTTEngine;
    });
}

function setupTabs() {
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Désactiver tous les onglets
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activer l'onglet cliqué
            button.classList.add('active');
            button.setAttribute('aria-selected', 'true');
            const tabId = button.getAttribute('data-tab');
            const tabContent = document.getElementById(tabId);
            tabContent.classList.add('active');
            
            // Sauvegarder l'onglet actif dans le localStorage
            localStorage.setItem('activeTab', tabId);
            
            // Mettre à jour les métriques si on est sur l'onglet métriques
            if (tabId === 'metrics') {
                updateSTTMetricsUI();
                updateComparisonBars();
            }
        });
    });
    
    // Restaurer l'onglet actif depuis le localStorage
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        const tabButton = document.querySelector(`.tab-button[data-tab="${activeTab}"]`);
        if (tabButton) {
            tabButton.click();
        }
    }
}

function setupCommandVariations() {
    const commandElements = document.querySelectorAll('.command');
    
    commandElements.forEach(command => {
        // Créer l'élément pour afficher les variations
        const variationsElement = document.createElement('div');
        variationsElement.className = 'command-variations';
        
        // Récupérer les variations depuis l'attribut data
        const variations = command.getAttribute('data-variations');
        if (variations) {
            const variationsList = variations.split(',');
            
            // Créer la liste des variations
            const ul = document.createElement('ul');
            variationsList.forEach(variation => {
                const li = document.createElement('li');
                li.textContent = variation.trim();
                ul.appendChild(li);
            });
            
            variationsElement.appendChild(ul);
            command.parentNode.appendChild(variationsElement);
            
            // Ajouter les événements pour afficher/masquer les variations
            command.addEventListener('mouseenter', () => {
                // Positionner l'élément des variations
                const rect = command.getBoundingClientRect();
                variationsElement.style.top = `${command.offsetHeight}px`;
                variationsElement.style.left = '0';
                
                // Vérifier si l'élément dépasse de l'écran à droite
                const variationsRect = variationsElement.getBoundingClientRect();
                if (rect.left + variationsRect.width > window.innerWidth) {
                    variationsElement.style.left = 'auto';
                    variationsElement.style.right = '0';
                }
                
                variationsElement.style.display = 'block';
            });
            
            command.addEventListener('mouseleave', () => {
                setTimeout(() => {
                    if (!variationsElement.matches(':hover')) {
                        variationsElement.style.display = 'none';
                    }
                }, 100);
            });
            
            variationsElement.addEventListener('mouseleave', () => {
                variationsElement.style.display = 'none';
            });
        }
    });
}
function changeTTSEngine(engine) {
    fetch('/change_tts_engine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ engine: engine })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentTTSEngine = engine;
            
            // Déterminer le nom à afficher
            let engineName;
            switch(engine) {
                case 'pyttsx3':
                    engineName = 'Windows TTS (natif)';
                    break;
                case 'gtts':
                    engineName = 'Google TTS (en ligne)';
                    break;
                case 'tacotron':
                    engineName = 'Tacotron 2 (haute qualité)';
                    break;
                default:
                    engineName = engine;
            }
            
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Moteur TTS changé pour: ${engineName}`,
                type: 'info'
            });
        } else {
            addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: `Erreur lors du changement de moteur TTS: ${data.error}`,
                type: 'error'
            });
            // Réinitialiser le sélecteur à la valeur actuelle
            document.getElementById('tts-engine').value = currentTTSEngine;
        }
    })
    .catch(error => {
        console.error('Erreur lors du changement de moteur TTS:', error);
        // Réinitialiser le sélecteur à la valeur actuelle
        document.getElementById('tts-engine').value = currentTTSEngine;
    });
}
// Ajouter des gestionnaires pour les nouveaux éléments
class BugAnalyzer {
    constructor() {
        this.bugs = [];
        this.categories = {
            'accessibility': [],
            'aria': [],
            'logic': [],
            'performance': [],
            'security': []
        };
    }

    analyze() {
        // Utiliser les validateurs existants
        const accessibilityChecker = new AccessibilityChecker();
        const ariaValidator = new AriaValidator();
        
        // Récupérer les résultats des validateurs
        const accessibilityResults = accessibilityChecker.runAllChecks();
        const ariaResults = ariaValidator.validateAll();
        
        // Catégoriser les bugs
        this.categorizeIssues(accessibilityResults, 'accessibility');
        this.categorizeIssues(ariaResults, 'aria');
        
        // Ajouter des vérifications spécifiques
        this.checkForCommonBugs();
        
        return {
            totalBugs: this.bugs.length,
            categories: this.categories,
            details: this.bugs
        };
    }

    categorizeIssues(results, category) {
        if (results.issues && results.issues.length > 0) {
            results.issues.forEach(issue => {
                this.bugs.push({
                    type: 'issue',
                    category: category,
                    message: issue.message,
                    element: issue.element,
                    reference: issue.wcagReference || issue.ariaReference
                });
                this.categories[category].push(issue);
            });
        }
        
        if (results.warnings && results.warnings.length > 0) {
            results.warnings.forEach(warning => {
                this.bugs.push({
                    type: 'warning',
                    category: category,
                    message: warning.message,
                    element: warning.element,
                    reference: warning.wcagReference || warning.ariaReference
                });
                this.categories[category].push(warning);
            });
        }
    }

    checkForCommonBugs() {
        // Vérification des erreurs JavaScript
        try {
            // Vérifier les variables non définies
            if (typeof undefinedVariable !== 'undefined') {
                this.bugs.push({
                    type: 'error',
                    category: 'logic',
                    message: 'Variable non définie détectée',
                    element: null,
                    reference: 'JS-001'
                });
            }
        } catch (e) {
            // Ignorer les erreurs intentionnelles
        }

        // Vérifier les erreurs de chargement
        const failedResources = window.performance.getEntriesByType('resource')
            .filter(res => res.initiatorType !== 'beacon' && res.duration === 0);
        
        if (failedResources.length > 0) {
            this.bugs.push({
                type: 'error',
                category: 'performance',
                message: `${failedResources.length} ressources n'ont pas pu être chargées`,
                element: null,
                reference: 'PERF-001'
            });
        }
    }
}

function setupAdditionalHandlers() {
    // Ajouter le gestionnaire pour la vue bugs
    const bugsTab = document.querySelector('.tab-button[data-tab="bugs"]');
    if (bugsTab) {
        bugsTab.addEventListener('click', () => {
            const analyzer = new BugAnalyzer();
            const results = analyzer.analyze();
            
            // Afficher les résultats
            displayBugReport(results);
        });
    }
    // Gestionnaire pour le bouton de mode sombre
    const darkModeButton = document.getElementById('toggle-dark-mode');
    if (darkModeButton) {
        darkModeButton.addEventListener('click', toggleDarkMode);
    }
    
    // Gestionnaire pour le bouton d'animations
    const animationsButton = document.getElementById('toggle-animations');
    if (animationsButton) {
        animationsButton.addEventListener('click', toggleAnimations);
    }
    
    // Gestionnaires pour les boutons de filtre de logs
    const filterButtons = document.querySelectorAll('.filter-button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Désactiver tous les boutons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Activer le bouton cliqué
            this.classList.add('active');
            
            // Filtrer les logs
            const filter = this.getAttribute('data-filter');
            filterLogs(filter);
        });
    });
    
    // Gestionnaire pour le bouton d'effacement des logs
    const clearLogsButton = document.querySelector('.clear-logs-button');
    if (clearLogsButton) {
        clearLogsButton.addEventListener('click', clearLogs);
    }
}

// Fonction pour basculer le mode sombre
function toggleDarkMode() {
    darkMode = !darkMode;
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('darkMode', darkMode);
    
    // Changer l'icône du bouton
    const icon = document.querySelector('#toggle-dark-mode i');
    if (icon) {
        icon.className = darkMode ? 'fas fa-sun' : 'fas fa-moon';
    }
    
    // Afficher une notification
    showNotification(darkMode ? 'Mode sombre activé' : 'Mode clair activé', 'info');
}

// Fonction pour basculer les animations
function toggleAnimations() {
    animationsEnabled = !animationsEnabled;
    document.body.classList.toggle('reduced-motion', !animationsEnabled);
    localStorage.setItem('animationsDisabled', !animationsEnabled);
    
    // Changer l'icône du bouton
    const icon = document.querySelector('#toggle-animations i');
    if (icon) {
        icon.className = animationsEnabled ? 'fas fa-film' : 'fas fa-film-slash';
    }
    
    // Afficher une notification
    showNotification(animationsEnabled ? 'Animations activées' : 'Animations réduites', 'info');
}

// Fonction pour filtrer les logs
function filterLogs(filter) {
    const logs = document.querySelectorAll('.log-entry');
    
    logs.forEach(log => {
        if (filter === 'all') {
            log.style.display = 'block';
        } else {
            log.style.display = log.classList.contains(filter) ? 'block' : 'none';
        }
    });
    
    // Afficher l'état vide si aucun log n'est visible
    const visibleLogs = Array.from(logs).filter(log => log.style.display !== 'none');
    const emptyState = document.querySelector('.logs-empty-state');
    
    if (emptyState) {
        emptyState.style.display = visibleLogs.length === 0 ? 'flex' : 'none';
    }
}

// Fonction pour effacer les logs
function displayBugReport(report) {
    const bugsContainer = document.getElementById('bugs-container');
    if (!bugsContainer) return;
    
    bugsContainer.innerHTML = `
        <div class="bug-summary">
            <h2>Rapport de bugs</h2>
            <p>Total des problèmes détectés: ${report.totalBugs}</p>
            <div class="bug-categories">
                ${Object.entries(report.categories).map(([category, issues]) => `
                    <div class="bug-category">
                        <h3>${category}</h3>
                        <p>Problèmes: ${issues.length}</p>
                    </div>
                `).join('')}
            </div>
        </div>
        <div class="bug-details">
            ${report.details.map((bug, index) => `
                <div class="bug-item ${bug.type}">
                    <h4>${index + 1}. ${bug.message}</h4>
                    <p>Catégorie: ${bug.category}</p>
                    ${bug.element ? `<p>Élément: ${bug.element.selector}</p>` : ''}
                    ${bug.reference ? `<p>Référence: ${bug.reference}</p>` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

function clearLogs() {
    // Demander confirmation
    if (confirm('Êtes-vous sûr de vouloir effacer tous les logs ?')) {
        // Vider le conteneur de logs
        logsContainer.innerHTML = '';
        
        // Ajouter l'état vide
        const emptyState = document.createElement('div');
        emptyState.className = 'logs-empty-state';
        emptyState.innerHTML = `
            <i class="fas fa-clipboard-list"></i>
            <p>Le journal d'activité s'affichera ici</p>
        `;
        logsContainer.appendChild(emptyState);
        
        // Afficher une notification
        showNotification('Journal d\'activité effacé', 'info');
    }
}

// Ajouter l'appel à setupAdditionalHandlers dans l'initialisation
document.addEventListener('DOMContentLoaded', () => {
    // ... code existant ...
    
    // Configurer les gestionnaires supplémentaires
    setupAdditionalHandlers();
    
    // ... code existant ...
});
