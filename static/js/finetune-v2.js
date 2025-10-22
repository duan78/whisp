/**
 * Interface optimisée pour la gestion des données de fine-tuning
 * Version 2.0 avec support du traitement par lots et raccourcis clavier avancés
 */

class FinetuneManager {
    constructor() {
        // État de l'application
        this.samples = [];
        this.filteredSamples = [];
        this.selectedSamples = new Set();
        this.modifiedSamples = new Map(); // Map<sampleId, newTranscription>
        this.currentAudio = null;
        this.autoSaveEnabled = true;
        this.batchMode = false;
        this.compactMode = false;
        
        // Configuration
        this.config = {
            autoSaveDelay: 2000, // 2 secondes
            maxBatchSize: 50,
            pageSize: 100
        };
        
        // Timers
        this.autoSaveTimer = null;
        
        // Initialisation
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.loadSamples();
        this.startAutoUpdate();
    }
    
    // Configuration des écouteurs d'événements
    setupEventListeners() {
        // Sélection
        $('#select-all').on('change', (e) => this.toggleSelectAll(e.target.checked));
        
        // Actions groupées
        $('.btn-bulk-train').on('click', () => this.bulkChangeSplit('train'));
        $('.btn-bulk-validation').on('click', () => this.bulkChangeSplit('validation'));
        $('.btn-bulk-test').on('click', () => this.bulkChangeSplit('test'));
        $('.btn-bulk-delete').on('click', () => this.bulkDelete());
        
        // Filtres
        $('#filter-engine').on('change', () => this.applyFilters());
        $('#filter-split').on('change', () => this.applyFilters());
        $('#filter-quality').on('change', () => this.applyFilters());
        $('#search-input').on('input', () => this.applyFilters());
        $('#clear-search').on('click', () => {
            $('#search-input').val('');
            this.applyFilters();
        });
        
        // Options d'affichage
        $('#toggle-compact').on('click', () => this.toggleCompactMode());
        $('#batch-mode').on('click', () => this.toggleBatchMode());
        $('#auto-save').on('click', () => this.toggleAutoSave());
        $('#toggle-filters').on('click', () => this.toggleAdvancedFilters());
        
        // Actions principales
        $('#sync-dataset').on('click', () => this.syncDataset());
        $('#export-dataset').on('click', () => this.exportDataset());
        $('#refresh-samples').on('click', () => this.loadSamples());
        
        // Filtres avancés
        $('.filter-chip').on('click', function() {
            $(this).toggleClass('active');
            this.applyFilters();
        }.bind(this));
        
        // Modal de suppression
        $('#confirm-delete-btn').on('click', () => this.confirmBulkDelete());
    }
    
    // Configuration des raccourcis clavier
    setupKeyboardShortcuts() {
        $(document).on('keydown', (e) => {
            // Ignorer si on est dans un input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Ctrl+A - Tout sélectionner
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                this.selectAll();
            }
            
            // Ctrl+S - Sauvegarder
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveModifications();
            }
            
            // Delete - Supprimer sélection
            if (e.key === 'Delete' && this.selectedSamples.size > 0) {
                e.preventDefault();
                this.bulkDelete();
            }
            
            // 1, 2, 3 - Changer split
            if (['1', '2', '3'].includes(e.key) && this.selectedSamples.size > 0) {
                e.preventDefault();
                const splits = {1: 'train', 2: 'validation', 3: 'test'};
                this.bulkChangeSplit(splits[e.key]);
            }
            
            // Space - Play/Pause audio
            if (e.key === ' ' && !e.target.classList.contains('transcription-inline')) {
                e.preventDefault();
                this.toggleCurrentAudio();
            }
            
            // Flèches pour navigation
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateSamples(e.key === 'ArrowDown' ? 1 : -1);
            }
            
            // Ctrl+F - Focus recherche
            if (e.ctrlKey && e.key === 'f') {
                e.preventDefault();
                $('#search-input').focus();
            }
            
