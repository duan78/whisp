/**
 * Gestion de l'interface de conversation
 * @module ChatInterface
 */

class ChatInterface {
  constructor() {
    this.messages = [];
    this.filteredMessages = [];
    this.currentFilter = {
      commands: true,
      responses: true,
      errors: false
    };
    this.searchQuery = '';

    this.init();
  }

  init() {
    // Récupérer les éléments DOM
    this.chatMessages = document.getElementById('chat-messages');
    this.searchInput = document.getElementById('chat-search-input');
    this.textCommandInput = document.getElementById('text-command-input');

    if (!this.chatMessages) {
      console.warn('Chat interface element not found');
      return;
    }

    // Setup event listeners
    this.setupEventListeners();

    // Charger les messages existants depuis les logs
    this.loadExistingMessages();

    // Écouter les nouveaux messages via SSE
    this.listenForNewMessages();
  }

  setupEventListeners() {
    // Recherche
    const searchBtn = document.getElementById('search-chat');
    if (searchBtn) {
      searchBtn.addEventListener('click', () => this.toggleSearch());
    }

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase();
        this.filterMessages();
      });
    }

    // Filtres
    const filterCommands = document.getElementById('filter-commands');
    const filterResponses = document.getElementById('filter-responses');
    const filterErrors = document.getElementById('filter-errors');

    if (filterCommands) {
      filterCommands.addEventListener('change', (e) => {
        this.currentFilter.commands = e.target.checked;
        this.filterMessages();
      });
    }

    if (filterResponses) {
      filterResponses.addEventListener('change', (e) => {
        this.currentFilter.responses = e.target.checked;
        this.filterMessages();
      });
    }

    if (filterErrors) {
      filterErrors.addEventListener('change', (e) => {
        this.currentFilter.errors = e.target.checked;
        this.filterMessages();
      });
    }

    // Export
    const exportBtn = document.getElementById('export-chat');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportChat());
    }

    // Clear
    const clearBtn = document.getElementById('clear-chat');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        if (confirm('Êtes-vous sûr de vouloir effacer toute la conversation ?')) {
          this.clearChat();
        }
      });
    }

    // Commande texte
    const sendBtn = document.getElementById('send-text-command');
    if (sendBtn) {
      sendBtn.addEventListener('click', () => this.sendTextCommand());
    }

    if (this.textCommandInput) {
      this.textCommandInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.sendTextCommand();
        }
      });
    }
  }

  loadExistingMessages() {
    // Charger depuis assistant_state.logs
    fetch('/get_logs')
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch logs');
        return response.json();
      })
      .then(data => {
        if (data.logs && Array.isArray(data.logs)) {
          data.logs.forEach(log => {
            this.addMessage(log.message, log.type, log.timestamp, false);
          });
          this.scrollToBottom();
        }
      })
      .catch(error => {
        console.error('Erreur lors du chargement des messages:', error);
      });
  }

  addMessage(content, type = 'info', timestamp = null, animate = true) {
    const message = {
      id: Date.now() + Math.random(),
      content,
      type,
      timestamp: timestamp || new Date().toISOString()
    };

    this.messages.push(message);
    this.filterMessages();

    if (animate) {
      this.scrollToBottom();
    }

    // Annoncer pour les lecteurs d'écran
    this.announceForScreenReader(message);
  }

  filterMessages() {
    this.filteredMessages = this.messages.filter(msg => {
      // Filtre par type
      if (!this.currentFilter.commands && msg.type === 'command') return false;
      if (!this.currentFilter.responses && (msg.type === 'response' || msg.type === 'info')) return false;
      if (!this.currentFilter.errors && msg.type === 'error') return false;

      // Filtre par recherche
      if (this.searchQuery && !msg.content.toLowerCase().includes(this.searchQuery)) {
        return false;
      }

      return true;
    });

    this.renderMessages();
  }

  renderMessages() {
    if (!this.chatMessages) return;

    this.chatMessages.innerHTML = '';

    this.filteredMessages.forEach(msg => {
      const messageEl = this.createMessageElement(msg);
      this.chatMessages.appendChild(messageEl);
    });

    if (this.filteredMessages.length === 0) {
      this.chatMessages.innerHTML = `
        <div class="chat-empty-state" role="status">
          <i class="fas fa-comments" aria-hidden="true"></i>
          <p>Aucun message à afficher</p>
        </div>
      `;
    }
  }

  createMessageElement(message) {
    const div = document.createElement('div');
    div.className = `chat-message ${message.type}`;
    div.setAttribute('data-message-id', message.id);

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    const content = document.createElement('p');
    content.className = 'chat-message-content';
    content.textContent = message.content;
    bubble.appendChild(content);

    const meta = document.createElement('div');
    meta.className = 'chat-message-meta';

    const time = document.createElement('time');
    const date = new Date(message.timestamp);
    time.textContent = date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    time.dateTime = message.timestamp;
    meta.appendChild(time);

    const typeLabel = document.createElement('span');
    typeLabel.className = 'message-type-label';
    typeLabel.textContent = this.getMessageTypeLabel(message.type);
    typeLabel.setAttribute('aria-label', `Type: ${this.getMessageTypeLabel(message.type)}`);
    meta.appendChild(typeLabel);

    bubble.appendChild(meta);

    // Actions (copier, supprimer)
    const actions = document.createElement('div');
    actions.className = 'chat-message-actions';

    const copyBtn = document.createElement('button');
    copyBtn.className = 'chat-message-action-btn';
    copyBtn.innerHTML = '<i class="fas fa-copy" aria-hidden="true"></i>';
    copyBtn.setAttribute('aria-label', 'Copier le message');
    copyBtn.addEventListener('click', () => this.copyMessage(message.content));
    actions.appendChild(copyBtn);

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'chat-message-action-btn';
    deleteBtn.innerHTML = '<i class="fas fa-trash" aria-hidden="true"></i>';
    deleteBtn.setAttribute('aria-label', 'Supprimer le message');
    deleteBtn.addEventListener('click', () => this.deleteMessage(message.id));
    actions.appendChild(deleteBtn);

    bubble.appendChild(actions);
    div.appendChild(bubble);

    return div;
  }

  getMessageTypeLabel(type) {
    const labels = {
      'command': 'Commande',
      'response': 'Réponse',
      'info': 'Info',
      'error': 'Erreur',
      'warning': 'Avertissement'
    };
    return labels[type] || type;
  }

  copyMessage(content) {
    navigator.clipboard.writeText(content).then(() => {
      this.showNotification('Message copié !', 'success');
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  }

  deleteMessage(messageId) {
    this.messages = this.messages.filter(msg => msg.id !== messageId);
    this.filterMessages();
  }

  toggleSearch() {
    const searchBar = document.getElementById('chat-search-bar');
    if (searchBar) {
      searchBar.classList.toggle('hidden');
      if (!searchBar.classList.contains('hidden') && this.searchInput) {
        this.searchInput.focus();
      }
    }
  }

  scrollToBottom() {
    if (this.chatMessages) {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
  }

  exportChat() {
    const exportData = {
      exportDate: new Date().toISOString(),
      messageCount: this.messages.length,
      messages: this.messages
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `whisp-conversation-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);

    this.showNotification('Conversation exportée !', 'success');
  }

  clearChat() {
    this.messages = [];
    this.filteredMessages = [];
    this.renderMessages();

    // Aussi clear du backend
    fetch('/clear_logs', { method: 'POST' })
      .then(() => {
        this.showNotification('Conversation effacée', 'success');
      })
      .catch(error => {
        console.error('Erreur lors de l\'effacement:', error);
        this.showNotification('Erreur lors de l\'effacement', 'error');
      });
  }

  sendTextCommand() {
    const command = this.textCommandInput.value.trim();
    if (!command) return;

    fetch('/process_command', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ command })
    })
      .then(response => response.json())
      .then(data => {
        this.textCommandInput.value = '';
        if (data.error) {
          this.showNotification(data.error, 'error');
        }
      })
      .catch(error => {
        console.error('Erreur lors de l\'envoi de la commande:', error);
        this.showNotification('Erreur lors de l\'envoi', 'error');
      });
  }

  listenForNewMessages() {
    // Les messages arrivent déjà via SSE dans script.js
    // On ajoute un hook pour les capturer
    window.addEventListener('whisp:new-log', (event) => {
      const { message, type, timestamp } = event.detail;
      this.addMessage(message, type, timestamp);
    });
  }

  announceForScreenReader(message) {
    // Utiliser une région live pour annoncer les nouveaux messages
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = `Nouveau message ${this.getMessageTypeLabel(message.type)}: ${message.content}`;

    document.body.appendChild(announcement);
    setTimeout(() => announcement.remove(), 1000);
  }

  showNotification(message, type = 'info') {
    // Réutiliser la fonction existante si disponible
    if (window.showNotification) {
      window.showNotification(message, type);
    } else {
      console.log(`[${type.toUpperCase()}] ${message}`);
    }
  }
}

// Initialiser quand le DOM est prêt
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
  });
} else {
  window.chatInterface = new ChatInterface();
}

// Export pour utilisation externe
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ChatInterface;
}
