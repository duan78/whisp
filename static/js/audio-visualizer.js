/**
 * Visualiseur audio temps réel pour Whisp
 * Utilise Web Audio API pour analyser et afficher l'audio
 * @module AudioVisualizer
 */

class AudioVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      console.error('Canvas non trouvé:', canvasId);
      return;
    }

    this.ctx = this.canvas.getContext('2d');
    this.audioContext = null;
    this.analyser = null;
    this.dataArray = null;
    this.isListening = false;
    this.animationId = null;

    // Configuration
    this.config = {
      fftSize: 2048,
      smoothingTimeConstant: 0.8,
      barCount: 32,
      barGap: 2,
      minHeight: 4,
      maxHeightRatio: 0.8
    };

    // Couleurs selon le thème
    this.colors = {
      primary: '#2563EB',
      secondary: '#7C3AED',
      gradientStart: 'rgba(37, 99, 235, 0.8)',
      gradientEnd: 'rgba(124, 58, 237, 0.3)'
    };

    this.init();
  }

  async init() {
    // Setup canvas size
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    // Écouter les changements de thème
    this.updateColors();
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      this.updateColors();
    });

    // Écouter les changements de thème manuels
    const observer = new MutationObserver(() => this.updateColors());
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme', 'class']
    });

    // Écouter les événements de l'assistant
    this.setupEventListeners();

    // Afficher l'état initial
    this.drawIdleState();
  }

  resizeCanvas() {
    const parent = this.canvas.parentElement;
    if (parent) {
      this.canvas.width = parent.clientWidth;
      this.canvas.height = parent.clientHeight || 120;
    }
    this.width = this.canvas.width;
    this.height = this.canvas.height;
  }

  updateColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                   document.documentElement.classList.contains('dark-mode');
    this.colors = {
      primary: isDark ? '#60A5FA' : '#2563EB',
      secondary: isDark ? '#A78BFA' : '#7C3AED',
      gradientStart: isDark ? 'rgba(96, 165, 250, 0.8)' : 'rgba(37, 99, 235, 0.8)',
      gradientEnd: isDark ? 'rgba(167, 139, 250, 0.3)' : 'rgba(124, 58, 237, 0.3)'
    };
  }

  async startListening() {
    if (this.isListening) return;

    try {
      // Créer l'AudioContext
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

      // Créer l'analyseur
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = this.config.fftSize;
      this.analyser.smoothingTimeConstant = this.config.smoothingTimeConstant;

      // Créer le tableau de données
      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);

      // Dans un vrai scénario, on connecterait ici au stream audio du micro
      // Pour l'instant, on simule avec des données aléatoires
      this.isListening = true;
      this.animate();

      this.updateState('listening');
    } catch (error) {
      console.error('Erreur lors du démarrage de l\'écoute:', error);
      this.updateState('error');
    }
  }

  stopListening() {
    this.isListening = false;
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.drawIdleState();
    this.updateState('idle');
  }

  animate() {
    if (!this.isListening) return;

    this.animationId = requestAnimationFrame(() => this.animate());

    // Simuler des données audio (remplacer par vraies données du micro)
    this.simulateAudioData();

    // Dessiner
    this.draw();
  }

  simulateAudioData() {
    if (!this.dataArray) return;

    // Générer des données aléatoires pour la démo
    for (let i = 0; i < this.dataArray.length; i++) {
      const value = Math.random() * 255;
      this.dataArray[i] = value;
    }
  }

  draw() {
    const ctx = this.ctx;
    const width = this.width;
    const height = this.height;

    // Clear
    ctx.clearRect(0, 0, width, height);

    // Dessiner les barres de fréquence
    const barCount = this.config.barCount;
    const barWidth = (width / barCount) - this.config.barGap;

    // Créer le gradient
    const gradient = ctx.createLinearGradient(0, height, 0, 0);
    gradient.addColorStop(0, this.colors.gradientEnd);
    gradient.addColorStop(1, this.colors.gradientStart);

    ctx.fillStyle = gradient;

    // Dessiner chaque barre
    for (let i = 0; i < barCount; i++) {
      // Prendre un échantillon des données
      const dataIndex = Math.floor(i * this.dataArray.length / barCount);
      const value = this.dataArray ? this.dataArray[dataIndex] : 0;

      // Calculer la hauteur de la barre
      const barHeight = Math.max(
        this.config.minHeight,
        (value / 255) * height * this.config.maxHeightRatio
      );

      const y = height - barHeight;
      const xPos = i * (barWidth + this.config.barGap);

      // Dessiner la barre avec coins arrondis
      this.drawRoundedRect(ctx, xPos, y, barWidth, barHeight, 4);
    }
  }

  drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    ctx.fill();
  }

  drawIdleState() {
    const ctx = this.ctx;
    const width = this.width;
    const height = this.height;

    ctx.clearRect(0, 0, width, height);

    // Dessiner une ligne d'état
    ctx.strokeStyle = this.colors.primary;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // Ajouter du texte
    ctx.fillStyle = this.colors.primary;
    ctx.font = '14px Inter';
    ctx.textAlign = 'center';
    ctx.fillText('Prêt à écouter', width / 2, height / 2 - 10);
  }

  drawProcessingState() {
    const ctx = this.ctx;
    const width = this.width;
    const height = this.height;

    ctx.clearRect(0, 0, width, height);

    // Dessiner un indicateur de chargement
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 20;

    ctx.strokeStyle = this.colors.secondary;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.stroke();

    // Rayon animé
    const startAngle = Date.now() / 500;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, startAngle + Math.PI / 2);
    ctx.stroke();
  }

  updateState(state) {
    const stateElement = document.getElementById('voice-state-indicator');
    if (stateElement) {
      stateElement.setAttribute('data-state', state);
      stateElement.setAttribute('aria-label', `État vocal: ${this.getStateLabel(state)}`);

      // Update label text
      const labelElement = stateElement.querySelector('.voice-state-label');
      if (labelElement) {
        labelElement.textContent = this.getStateLabel(state);
      }
    }

    // Mettre à jour l'attribut aria-live pour annoncer le changement
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = `État vocal: ${this.getStateLabel(state)}`;
    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 1000);
  }

  getStateLabel(state) {
    const labels = {
      'idle': 'En attente',
      'listening': 'Écoute en cours',
      'processing': 'Traitement en cours',
      'responding': 'Réponse en cours',
      'error': 'Erreur'
    };
    return labels[state] || state;
  }

  setupEventListeners() {
    // Écouter les événements SSE
    window.addEventListener('whisp:state-change', (event) => {
      const { state } = event.detail;
      if (state === 'listening') {
        this.startListening();
      } else if (state === 'idle') {
        this.stopListening();
      } else if (state === 'processing') {
        this.drawProcessingState();
      }
    });
  }

  destroy() {
    this.stopListening();
    window.removeEventListener('resize', this.resizeCanvas);
  }
}

// Export
window.AudioVisualizer = AudioVisualizer;

// Auto-initialisation si le canvas est présent
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('audio-visualizer');
    if (canvas) {
      window.audioVisualizer = new AudioVisualizer('audio-visualizer');
    }
  });
} else {
  const canvas = document.getElementById('audio-visualizer');
  if (canvas) {
    window.audioVisualizer = new AudioVisualizer('audio-visualizer');
  }
}
