/**
 * Gestion de la configuration de Whisp
 * @module ConfigManager
 */

class ConfigManager {
  constructor() {
    this.config = {};
    this.init();
  }

  async init() {
    await this.loadConfig();
    this.setupEventListeners();
    this.populateUI();
  }

  async loadConfig() {
    try {
      const response = await fetch('/get_all_config');
      if (!response.ok) throw new Error('Failed to load config');
      this.config = await response.json();
    } catch (error) {
      console.error('Erreur lors du chargement de la configuration:', error);
      this.showNotification('Erreur lors du chargement', 'error');
    }
  }

  setupEventListeners() {
    // Moteur STT
    const sttEngineSelect = document.getElementById('stt-engine-select');
    if (sttEngineSelect) {
      sttEngineSelect.addEventListener('change', (e) => {
        this.changeSTTEngine(e.target.value);
      });
    }

    // Moteur TTS
    const ttsEngineSelect = document.getElementById('tts-engine-select');
    if (ttsEngineSelect) {
      ttsEngineSelect.addEventListener('change', (e) => {
        this.changeTTSEngine(e.target.value);
      });
    }

    // Appliquer les réglages
    const applyBtn = document.getElementById('apply-stt-settings');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        this.applySTTSettings();
      });
    }

    // Réinitialiser
    const resetBtn = document.getElementById('reset-stt-settings');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.resetSTTSettings();
      });
    }

    // Redémarrer
    const restartBtn = document.getElementById('restart-recognition');
    if (restartBtn) {
      restartBtn.addEventListener('click', () => {
        this.restartRecognition();
      });
    }

    // Sliders avec output en temps réel
    this.setupSliders();
  }

  setupSliders() {
    document.querySelectorAll('input[type="range"]').forEach(slider => {
      const output = slider.nextElementSibling;
      if (output && output.tagName === 'OUTPUT') {
        slider.addEventListener('input', () => {
          output.textContent = this.formatSliderValue(slider);
        });
      }
    });
  }

  formatSliderValue(slider) {
    const value = parseFloat(slider.value);
    if (slider.id === 'voice-rate') {
      return `${value}x`;
    } else if (slider.id === 'voice-volume') {
      return `${Math.round(value * 100)}%`;
    }
    return value;
  }

  populateUI() {
    // Populate form fields with current config
    if (this.config.stt_engine) {
      const sttSelect = document.getElementById('stt-engine-select');
      if (sttSelect) {
        sttSelect.value = this.config.stt_engine;
      }
    }

    if (this.config.tts_engine) {
      const ttsSelect = document.getElementById('tts-engine-select');
      if (ttsSelect) {
        ttsSelect.value = this.config.tts_engine;
        if (this.config.tts_engine === 'coqui') {
          this.loadCoquiModels();
        }
      }
    }

    // Populate other settings...
  }

  async changeSTTEngine(engine) {
    try {
      const response = await fetch('/change_stt_engine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine })
      });

      const data = await response.json();
      if (data.success) {
        this.showNotification(`Moteur STT changé: ${engine}`, 'success');
        // Update local config
        this.config.stt_engine = engine;
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors du changement de moteur:', error);
      this.showNotification('Erreur lors du changement', 'error');
    }
  }

  async changeTTSEngine(engine) {
    try {
      const response = await fetch('/change_tts_engine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine })
      });

      const data = await response.json();
      if (data.success) {
        this.showNotification(`Moteur TTS changé: ${engine}`, 'success');
        this.config.tts_engine = engine;

        // Show Coqui models if applicable
        const coquiContainer = document.getElementById('coqui-models-container');
        if (coquiContainer) {
          if (engine === 'coqui') {
            coquiContainer.classList.remove('hidden');
            this.loadCoquiModels();
          } else {
            coquiContainer.classList.add('hidden');
          }
        }
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors du changement de moteur:', error);
      this.showNotification('Erreur lors du changement', 'error');
    }
  }

  async loadCoquiModels() {
    try {
      const response = await fetch('/get_coqui_models');
      const models = await response.json();

      const container = document.getElementById('coqui-models-list');
      if (!container) return;

      if (Array.isArray(models) && models.length > 0) {
        container.innerHTML = models.map(model => `
          <button class="model-card" data-model="${model.id}" aria-label="Sélectionner le modèle ${model.name}">
            <i class="fas fa-waveform" aria-hidden="true"></i>
            <div class="model-info">
              <h4>${model.name}</h4>
              <p>${model.description || 'Modèle TTS Coqui'}</p>
            </div>
          </button>
        `).join('');

        container.querySelectorAll('.model-card').forEach(card => {
          card.addEventListener('click', () => {
            this.selectCoquiModel(card.dataset.model);
          });
        });
      } else {
        container.innerHTML = '<p>Aucun modèle disponible</p>';
      }
    } catch (error) {
      console.error('Erreur lors du chargement des modèles:', error);
    }
  }

  async selectCoquiModel(modelId) {
    try {
      const response = await fetch('/change_coqui_model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId })
      });

      const data = await response.json();
      if (data.success) {
        this.showNotification(`Modèle Coqui changé: ${modelId}`, 'success');
        this.config.coqui_model = modelId;
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors du changement de modèle:', error);
    }
  }

  async applySTTSettings() {
    const settings = {};

    // Get chunk size
    const chunkSizeInput = document.getElementById('chunk-size');
    if (chunkSizeInput) {
      settings.chunk_size = parseInt(chunkSizeInput.value);
    }

    // Get phrase timeout
    const phraseTimeoutInput = document.getElementById('phrase-timeout');
    if (phraseTimeoutInput) {
      settings.phrase_timeout = parseFloat(phraseTimeoutInput.value);
    }

    // Get pause threshold
    const pauseThresholdInput = document.getElementById('pause-threshold');
    if (pauseThresholdInput) {
      settings.pause_threshold = parseFloat(pauseThresholdInput.value);
    }

    // Get language
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
      settings.language = languageSelect.value;
    }

    // Get wake word
    const wakeWordInput = document.getElementById('wake-word');
    if (wakeWordInput) {
      settings.wake_word = wakeWordInput.value;
    }

    // Get dynamic energy threshold
    const dynamicEnergyCheckbox = document.getElementById('dynamic-energy-threshold');
    if (dynamicEnergyCheckbox) {
      settings.dynamic_energy_threshold = dynamicEnergyCheckbox.checked;
    }

    try {
      const response = await fetch('/set_stt_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      const data = await response.json();
      if (data.success) {
        this.showNotification('Paramètres STT appliqués', 'success');
        // Update local config
        Object.assign(this.config, settings);
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors de l\'application des paramètres:', error);
      this.showNotification('Erreur lors de l\'application', 'error');
    }
  }

  async resetSTTSettings() {
    try {
      const response = await fetch('/reset_stt_settings', { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        this.showNotification('Paramètres STT réinitialisés', 'success');
        await this.loadConfig();
        this.populateUI();
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors de la réinitialisation:', error);
      this.showNotification('Erreur lors de la réinitialisation', 'error');
    }
  }

  async restartRecognition() {
    try {
      const response = await fetch('/restart_recognition', { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        this.showNotification('Reconnaissance redémarrée', 'success');
      } else {
        this.showNotification(`Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      console.error('Erreur lors du redémarrage:', error);
      this.showNotification('Erreur lors du redémarrage', 'error');
    }
  }

  showNotification(message, type = 'info') {
    if (window.showNotification) {
      window.showNotification(message, type);
    } else {
      console.log(`[${type.toUpperCase()}] ${message}`);
      // Fallback: create a toast
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.textContent = message;
      toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 24px;
        background: ${type === 'error' ? '#e74c3c' : type === 'success' ? '#2ecc71' : '#3498db'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
      `;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.remove();
      }, 3000);
    }
  }
}

// Initialisation
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (!window.configManager) {
      window.configManager = new ConfigManager();
    }
  });
} else {
  if (!window.configManager) {
    window.configManager = new ConfigManager();
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ConfigManager;
}
