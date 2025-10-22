/**
 * Module de gestion par lots pour l'interface finetune
 * Ajoute les fonctionnalités de sélection multiple et actions groupées
 */

(function() {
    'use strict';

    // État global pour la sélection multiple
    const batchState = {
        multiSelectMode: false,
        selectedSamples: new Set(),
        modifiedSamples: new Map(),
        lastSelectedIndex: -1,
        shiftKeyPressed: false
    };

    // Cache des éléments DOM fréquemment utilisés
    const domCache = {
        bulkBar: null,
        selectedCount: null,
        selectAllCheckbox: null,
        samplesContainer: null
    };

    /**
     * Initialise le module de traitement par lots
     */
    function initBatchModule() {
        cacheDOMElements();
        setupEventListeners();
        setupKeyboardShortcuts();
    }

    /**
     * Met en cache les éléments DOM fréquemment utilisés
     */
    function cacheDOMElements() {
        domCache.bulkBar = document.getElementById('bulk-selection-bar');
        domCache.selectedCount = document.getElementById('selected-count');
        domCache.selectAllCheckbox = document.getElementById('select-all-checkbox');
        domCache.samplesContainer = document.getElementById('samples-container');
    }

    /**
     * Configure les écouteurs d'événements
     */
    function setupEventListeners() {
        // Toggle mode sélection multiple
        document.getElementById('enable-multi-select').addEventListener('change', function(e) {
            toggleMultiSelectMode(e.target.checked);
        });

        // Sélectionner tout
        domCache.selectAllCheckbox.addEventListener('change', function(e) {
            selectAll(e.target.checked);
        });

        // Actions groupées
        document.getElementById('bulk-set-train').addEventListener('click', () => bulkChangeSplit('train'));
        document.getElementById('bulk-set-validation').addEventListener('click', () => bulkChangeSplit('validation'));
        document.getElementById('bulk-set-test').addEventListener('click', () => bulkChangeSplit('test'));
        document.getElementById('bulk-save').addEventListener('click', bulkSaveTranscriptions);
        document.getElementById('bulk-delete').addEventListener('click', bulkDeleteSamples);
        document.getElementById('clear-selection').addEventListener('click', clearSelection);

        // Détection du shift pour la multi-sélection
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Shift') batchState.shiftKeyPressed = true;
        });

        document.addEventListener('keyup', (e) => {
            if (e.key === 'Shift') batchState.shiftKeyPressed = false;
        });

        // Observer les changements dans le conteneur des échantillons
        const observer = new MutationObserver(() => {
            if (batchState.multiSelectMode) {
                addCheckboxesToSamples();
            }
        });

        observer.observe(domCache.samplesContainer, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Configure les raccourcis clavier
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ignorer si on est dans un champ de texte
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // M - Toggle mode multi-sélection
            if (e.key === 'm' || e.key === 'M') {
                e.preventDefault();
                const checkbox = document.getElementById('enable-multi-select');
                checkbox.checked = !checkbox.checked;
                toggleMultiSelectMode(checkbox.checked);
            }

            // Ctrl+A - Sélectionner tout
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                if (batchState.multiSelectMode) {
                    selectAll(true);
                }
            }

            // Ctrl+D - Désélectionner tout
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                if (batchState.multiSelectMode) {
                    clearSelection();
                }
            }

            // Ctrl+S - Sauvegarder toutes les modifications
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveAllModifications();
            }

            // Delete - Supprimer la sélection
            if (e.key === 'Delete' && batchState.selectedSamples.size > 0) {
                e.preventDefault();
                bulkDeleteSamples();
            }

            // 1, 2, 3 - Changer le split de la sélection
            if (['1', '2', '3'].includes(e.key) && batchState.selectedSamples.size > 0) {
                e.preventDefault();
                const splits = {'1': 'train', '2': 'validation', '3': 'test'};
                bulkChangeSplit(splits[e.key]);
            }

            // T - Vue tableau
            if (e.key === 't' || e.key === 'T') {
                e.preventDefault();
                document.getElementById('table-view-btn').click();
            }
        });
    }

    /**
     * Active/désactive le mode sélection multiple
     */
    function toggleMultiSelectMode(enabled) {
        batchState.multiSelectMode = enabled;
        document.body.classList.toggle('multi-select-mode', enabled);

        if (enabled) {
            addCheckboxesToSamples();
            showNotification('Mode sélection multiple activé', 'info');
        } else {
            removeCheckboxesFromSamples();
            clearSelection();
            domCache.bulkBar.style.display = 'none';
            showNotification('Mode sélection multiple désactivé', 'info');
        }
    }

    /**
     * Ajoute les checkboxes aux échantillons
     */
    function addCheckboxesToSamples() {
        const cards = document.querySelectorAll('.sample-card');
        
        cards.forEach((card, index) => {
            // Vérifier si la checkbox existe déjà
            if (card.querySelector('.selection-checkbox')) return;

            const sampleId = card.id.replace('sample-', '');
            
            // Créer la checkbox
            const checkboxContainer = document.createElement('div');
            checkboxContainer.className = 'selection-checkbox';
            checkboxContainer.innerHTML = `
                <label class="custom-checkbox">
                    <input type="checkbox" data-sample-id="${sampleId}" data-index="${index}">
                    <span class="checkmark"></span>
                </label>
            `;

            // Ajouter la checkbox à la carte
            card.insertBefore(checkboxContainer, card.firstChild);
            card.classList.add('selectable');

            // Événements de sélection
            const checkbox = checkboxContainer.querySelector('input');
            checkbox.addEventListener('change', function() {
                handleSampleSelection(sampleId, this.checked, index);
            });

            // Click sur la carte pour sélectionner
            card.addEventListener('click', function(e) {
                // Ignorer si on clique sur un contrôle
                if (e.target.closest('button, audio, textarea, input:not([type="checkbox"])')) {
                    return;
                }
                
                e.preventDefault();
                
                if (batchState.shiftKeyPressed && batchState.lastSelectedIndex !== -1) {
                    // Sélection par plage avec Shift
                    selectRange(batchState.lastSelectedIndex, index);
                } else {
                    // Sélection simple
                    checkbox.checked = !checkbox.checked;
                    handleSampleSelection(sampleId, checkbox.checked, index);
                }
            });
        });
    }

    /**
     * Retire les checkboxes des échantillons
     */
    function removeCheckboxesFromSamples() {
        document.querySelectorAll('.selection-checkbox').forEach(el => el.remove());
        document.querySelectorAll('.sample-card').forEach(card => {
            card.classList.remove('selectable', 'selected');
        });
    }

    /**
     * Gère la sélection d'un échantillon
     */
    function handleSampleSelection(sampleId, isSelected, index) {
        const card = document.getElementById(`sample-${sampleId}`);
        
        if (isSelected) {
            batchState.selectedSamples.add(sampleId);
            card.classList.add('selected');
        } else {
            batchState.selectedSamples.delete(sampleId);
            card.classList.remove('selected');
        }

        batchState.lastSelectedIndex = index;
        updateSelectionUI();
    }

    /**
     * Sélectionne une plage d'échantillons
     */
    function selectRange(startIndex, endIndex) {
        const cards = document.querySelectorAll('.sample-card');
        const start = Math.min(startIndex, endIndex);
        const end = Math.max(startIndex, endIndex);

        for (let i = start; i <= end; i++) {
            const card = cards[i];
            if (card) {
                const checkbox = card.querySelector('.selection-checkbox input');
                if (checkbox && !checkbox.checked) {
                    checkbox.checked = true;
                    const sampleId = checkbox.getAttribute('data-sample-id');
                    handleSampleSelection(sampleId, true, i);
                }
            }
        }
    }

    /**
     * Sélectionne ou désélectionne tout
     */
    function selectAll(select) {
        const checkboxes = document.querySelectorAll('.selection-checkbox input');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = select;
            const sampleId = checkbox.getAttribute('data-sample-id');
            const index = parseInt(checkbox.getAttribute('data-index'));
            handleSampleSelection(sampleId, select, index);
        });
    }

    /**
     * Efface toute la sélection
     */
    function clearSelection() {
        selectAll(false);
        domCache.selectAllCheckbox.checked = false;
    }

    /**
     * Met à jour l'interface de sélection
     */
    function updateSelectionUI() {
        const count = batchState.selectedSamples.size;
        domCache.selectedCount.textContent = count;

        if (count > 0) {
            domCache.bulkBar.style.display = 'flex';
        } else {
            domCache.bulkBar.style.display = 'none';
        }

        // Mettre à jour l'état de "select all"
        const totalCheckboxes = document.querySelectorAll('.selection-checkbox input').length;
        domCache.selectAllCheckbox.checked = count === totalCheckboxes && count > 0;
        domCache.selectAllCheckbox.indeterminate = count > 0 && count < totalCheckboxes;
    }

    /**
     * Change le split de tous les échantillons sélectionnés
     */
    async function bulkChangeSplit(newSplit) {
        if (batchState.selectedSamples.size === 0) return;

        const samples = Array.from(batchState.selectedSamples).map(id => {
            const sample = window.allSamples.find(s => s.id === id);
            return {
                audio_path: sample.audio_path,
                text_path: sample.text_path,
                json_path: sample.json_path,
                split: newSplit
            };
        });

        try {
            const response = await fetch('/api/finetune/batch_change_split', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ updates: samples })
            });

            const data = await response.json();
            if (data.success) {
                showNotification(`${samples.length} échantillons déplacés vers ${newSplit}`, 'success');
                
                // Mettre à jour localement
                batchState.selectedSamples.forEach(id => {
                    const sample = window.allSamples.find(s => s.id === id);
                    if (sample) sample.split = newSplit;
                });

                // Rafraîchir l'affichage
                window.displaySamples();
                clearSelection();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification('Erreur: ' + error.message, 'danger');
        }
    }

    /**
     * Sauvegarde toutes les transcriptions modifiées
     */
    async function bulkSaveTranscriptions() {
        const modifiedTextareas = document.querySelectorAll('.transcription-textarea.modified');
        if (modifiedTextareas.length === 0) {
            showNotification('Aucune modification à sauvegarder', 'info');
            return;
        }

        const updates = [];
        modifiedTextareas.forEach(textarea => {
            const sampleId = textarea.getAttribute('data-sample-id');
            if (!batchState.selectedSamples.has(sampleId)) return;

            updates.push({
                text_path: textarea.getAttribute('data-text-path'),
                json_path: textarea.getAttribute('data-json-path'),
                transcription: textarea.value.trim()
            });
        });

        if (updates.length === 0) {
            showNotification('Aucune modification dans la sélection', 'info');
            return;
        }

        try {
            const response = await fetch('/api/finetune/batch_update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ updates })
            });

            const data = await response.json();
            if (data.success) {
                showNotification(`${updates.length} transcriptions sauvegardées`, 'success');
                
                // Mettre à jour l'interface
                updates.forEach(update => {
                    const textarea = document.querySelector(`.transcription-textarea[data-text-path="${update.text_path}"]`);
                    if (textarea) {
                        textarea.classList.remove('modified');
                        textarea.setAttribute('data-original', update.transcription);
                    }
                });

                window.modifiedSamples.clear();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification('Erreur: ' + error.message, 'danger');
        }
    }

    /**
     * Supprime tous les échantillons sélectionnés
     */
    async function bulkDeleteSamples() {
        if (batchState.selectedSamples.size === 0) return;

        if (!confirm(`Êtes-vous sûr de vouloir supprimer ${batchState.selectedSamples.size} échantillons ?`)) {
            return;
        }

        const samples = Array.from(batchState.selectedSamples).map(id => {
            const sample = window.allSamples.find(s => s.id === id);
            return {
                audio_path: sample.audio_path,
                text_path: sample.text_path,
                json_path: sample.json_path
            };
        });

        try {
            const response = await fetch('/api/finetune/batch_delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ samples })
            });

            const data = await response.json();
            if (data.success) {
                showNotification(`${samples.length} échantillons supprimés`, 'success');
                
                // Retirer du tableau global
                window.allSamples = window.allSamples.filter(s => !batchState.selectedSamples.has(s.id));
                window.filteredSamples = window.filteredSamples.filter(s => !batchState.selectedSamples.has(s.id));
                
                // Rafraîchir l'affichage
                window.displaySamples();
                clearSelection();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification('Erreur: ' + error.message, 'danger');
        }
    }

    /**
     * Sauvegarde toutes les modifications (raccourci Ctrl+S)
     */
    async function saveAllModifications() {
        const modifiedTextareas = document.querySelectorAll('.transcription-textarea.modified');
        if (modifiedTextareas.length === 0) {
            showNotification('Aucune modification à sauvegarder', 'info');
            return;
        }

        const updates = [];
        modifiedTextareas.forEach(textarea => {
            updates.push({
                text_path: textarea.getAttribute('data-text-path'),
                json_path: textarea.getAttribute('data-json-path'),
                transcription: textarea.value.trim()
            });
        });

        // Sauvegarder par lots de 10
        const batchSize = 10;
        let saved = 0;

        for (let i = 0; i < updates.length; i += batchSize) {
            const batch = updates.slice(i, i + batchSize);
            
            try {
                const response = await fetch('/api/finetune/batch_update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ updates: batch })
                });

                const data = await response.json();
                if (data.success) {
                    saved += batch.length;
                    
                    // Mettre à jour l'interface
                    batch.forEach(update => {
                        const textarea = document.querySelector(`.transcription-textarea[data-text-path="${update.text_path}"]`);
                        if (textarea) {
                            textarea.classList.remove('modified');
                            textarea.setAttribute('data-original', update.transcription);
                            
                            // Mettre à jour le tableau global
                            const sampleId = textarea.getAttribute('data-sample-id');
                            const sample = window.allSamples.find(s => s.id === sampleId);
                            if (sample) {
                                sample.transcription = update.transcription;
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Erreur batch:', error);
            }
        }

        showNotification(`${saved} transcriptions sauvegardées`, 'success');
        window.modifiedSamples.clear();
    }

    /**
     * Affiche une notification
     */
    function showNotification(message, type = 'info') {
        // Utiliser la fonction existante si disponible
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // Fallback basique
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} notification-toast`;
            alert.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 350px;';
            alert.innerHTML = `
                <span>${message}</span>
                <button type="button" class="close" onclick="this.parentElement.remove()">×</button>
            `;
            document.body.appendChild(alert);
            setTimeout(() => alert.remove(), 3000);
        }
    }

    // Initialiser le module quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBatchModule);
    } else {
        initBatchModule();
    }

    // Exposer certaines fonctions pour l'utilisation externe
    window.batchModule = {
        toggleMultiSelectMode,
        selectAll,
        clearSelection,
        saveAllModifications
    };

})();