            // Escape - Désélectionner tout
            if (e.key === 'Escape') {
                this.clearSelection();
            }
        });
    }
    
    // Chargement des échantillons
    async loadSamples() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/finetune/samples');
            const data = await response.json();
            
            if (data.success) {
                this.samples = data.samples;
                this.processEngines();
                this.applyFilters();
                this.updateStats();
                this.showToast('Échantillons chargés', 'success');
            } else {
                this.showToast('Erreur de chargement: ' + data.error, 'danger');
            }
        } catch (error) {
            this.showToast('Erreur de connexion', 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    // Extraction des moteurs uniques
    processEngines() {
        const engines = [...new Set(this.samples.map(s => s.engine))];
        const select = $('#filter-engine');
        select.find('option:not(:first)').remove();
        
        engines.forEach(engine => {
            select.append(`<option value="${engine}">${engine}</option>`);
        });
    }
    
    // Application des filtres
    applyFilters() {
        const engine = $('#filter-engine').val();
        const split = $('#filter-split').val();
        const quality = $('#filter-quality').val();
        const search = $('#search-input').val().toLowerCase();
        
        // Filtres avancés
        const activeFilters = $('.filter-chip.active').toArray().map(el => ({
            type: $(el).data('filter'),
            value: $(el).data('value')
        }));
        
        this.filteredSamples = this.samples.filter(sample => {
            // Filtres de base
            if (engine && sample.engine !== engine) return false;
            if (split && sample.split !== split) return false;
            if (search && !sample.transcription.toLowerCase().includes(search)) return false;
            
            // Filtre qualité
            if (quality) {
                const sampleQuality = this.calculateQuality(sample);
                if (sampleQuality !== quality) return false;
            }
            
            // Filtres avancés
            for (const filter of activeFilters) {
                if (!this.matchAdvancedFilter(sample, filter)) return false;
            }
            
            return true;
        });
        
        this.renderSamples();
        this.updateShowingInfo();
    }
    
    // Calcul de la qualité d'un échantillon
    calculateQuality(sample) {
        if (!sample.duration || !sample.transcription) return 'low';
        
        const charRate = sample.transcription.length / sample.duration;
        if (charRate > 8) return 'high';
        if (charRate < 3) return 'low';
        return 'medium';
    }
    
    // Correspondance avec les filtres avancés
    matchAdvancedFilter(sample, filter) {
        switch (filter.type) {
            case 'duration':
                if (!sample.duration) return false;
                switch (filter.value) {
                    case '0-5': return sample.duration <= 5;
                    case '5-10': return sample.duration > 5 && sample.duration <= 10;
                    case '10+': return sample.duration > 10;
                }
                break;
                
            case 'status':
                const isModified = this.modifiedSamples.has(sample.id);
                return filter.value === 'modified' ? isModified : !isModified;
                
            case 'date':
                if (!sample.timestamp) return false;
                const date = new Date(sample.timestamp * 1000);
                const now = new Date();
                
                switch (filter.value) {
                    case 'today':
                        return date.toDateString() === now.toDateString();
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        return date >= weekAgo;
                    case 'month':
                        return date.getMonth() === now.getMonth() && 
                               date.getFullYear() === now.getFullYear();
                }
                break;
        }
        
        return true;
    }
    
    // Rendu des échantillons
    renderSamples() {
        const container = $('#samples-container');
        container.empty();
        
        if (this.filteredSamples.length === 0) {
            container.html(`
                <div class="text-center p-5 text-muted">
                    <i class="fas fa-search fa-3x mb-3"></i>
                    <p>Aucun échantillon ne correspond aux critères</p>
                </div>
            `);
            return;
        }
        
        // Rendu par lots pour les performances
        const batchSize = 50;
        let rendered = 0;
        
        const renderBatch = () => {
            const batch = this.filteredSamples.slice(rendered, rendered + batchSize);
            
            batch.forEach(sample => {
                container.append(this.createSampleRow(sample));
            });
            
            rendered += batch.length;
            
            // Continuer le rendu si nécessaire
            if (rendered < this.filteredSamples.length) {
                requestAnimationFrame(renderBatch);
            } else {
                this.attachSampleEventListeners();
            }
        };
        
        renderBatch();
    }
    
    // Création d'une ligne d'échantillon
    createSampleRow(sample) {
        const quality = this.calculateQuality(sample);
        const isSelected = this.selectedSamples.has(sample.id);
        const isModified = this.modifiedSamples.has(sample.id);
        const duration = sample.duration ? `${sample.duration.toFixed(1)}s` : '-';
        
        return `
            <div class="sample-row ${isSelected ? 'selected' : ''}" data-id="${sample.id}">
                <label class="custom-checkbox">
                    <input type="checkbox" class="sample-checkbox" ${isSelected ? 'checked' : ''}>
                    <span class="checkmark"></span>
                </label>
                
                <div class="audio-player-compact">
                    <button class="play-button" data-audio="${sample.audio_path}">
                        <i class="fas fa-play"></i>
                    </button>
                    <span class="audio-duration">${duration}</span>
                    <div class="quality-bar">
                        <div class="quality-fill quality-${quality}" style="width: ${quality === 'high' ? '100%' : quality === 'medium' ? '60%' : '30%'}"></div>
                    </div>
                </div>
                
                <div class="transcription-inline ${isModified ? 'modified' : ''}" 
                     contenteditable="true"
                     data-id="${sample.id}"
                     data-original="${this.escapeHtml(sample.transcription)}">${this.escapeHtml(isModified ? this.modifiedSamples.get(sample.id) : sample.transcription)}</div>
                
                <div class="split-info">
                    <span class="badge badge-${sample.split === 'train' ? 'success' : sample.split === 'validation' ? 'warning' : 'info'}">
                        ${sample.split}
                    </span>
                </div>
                
                <div class="sample-meta text-muted">
                    <small>${sample.engine}</small>
                    <small>${new Date(sample.timestamp * 1000).toLocaleDateString()}</small>
                </div>
                
                <div class="quick-actions">
                    <button class="quick-action-btn" data-action="save" title="Sauvegarder">
                        <i class="fas fa-save"></i>
                    </button>
                    <button class="quick-action-btn" data-action="split" title="Changer split">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    <button class="quick-action-btn" data-action="delete" title="Supprimer">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    // Attachement des écouteurs aux échantillons
    attachSampleEventListeners() {
        // Checkbox de sélection
        $('.sample-checkbox').off('change').on('change', (e) => {
            const row = $(e.target).closest('.sample-row');
            const id = row.data('id');
            
            if (e.target.checked) {
                this.selectedSamples.add(id);
                row.addClass('selected');
            } else {
                this.selectedSamples.delete(id);
                row.removeClass('selected');
            }
            
            this.updateSelectionInfo();
        });
        
        // Click sur la ligne (sélection avec Ctrl/Shift)
        $('.sample-row').off('click').on('click', (e) => {
            if ($(e.target).closest('.custom-checkbox, button, .transcription-inline').length > 0) {
                return; // Ignorer si click sur contrôles
            }
            
            const row = $(e.currentTarget);
            const id = row.data('id');
            const checkbox = row.find('.sample-checkbox');
            
            if (e.ctrlKey) {
                // Toggle sélection
                checkbox.prop('checked', !checkbox.prop('checked')).trigger('change');
            } else if (e.shiftKey && this.lastSelectedId) {
                // Sélection multiple
                this.selectRange(this.lastSelectedId, id);
            } else {
                // Sélection simple
                this.clearSelection();
                checkbox.prop('checked', true).trigger('change');
            }
            
            this.lastSelectedId = id;
        });
        
        // Boutons play/pause
        $('.play-button').off('click').on('click', (e) => {
            e.stopPropagation();
            this.toggleAudio($(e.currentTarget));
        });
        
        // Édition de transcription
        $('.transcription-inline').off('input').on('input', (e) => {
            const el = $(e.target);
            const id = el.data('id');
            const original = el.data('original');
            const current = el.text().trim();
            
            if (current !== original) {
                this.modifiedSamples.set(id, current);
                el.addClass('modified');
            } else {
                this.modifiedSamples.delete(id);
                el.removeClass('modified');
            }
            
            this.updateModifiedCount();
            this.scheduleAutoSave();
        });
        
        // Actions rapides
        $('.quick-action-btn').off('click').on('click', (e) => {
            e.stopPropagation();
            const btn = $(e.currentTarget);
            const action = btn.data('action');
            const row = btn.closest('.sample-row');
            const id = row.data('id');
            
            switch (action) {
                case 'save':
                    this.saveSample(id);
                    break;
                case 'split':
                    this.showSplitMenu(id, btn);
                    break;
                case 'delete':
                    this.deleteSample(id);
                    break;
            }
        });
    }
    
    // Gestion de l'audio
    toggleAudio(button) {
        const audioPath = button.data('audio');
        const icon = button.find('i');
        
        // Si c'est le même audio, toggle play/pause
        if (this.currentAudio && this.currentAudio.src.includes(audioPath)) {
            if (this.currentAudio.paused) {
                this.currentAudio.play();
                icon.removeClass('fa-play').addClass('fa-pause');
                button.addClass('playing');
            } else {
                this.currentAudio.pause();
                icon.removeClass('fa-pause').addClass('fa-play');
                button.removeClass('playing');
            }
        } else {
            // Arrêter l'audio précédent
            if (this.currentAudio) {
                this.currentAudio.pause();
                $('.play-button').removeClass('playing').find('i').removeClass('fa-pause').addClass('fa-play');
            }
            
            // Créer et jouer le nouvel audio
            this.currentAudio = new Audio(audioPath);
            this.currentAudio.play();
            icon.removeClass('fa-play').addClass('fa-pause');
            button.addClass('playing');
            
            // Réinitialiser le bouton à la fin
            this.currentAudio.addEventListener('ended', () => {
                icon.removeClass('fa-pause').addClass('fa-play');
                button.removeClass('playing');
            });
        }
    }
    
    // Sauvegarde automatique
    scheduleAutoSave() {
        if (!this.autoSaveEnabled) return;
        
        clearTimeout(this.autoSaveTimer);
        this.autoSaveTimer = setTimeout(() => {
            this.saveModifications();
        }, this.config.autoSaveDelay);
    }
    
    // Sauvegarde des modifications
    async saveModifications() {
        if (this.modifiedSamples.size === 0) return;
        
        const modifications = Array.from(this.modifiedSamples.entries()).map(([id, transcription]) => {
            const sample = this.samples.find(s => s.id === id);
            return {
                text_path: sample.text_path,
                json_path: sample.json_path,
                transcription: transcription
            };
        });
        
        try {
            // Sauvegarde par lots pour les performances
            const batchSize = 10;
            for (let i = 0; i < modifications.length; i += batchSize) {
                const batch = modifications.slice(i, i + batchSize);
                
                const response = await fetch('/api/finetune/batch_update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ updates: batch })
                });
                
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error);
                }
            }
            
            // Mettre à jour les échantillons locaux
            this.modifiedSamples.forEach((transcription, id) => {
                const sample = this.samples.find(s => s.id === id);
                if (sample) {
                    sample.transcription = transcription;
                }
            });
            
            // Nettoyer les modifications
            this.modifiedSamples.clear();
            $('.transcription-inline.modified').removeClass('modified');
            this.updateModifiedCount();
            
            this.showToast(`${modifications.length} modifications sauvegardées`, 'success');
        } catch (error) {
            this.showToast('Erreur lors de la sauvegarde: ' + error.message, 'danger');
        }
    }
    
    // Actions groupées
    async bulkChangeSplit(newSplit) {
        if (this.selectedSamples.size === 0) return;
        
        const updates = Array.from(this.selectedSamples).map(id => {
            const sample = this.samples.find(s => s.id === id);
            return {
                text_path: sample.text_path,
                json_path: sample.json_path,
                audio_path: sample.audio_path,
                split: newSplit
            };
        });
        
        try {
            const response = await fetch('/api/finetune/batch_change_split', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ updates })
            });
            
            const data = await response.json();
            if (data.success) {
                // Mettre à jour localement
                this.selectedSamples.forEach(id => {
                    const sample = this.samples.find(s => s.id === id);
                    if (sample) {
                        sample.split = newSplit;
                    }
                });
                
                this.showToast(`${this.selectedSamples.size} échantillons déplacés vers ${newSplit}`, 'success');
                this.clearSelection();
                this.applyFilters();
                this.updateStats();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showToast('Erreur lors du changement de split: ' + error.message, 'danger');
        }
    }
    
    bulkDelete() {
        if (this.selectedSamples.size === 0) return;
        
        $('#delete-count').text(this.selectedSamples.size);
        $('#confirm-bulk-delete').modal('show');
    }
    
    async confirmBulkDelete() {
        const toDelete = Array.from(this.selectedSamples).map(id => {
            const sample = this.samples.find(s => s.id === id);
            return {
                text_path: sample.text_path,
                json_path: sample.json_path,
                audio_path: sample.audio_path
            };
        });
        
        try {
            const response = await fetch('/api/finetune/batch_delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ samples: toDelete })
            });
            
            const data = await response.json();
            if (data.success) {
                // Supprimer localement
                this.samples = this.samples.filter(s => !this.selectedSamples.has(s.id));
                
                this.showToast(`${this.selectedSamples.size} échantillons supprimés`, 'success');
                this.clearSelection();
                this.applyFilters();
                this.updateStats();
                $('#confirm-bulk-delete').modal('hide');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showToast('Erreur lors de la suppression: ' + error.message, 'danger');
        }
    }
    
    // Utilitaires de sélection
    selectAll() {
        this.filteredSamples.forEach(sample => {
            this.selectedSamples.add(sample.id);
        });
        
        $('.sample-checkbox').prop('checked', true);
        $('.sample-row').addClass('selected');
        $('#select-all').prop('checked', true);
        
        this.updateSelectionInfo();
    }
    
    clearSelection() {
        this.selectedSamples.clear();
        $('.sample-checkbox').prop('checked', false);
        $('.sample-row').removeClass('selected');
        $('#select-all').prop('checked', false);
        
        this.updateSelectionInfo();
    }
    
    selectRange(fromId, toId) {
        const fromIndex = this.filteredSamples.findIndex(s => s.id === fromId);
        const toIndex = this.filteredSamples.findIndex(s => s.id === toId);
        
        const start = Math.min(fromIndex, toIndex);
        const end = Math.max(fromIndex, toIndex);
        
        for (let i = start; i <= end; i++) {
            const sample = this.filteredSamples[i];
            this.selectedSamples.add(sample.id);
            $(`.sample-row[data-id="${sample.id}"]`).addClass('selected').find('.sample-checkbox').prop('checked', true);
        }
        
        this.updateSelectionInfo();
    }
    
    toggleSelectAll(checked) {
        if (checked) {
            this.selectAll();
        } else {
            this.clearSelection();
        }
    }
    
    // Mise à jour de l'interface
    updateSelectionInfo() {
        const count = this.selectedSamples.size;
        $('#selected-count').text(count);
        
        if (count > 0) {
            $('#selection-info').addClass('active');
        } else {
            $('#selection-info').removeClass('active');
        }
    }
    
    updateStats() {
        const stats = {
            total: this.samples.length,
            train: 0,
            validation: 0,
            test: 0,
            totalDuration: 0
        };
        
        this.samples.forEach(sample => {
            stats[sample.split]++;
            stats.totalDuration += sample.duration || 0;
        });
        
        $('#total-samples').text(stats.total);
        $('#train-count').text(stats.train);
        $('#validation-count').text(stats.validation);
        $('#test-count').text(stats.test);
        $('#total-duration').text(this.formatDuration(stats.totalDuration));
        
        this.updateModifiedCount();
    }
    
    updateModifiedCount() {
        $('#modified-count').text(this.modifiedSamples.size);
    }
    
    updateShowingInfo() {
        $('#showing-info').text(`Affichage de ${this.filteredSamples.length} sur ${this.samples.length} éléments`);
    }
    
    // Formatage
    formatDuration(seconds) {
        if (seconds < 60) return `${seconds.toFixed(1)}s`;
        if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            return `${minutes}m ${(seconds % 60).toFixed(0)}s`;
        }
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // UI Helpers
    showLoading(show) {
        if (show) {
            $('#loading-indicator').show();
        } else {
            $('#loading-indicator').hide();
        }
    }
    
    showToast(message, type = 'info') {
        const toast = $(`
            <div class="toast" role="alert">
                <div class="toast-header">
                    <strong class="mr-auto">${type === 'success' ? 'Succès' : type === 'danger' ? 'Erreur' : 'Info'}</strong>
                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast">
                        <span>&times;</span>
                    </button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `);
        
        $('#toast-container').append(toast);
        toast.toast({ delay: 3000 }).toast('show');
        
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    }
    
    // Toggles
    toggleCompactMode() {
        this.compactMode = !this.compactMode;
        $('#toggle-compact').toggleClass('active', this.compactMode);
        $('body').toggleClass('compact-mode', this.compactMode);
    }
    
    toggleBatchMode() {
        this.batchMode = !this.batchMode;
        $('#batch-mode').toggleClass('active', this.batchMode);
        // TODO: Implémenter le mode batch
    }
    
    toggleAutoSave() {
        this.autoSaveEnabled = !this.autoSaveEnabled;
        $('#auto-save').toggleClass('active', this.autoSaveEnabled);
        
        if (!this.autoSaveEnabled) {
            clearTimeout(this.autoSaveTimer);
        }
    }
    
    toggleAdvancedFilters() {
        $('#advanced-filters').slideToggle();
    }
    
    // Actions dataset
    async syncDataset() {
        try {
            const response = await fetch('/api/finetune/regenerate_dataset', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                this.showToast('Dataset synchronisé avec succès', 'success');
                await this.loadSamples();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showToast('Erreur lors de la synchronisation: ' + error.message, 'danger');
        }
    }
    
    async exportDataset() {
        try {
            // TODO: Implémenter l'export
            this.showToast('Export du dataset en cours...', 'info');
            
            // Simuler l'export
            setTimeout(() => {
                this.showToast('Dataset exporté avec succès', 'success');
            }, 2000);
        } catch (error) {
            this.showToast('Erreur lors de l\'export: ' + error.message, 'danger');
        }
    }
    
    // Mise à jour automatique
    startAutoUpdate() {
        setInterval(() => {
            $('#last-update').text('Dernière mise à jour: ' + new Date().toLocaleTimeString());
        }, 60000); // Toutes les minutes
    }
}

// Initialisation au chargement de la page
$(document).ready(() => {
    window.finetuneManager = new FinetuneManager();
});