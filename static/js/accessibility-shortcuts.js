/**
 * Raccourcis clavier pour l'accessibilité
 * @module AccessibilityShortcuts
 */

class AccessibilityShortcuts {
  constructor() {
    this.shortcuts = {
      'Alt+Shift+M': 'toggleMicrophone',
      'Alt+Shift+H': 'showHelp',
      'Alt+Shift+C': 'focusChat',
      'Alt+Shift+S': 'focusSearch',
      'Alt+Shift+T': 'toggleTheme',
      'Escape': 'closeModals'
    };

    this.init();
  }

  init() {
    document.addEventListener('keydown', (e) => this.handleKeyPress(e));

    // Afficher les raccourcis disponibles dans l'aide
    this.addShortcutHelp();
  }

  handleKeyPress(e) {
    const key = this.getKeyString(e);

    if (this.shortcuts[key]) {
      e.preventDefault();
      const action = this.shortcuts[key];
      this[action]();
    }
  }

  getKeyString(e) {
    const parts = [];
    if (e.altKey) parts.push('Alt');
    if (e.shiftKey) parts.push('Shift');
    if (e.ctrlKey) parts.push('Ctrl');
    if (e.metaKey) parts.push('Meta');
    parts.push(e.key);

    return parts.join('+');
  }

  toggleMicrophone() {
    const toggleBtn = document.getElementById('toggle-button');
    if (toggleBtn) {
      toggleBtn.click();
      const isPressed = toggleBtn.getAttribute('aria-pressed') === 'true';
      this.announce(`Microphone ${isPressed ? 'activé' : 'désactivé'}`);
    }
  }

  showHelp() {
    const helpBtn = document.getElementById('help-button');
    if (helpBtn) {
      helpBtn.click();
    }
  }

  focusChat() {
    const chatInput = document.getElementById('text-command-input');
    if (chatInput) {
      chatInput.focus();
      this.announce('Zone de saisie de conversation activée');
    } else {
      this.announce('Conversation non disponible');
    }
  }

  focusSearch() {
    const searchInput = document.getElementById('chat-search-input');
    if (searchInput) {
      searchInput.focus();
      this.announce('Barre de recherche activée');
    } else {
      this.announce('Recherche non disponible');
    }
  }

  toggleTheme() {
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
      themeBtn.click();
    } else {
      // Fallback: toggle dark mode manually
      const html = document.documentElement;
      const isDark = html.getAttribute('data-theme') === 'dark' ||
                     html.classList.contains('dark-mode');

      if (isDark) {
        html.removeAttribute('data-theme');
        html.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
        this.announce('Mode clair activé');
      } else {
        html.setAttribute('data-theme', 'dark');
        html.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
        this.announce('Mode sombre activé');
      }
    }
  }

  closeModals() {
    const modals = document.querySelectorAll('.modal.active, .active');
    let closedCount = 0;

    modals.forEach(modal => {
      if (modal.classList.contains('modal')) {
        modal.classList.remove('active');
        closedCount++;
      }
    });

    if (closedCount > 0) {
      this.announce(`${closedCount} fenêtre(s) fermée(s)`);
    }
  }

  announce(message) {
    const announcement = document.getElementById('announcements');
    if (announcement) {
      announcement.textContent = message;
      // Clear after announcement to allow repeat announcements
      setTimeout(() => {
        announcement.textContent = '';
      }, 1000);
    } else {
      // Fallback: create temporary announcement region
      const tempAnnouncement = document.createElement('div');
      tempAnnouncement.setAttribute('aria-live', 'polite');
      tempAnnouncement.setAttribute('aria-atomic', 'true');
      tempAnnouncement.className = 'sr-only';
      tempAnnouncement.style.position = 'absolute';
      tempAnnouncement.style.left = '-10000px';
      tempAnnouncement.style.width = '1px';
      tempAnnouncement.style.height = '1px';
      tempAnnouncement.textContent = message;

      document.body.appendChild(tempAnnouncement);
      setTimeout(() => {
        tempAnnouncement.remove();
      }, 1000);
    }
  }

  addShortcutHelp() {
    const helpSection = document.getElementById('keyboard-shortcuts-help');
    if (!helpSection) return;

    const shortcutsList = Object.entries(this.shortcuts)
      .filter(([key, action]) => action !== 'closeModals') // Exclude Escape from list
      .map(([key, action]) => {
        const label = this.getActionLabel(action);
        return `<li><kbd>${key}</kbd> - ${label}</li>`;
      }).join('');

    helpSection.innerHTML = `
      <h3>Raccourcis clavier</h3>
      <ul class="shortcuts-list">${shortcutsList}</ul>
      <p class="shortcuts-note">
        <i class="fas fa-info-circle" aria-hidden="true"></i>
        Utilisez <kbd>Échap</kbd> pour fermer les fenêtres modales
      </p>
    `;
  }

  getActionLabel(action) {
    const labels = {
      'toggleMicrophone': 'Activer/désactiver le micro',
      'showHelp': 'Afficher l\'aide',
      'focusChat': 'Focus sur la conversation',
      'focusSearch': 'Focus sur la recherche',
      'toggleTheme': 'Changer le thème',
      'closeModals': 'Fermer les modales'
    };
    return labels[action] || action;
  }
}

// Initialisation
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    if (!window.accessibilityShortcuts) {
      window.accessibilityShortcuts = new AccessibilityShortcuts();
    }
  });
} else {
  if (!window.accessibilityShortcuts) {
    window.accessibilityShortcuts = new AccessibilityShortcuts();
  }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AccessibilityShortcuts;
}
