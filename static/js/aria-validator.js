/**
 * Validateur ARIA pour Whisp Assistant
 * Vérifie la conformité aux spécifications WAI-ARIA 1.1
 */

class AriaValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        
        // Rôles ARIA valides
        this.validRoles = [
            // Rôles abstraits (ne devraient pas être utilisés directement)
            'command', 'composite', 'input', 'landmark', 'range', 'roletype', 'section', 'sectionhead', 'select', 'structure', 'widget', 'window',
            
            // Rôles de widgets
            'alert', 'alertdialog', 'button', 'checkbox', 'dialog', 'gridcell', 'link', 'log', 'marquee', 'menuitem', 'menuitemcheckbox', 
            'menuitemradio', 'option', 'progressbar', 'radio', 'scrollbar', 'searchbox', 'slider', 'spinbutton', 'status', 'switch', 
            'tab', 'tabpanel', 'textbox', 'timer', 'tooltip', 'treeitem',
            
            // Rôles composites
            'combobox', 'grid', 'listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'tree', 'treegrid',
            
            // Rôles de document
            'application', 'article', 'cell', 'columnheader', 'definition', 'directory', 'document', 'feed', 'figure', 'group', 'heading', 
            'img', 'list', 'listitem', 'math', 'none', 'note', 'presentation', 'row', 'rowgroup', 'rowheader', 'separator', 'table', 'term', 'toolbar',
            
            // Rôles de repères (landmarks)
            'banner', 'complementary', 'contentinfo', 'form', 'main', 'navigation', 'region', 'search'
        ];
        
        // Attributs ARIA valides
        this.validAttributes = [
            'aria-activedescendant', 'aria-atomic', 'aria-autocomplete', 'aria-busy', 'aria-checked', 'aria-colcount', 'aria-colindex', 
            'aria-colspan', 'aria-controls', 'aria-current', 'aria-describedby', 'aria-details', 'aria-disabled', 'aria-dropeffect', 
            'aria-errormessage', 'aria-expanded', 'aria-flowto', 'aria-grabbed', 'aria-haspopup', 'aria-hidden', 'aria-invalid', 
            'aria-keyshortcuts', 'aria-label', 'aria-labelledby', 'aria-level', 'aria-live', 'aria-modal', 'aria-multiline', 
            'aria-multiselectable', 'aria-orientation', 'aria-owns', 'aria-placeholder', 'aria-posinset', 'aria-pressed', 'aria-readonly', 
            'aria-relevant', 'aria-required', 'aria-roledescription', 'aria-rowcount', 'aria-rowindex', 'aria-rowspan', 'aria-selected', 
            'aria-setsize', 'aria-sort', 'aria-valuemax', 'aria-valuemin', 'aria-valuenow', 'aria-valuetext'
        ];
        
        // Attributs requis pour certains rôles
        this.requiredAttributes = {
            'checkbox': ['aria-checked'],
            'combobox': ['aria-expanded'],
            'gridcell': ['aria-selected'],
            'listbox': ['aria-multiselectable'],
            'option': ['aria-selected'],
            'radio': ['aria-checked'],
            'scrollbar': ['aria-controls', 'aria-orientation', 'aria-valuemax', 'aria-valuemin', 'aria-valuenow'],
            'slider': ['aria-valuemax', 'aria-valuemin', 'aria-valuenow'],
            'spinbutton': ['aria-valuemax', 'aria-valuemin', 'aria-valuenow'],
            'switch': ['aria-checked'],
            'tab': ['aria-selected'],
            'textbox': ['aria-multiline']
        };
        
        // Rôles qui ne devraient pas être utilisés sur certains éléments
        this.invalidRoleCombinations = {
            'a': ['button', 'checkbox', 'radio', 'textbox', 'switch'],
            'button': ['link', 'menuitem', 'tab'],
            'input': ['button', 'link'],
            'select': ['button', 'link', 'listbox'],
            'textarea': ['button', 'link', 'textbox']
        };
    }
    
    /**
     * Exécute toutes les validations ARIA
     */
    validateAll() {
        this.validateRoles();
        this.validateAttributes();
        this.validateLabelledBy();
        this.validateDescribedBy();
        this.validateLiveRegions();
        this.validateHiddenElements();
        
        return {
            errors: this.errors,
            warnings: this.warnings,
            summary: this.generateSummary()
        };
    }
    
    /**
     * Valide les rôles ARIA utilisés dans le document
     */
    validateRoles() {
        const elementsWithRole = document.querySelectorAll('[role]');
        
        elementsWithRole.forEach(element => {
            const role = element.getAttribute('role');
            
            // Vérifier si le rôle est valide
            if (!this.validRoles.includes(role)) {
                this.addError(`Rôle ARIA invalide: "${role}"`, element);
            }
            
            // Vérifier les combinaisons invalides
            const tagName = element.tagName.toLowerCase();
            if (this.invalidRoleCombinations[tagName] && this.invalidRoleCombinations[tagName].includes(role)) {
                this.addWarning(`Le rôle "${role}" n'est généralement pas recommandé sur un élément <${tagName}>`, element);
            }
            
            // Vérifier les attributs requis pour ce rôle
            if (this.requiredAttributes[role]) {
                this.requiredAttributes[role].forEach(attr => {
                    if (!element.hasAttribute(attr)) {
                        this.addError(`L'attribut "${attr}" est requis pour le rôle "${role}"`, element);
                    }
                });
            }
            
            // Vérifier les rôles redondants
            if ((tagName === 'button' && role === 'button') ||
                (tagName === 'a' && role === 'link' && element.hasAttribute('href')) ||
                (tagName === 'input' && element.type === 'checkbox' && role === 'checkbox') ||
                (tagName === 'input' && element.type === 'radio' && role === 'radio') ||
                (tagName === 'input' && (element.type === 'text' || element.type === 'email' || element.type === 'password') && role === 'textbox')) {
                this.addWarning(`Rôle redondant: "${role}" sur un élément <${tagName}>`, element);
            }
        });
    }
    
    /**
     * Valide les attributs ARIA utilisés dans le document
     */
    validateAttributes() {
        // Trouver tous les attributs commençant par "aria-"
        const allElements = document.querySelectorAll('*');
        
        allElements.forEach(element => {
            const attributes = element.attributes;
            
            for (let i = 0; i < attributes.length; i++) {
                const attr = attributes[i];
                
                if (attr.name.startsWith('aria-')) {
                    // Vérifier si l'attribut est valide
                    if (!this.validAttributes.includes(attr.name)) {
                        this.addError(`Attribut ARIA invalide: "${attr.name}"`, element);
                    }
                    
                    // Vérifier les valeurs pour certains attributs
                    if (attr.name === 'aria-hidden' && attr.value !== 'true' && attr.value !== 'false') {
                        this.addError(`Valeur invalide pour aria-hidden: "${attr.value}" (doit être "true" ou "false")`, element);
                    }
                    
                    if (attr.name === 'aria-checked' && attr.value !== 'true' && attr.value !== 'false' && attr.value !== 'mixed') {
                        this.addError(`Valeur invalide pour aria-checked: "${attr.value}" (doit être "true", "false" ou "mixed")`, element);
                    }
                    
                    if (attr.name === 'aria-expanded' && attr.value !== 'true' && attr.value !== 'false') {
                        this.addError(`Valeur invalide pour aria-expanded: "${attr.value}" (doit être "true" ou "false")`, element);
                    }
                    
                    if (attr.name === 'aria-live' && attr.value !== 'off' && attr.value !== 'polite' && attr.value !== 'assertive') {
                        this.addError(`Valeur invalide pour aria-live: "${attr.value}" (doit être "off", "polite" ou "assertive")`, element);
                    }
                }
            }
        });
    }
    
    /**
     * Valide les références aria-labelledby
     */
    validateLabelledBy() {
        const elementsWithLabelledBy = document.querySelectorAll('[aria-labelledby]');
        
        elementsWithLabelledBy.forEach(element => {
            const ids = element.getAttribute('aria-labelledby').split(/\s+/);
            
            ids.forEach(id => {
                if (id.trim() === '') return;
                
                const labelElement = document.getElementById(id);
                if (!labelElement) {
                    this.addError(`L'élément référencé par aria-labelledby avec l'ID "${id}" n'existe pas`, element);
                } else if (labelElement.textContent.trim() === '') {
                    this.addWarning(`L'élément référencé par aria-labelledby avec l'ID "${id}" a un contenu vide`, element);
                }
            });
        });
    }
    
    /**
     * Valide les références aria-describedby
     */
    validateDescribedBy() {
        const elementsWithDescribedBy = document.querySelectorAll('[aria-describedby]');
        
        elementsWithDescribedBy.forEach(element => {
            const ids = element.getAttribute('aria-describedby').split(/\s+/);
            
            ids.forEach(id => {
                if (id.trim() === '') return;
                
                const descElement = document.getElementById(id);
                if (!descElement) {
                    this.addError(`L'élément référencé par aria-describedby avec l'ID "${id}" n'existe pas`, element);
                } else if (descElement.textContent.trim() === '') {
                    this.addWarning(`L'élément référencé par aria-describedby avec l'ID "${id}" a un contenu vide`, element);
                }
            });
        });
    }
    
    /**
     * Valide les régions live
     */
    validateLiveRegions() {
        const liveRegions = document.querySelectorAll('[aria-live]');
        
        liveRegions.forEach(region => {
            const liveValue = region.getAttribute('aria-live');
            
            // Vérifier si aria-atomic est défini
            if (!region.hasAttribute('aria-atomic')) {
                this.addWarning(`Région live sans attribut aria-atomic`, region);
            }
            
            // Vérifier si aria-relevant est défini pour les régions assertives
            if (liveValue === 'assertive' && !region.hasAttribute('aria-relevant')) {
                this.addWarning(`Région live assertive sans attribut aria-relevant`, region);
            }
        });
    }
    
    /**
     * Valide les éléments cachés
     */
    validateHiddenElements() {
        const hiddenElements = document.querySelectorAll('[aria-hidden="true"]');
        
        hiddenElements.forEach(element => {
            // Vérifier si des éléments focalisables sont à l'intérieur
            const focusableElements = element.querySelectorAll('a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])');
            
            if (focusableElements.length > 0) {
                this.addError(`Éléments focalisables trouvés à l'intérieur d'un élément avec aria-hidden="true"`, element);
            }
            
            // Vérifier si des rôles landmarks sont à l'intérieur
            const landmarks = element.querySelectorAll('[role="banner"], [role="complementary"], [role="contentinfo"], [role="form"], [role="main"], [role="navigation"], [role="region"], [role="search"]');
            
            if (landmarks.length > 0) {
                this.addError(`Landmarks ARIA trouvés à l'intérieur d'un élément avec aria-hidden="true"`, element);
            }
        });
    }
    
    /**
     * Ajoute une erreur à la liste
     */
    addError(message, element) {
        this.errors.push({
            message,
            element: this.getElementInfo(element)
        });
    }
    
    /**
     * Ajoute un avertissement à la liste
     */
    addWarning(message, element) {
        this.warnings.push({
            message,
            element: this.getElementInfo(element)
        });
    }
    
    /**
     * Récupère des informations sur un élément pour le rapport
     */
    getElementInfo(element) {
        let selector = '';
        
        try {
            // Essayer de créer un sélecteur CSS pour l'élément
            if (element.id) {
                selector = `#${element.id}`;
            } else if (element.className && typeof element.className === 'string') {
                selector = `.${element.className.split(' ')[0]}`;
            } else {
                // Créer un sélecteur basé sur la hiérarchie
                let current = element;
                let parts = [];
                
                while (current && current !== document.body) {
                    let part = current.tagName.toLowerCase();
                    
                    if (current.id) {
                        part += `#${current.id}`;
                        parts.unshift(part);
                        break;
                    } else if (current.className && typeof current.className === 'string') {
                        part += `.${current.className.split(' ')[0]}`;
                    }
                    
                    parts.unshift(part);
                    current = current.parentNode;
                    
                    // Limiter la profondeur du sélecteur
                    if (parts.length > 3) break;
                }
                
                selector = parts.join(' > ');
            }
        } catch (e) {
            selector = element.tagName.toLowerCase();
        }
        
        return {
            tagName: element.tagName.toLowerCase(),
            selector,
            attributes: this.getElementAttributes(element),
            outerHTML: element.outerHTML.substring(0, 200) + (element.outerHTML.length > 200 ? '...' : '')
        };
    }
    
    /**
     * Récupère les attributs d'un élément
     */
    getElementAttributes(element) {
        const attributes = {};
        
        for (let i = 0; i < element.attributes.length; i++) {
            const attr = element.attributes[i];
            attributes[attr.name] = attr.value;
        }
        
        return attributes;
    }
    
    /**
     * Génère un résumé des problèmes trouvés
     */
    generateSummary() {
        return {
            totalErrors: this.errors.length,
            totalWarnings: this.warnings.length,
            ariaRolesUsed: this.countAriaRoles(),
            ariaAttributesUsed: this.countAriaAttributes()
        };
    }
    
    /**
     * Compte les rôles ARIA utilisés
     */
    countAriaRoles() {
        const roles = {};
        const elementsWithRole = document.querySelectorAll('[role]');
        
        elementsWithRole.forEach(element => {
            const role = element.getAttribute('role');
            roles[role] = (roles[role] || 0) + 1;
        });
        
        return roles;
    }
    
    /**
     * Compte les attributs ARIA utilisés
     */
    countAriaAttributes() {
        const attributes = {};
        const allElements = document.querySelectorAll('*');
        
        allElements.forEach(element => {
            for (let i = 0; i < element.attributes.length; i++) {
                const attr = element.attributes[i];
                if (attr.name.startsWith('aria-')) {
                    attributes[attr.name] = (attributes[attr.name] || 0) + 1;
                }
            }
        });
        
        return attributes;
    }
}

// Exécuter la validation lorsque la page est complètement chargée
window.addEventListener('load', function() {
    // Attendre un peu pour s'assurer que tous les scripts sont chargés
    setTimeout(() => {
        const validator = new AriaValidator();
        const results = validator.validateAll();
        
        // Afficher les résultats dans la console
        console.group('Rapport de validation ARIA');
        console.log('Résumé:', results.summary);
        
        if (results.errors.length > 0) {
            console.group(`Erreurs (${results.errors.length})`);
            results.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error.message}`);
                console.log('Élément:', error.element);
            });
            console.groupEnd();
        } else {
            console.log('✅ Aucune erreur ARIA détectée');
        }
        
        if (results.warnings.length > 0) {
            console.group(`Avertissements (${results.warnings.length})`);
            results.warnings.forEach((warning, index) => {
                console.log(`${index + 1}. ${warning.message}`);
                console.log('Élément:', warning.element);
            });
            console.groupEnd();
        } else {
            console.log('✅ Aucun avertissement ARIA détecté');
        }
        
        console.groupEnd();
    }, 1500);
});
