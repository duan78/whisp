/**
 * Outil de vérification d'accessibilité pour Whisp Assistant
 * Conforme aux normes WCAG 2.1 AA et RGAA 4
 */

class AccessibilityChecker {
    constructor() {
        this.issues = [];
        this.warnings = [];
    }

    /**
     * Exécute toutes les vérifications d'accessibilité
     */
    runAllChecks() {
        this.checkAltText();
        this.checkAriaLabels();
        this.checkHeadingStructure();
        this.checkColorContrast();
        this.checkFocusableElements();
        this.checkFormLabels();
        this.checkLandmarks();
        this.checkSkipLinks();
        this.checkTabIndex();
        this.checkLanguage();
        
        return {
            issues: this.issues,
            warnings: this.warnings,
            summary: this.generateSummary()
        };
    }

    /**
     * Vérifie que toutes les images ont un texte alternatif
     * WCAG 1.1.1 - Contenu non textuel
     */
    checkAltText() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('alt')) {
                this.addIssue('Image sans attribut alt', img, 'WCAG 1.1.1');
            } else if (img.alt === '' && !img.hasAttribute('role') && !img.hasAttribute('aria-hidden')) {
                // Les images décoratives doivent avoir alt="" et role="presentation" ou aria-hidden="true"
                this.addWarning('Image décorative sans role="presentation" ou aria-hidden="true"', img, 'WCAG 1.1.1');
            }
        });
    }

    /**
     * Vérifie que les éléments interactifs ont des labels accessibles
     * WCAG 2.4.4, 4.1.2
     */
    checkAriaLabels() {
        // Vérifier les boutons sans texte
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            if (button.textContent.trim() === '' && 
                !button.hasAttribute('aria-label') && 
                !button.hasAttribute('aria-labelledby')) {
                this.addIssue('Bouton sans texte ni aria-label', button, 'WCAG 4.1.2');
            }
        });

        // Vérifier les liens sans texte
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            if (link.textContent.trim() === '' && 
                !link.hasAttribute('aria-label') && 
                !link.hasAttribute('aria-labelledby') &&
                !link.querySelector('img[alt]')) {
                this.addIssue('Lien sans texte ni aria-label', link, 'WCAG 2.4.4');
            }
        });
    }

    /**
     * Vérifie la structure des titres
     * WCAG 1.3.1, 2.4.6
     */
    checkHeadingStructure() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let lastLevel = 0;
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.substring(1));
            
            // Vérifier si un niveau de titre a été sauté
            if (level - lastLevel > 1 && lastLevel !== 0) {
                this.addWarning(`Saut dans la hiérarchie des titres: de H${lastLevel} à H${level}`, heading, 'WCAG 1.3.1');
            }
            
            // Vérifier si le titre est vide
            if (heading.textContent.trim() === '') {
                this.addIssue('Titre vide', heading, 'WCAG 2.4.6');
            }
            
            lastLevel = level;
        });
        
        // Vérifier s'il y a un H1
        if (!document.querySelector('h1')) {
            this.addIssue('Aucun titre H1 trouvé sur la page', document.body, 'WCAG 1.3.1');
        }
    }

    /**
     * Vérifie le contraste des couleurs (approximatif)
     * WCAG 1.4.3
     * Note: Cette vérification est limitée car elle ne peut pas accéder aux styles calculés
     */
    checkColorContrast() {
        // Cette vérification nécessite une bibliothèque de calcul de contraste
        this.addWarning('Vérification manuelle du contraste des couleurs recommandée', document.body, 'WCAG 1.4.3');
    }

    /**
     * Vérifie que les éléments focalisables sont visibles lors du focus
     * WCAG 2.4.7
     */
    checkFocusableElements() {
        const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        
        // Vérifier si des styles CSS pourraient masquer l'outline
        const styleSheets = document.styleSheets;
        let outlineIssue = false;
        
        try {
            for (let i = 0; i < styleSheets.length; i++) {
                const rules = styleSheets[i].cssRules || styleSheets[i].rules;
                if (!rules) continue; // Feuille de style protégée (CORS)
                
                for (let j = 0; j < rules.length; j++) {
                    const rule = rules[j];
                    if (rule.selectorText && 
                        (rule.selectorText.includes(':focus') && !rule.selectorText.includes(':focus-visible')) && 
                        rule.style.outline === 'none' || rule.style.outline === '0') {
                        outlineIssue = true;
                        break;
                    }
                }
                if (outlineIssue) break;
            }
        } catch (e) {
            // Erreur CORS probable
            this.addWarning('Impossible de vérifier les styles CSS pour les outlines de focus', document.body, 'WCAG 2.4.7');
        }
        
        if (outlineIssue) {
            this.addIssue('Des styles CSS suppriment l\'outline de focus sans alternative', document.body, 'WCAG 2.4.7');
        }
    }

    /**
     * Vérifie que tous les champs de formulaire ont des labels associés
     * WCAG 1.3.1, 3.3.2, 4.1.2
     */
    checkFormLabels() {
        const formControls = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
        
        formControls.forEach(control => {
            const id = control.getAttribute('id');
            let hasLabel = false;
            
            if (id) {
                // Vérifier s'il y a un label associé
                hasLabel = document.querySelector(`label[for="${id}"]`) !== null;
            }
            
            // Vérifier les attributs aria
            const hasAriaLabel = control.hasAttribute('aria-label') && control.getAttribute('aria-label').trim() !== '';
            const hasAriaLabelledBy = control.hasAttribute('aria-labelledby') && control.getAttribute('aria-labelledby').trim() !== '';
            
            if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy) {
                // Exception pour les boutons et les champs de type submit, reset, button
                if (control.tagName !== 'BUTTON' && 
                    !(control.tagName === 'INPUT' && 
                    (control.type === 'submit' || control.type === 'reset' || control.type === 'button'))) {
                    this.addIssue('Champ de formulaire sans label associé', control, 'WCAG 1.3.1, 3.3.2');
                }
            }
        });
    }

    /**
     * Vérifie la présence et l'utilisation correcte des landmarks ARIA
     * WCAG 1.3.1, 2.4.1
     */
    checkLandmarks() {
        // Vérifier la présence des landmarks principaux
        if (!document.querySelector('header, [role="banner"]')) {
            this.addWarning('Aucun landmark header/banner trouvé', document.body, 'WCAG 1.3.1');
        }
        
        if (!document.querySelector('main, [role="main"]')) {
            this.addWarning('Aucun landmark main trouvé', document.body, 'WCAG 1.3.1');
        }
        
        if (!document.querySelector('nav, [role="navigation"]')) {
            this.addWarning('Aucun landmark navigation trouvé', document.body, 'WCAG 1.3.1');
        }
        
        if (!document.querySelector('footer, [role="contentinfo"]')) {
            this.addWarning('Aucun landmark footer/contentinfo trouvé', document.body, 'WCAG 1.3.1');
        }
    }

    /**
     * Vérifie la présence de liens d'évitement
     * WCAG 2.4.1
     */
    checkSkipLinks() {
        // Vérifier s'il y a un lien d'évitement vers le contenu principal
        const skipLinks = Array.from(document.querySelectorAll('a')).filter(a => {
            const href = a.getAttribute('href');
            return href && (href === '#main' || href === '#content' || href === '#main-content');
        });
        
        if (skipLinks.length === 0) {
            this.addWarning('Aucun lien d\'évitement trouvé', document.body, 'WCAG 2.4.1');
        } else {
            // Vérifier si la cible du lien existe
            skipLinks.forEach(link => {
                const targetId = link.getAttribute('href').substring(1);
                if (!document.getElementById(targetId)) {
                    this.addIssue(`La cible du lien d'évitement (${targetId}) n'existe pas`, link, 'WCAG 2.4.1');
                }
            });
        }
    }

    /**
     * Vérifie l'utilisation correcte de tabindex
     * WCAG 2.4.3
     */
    checkTabIndex() {
        const elementsWithTabIndex = document.querySelectorAll('[tabindex]');
        
        elementsWithTabIndex.forEach(el => {
            const tabIndex = parseInt(el.getAttribute('tabindex'));
            if (tabIndex > 0) {
                this.addWarning(`tabindex > 0 (${tabIndex}) peut perturber l'ordre de navigation au clavier`, el, 'WCAG 2.4.3');
            }
        });
    }

    /**
     * Vérifie que la langue de la page est spécifiée
     * WCAG 3.1.1
     */
    checkLanguage() {
        const html = document.querySelector('html');
        if (!html.hasAttribute('lang')) {
            this.addIssue('Attribut lang manquant sur l\'élément html', html, 'WCAG 3.1.1');
        } else if (html.getAttribute('lang') === '') {
            this.addIssue('Attribut lang vide sur l\'élément html', html, 'WCAG 3.1.1');
        }
    }

    /**
     * Ajoute un problème à la liste des problèmes
     */
    addIssue(message, element, wcagReference) {
        this.issues.push({
            message,
            element: this.getElementInfo(element),
            wcagReference
        });
    }

    /**
     * Ajoute un avertissement à la liste des avertissements
     */
    addWarning(message, element, wcagReference) {
        this.warnings.push({
            message,
            element: this.getElementInfo(element),
            wcagReference
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
                    
                    // Ajouter l'index parmi les frères de même type
                    const siblings = Array.from(current.parentNode.children).filter(c => c.tagName === current.tagName);
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(current) + 1;
                        part += `:nth-of-type(${index})`;
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
            outerHTML: element.outerHTML.substring(0, 200) + (element.outerHTML.length > 200 ? '...' : '')
        };
    }

    /**
     * Génère un résumé des problèmes trouvés
     */
    generateSummary() {
        return {
            totalIssues: this.issues.length,
            totalWarnings: this.warnings.length,
            wcagCategories: this.categorizeByWCAG()
        };
    }

    /**
     * Catégorise les problèmes par référence WCAG
     */
    categorizeByWCAG() {
        const categories = {};
        
        // Traiter les problèmes
        this.issues.forEach(issue => {
            const refs = issue.wcagReference.split(',').map(ref => ref.trim());
            refs.forEach(ref => {
                if (!categories[ref]) {
                    categories[ref] = { issues: 0, warnings: 0 };
                }
                categories[ref].issues++;
            });
        });
        
        // Traiter les avertissements
        this.warnings.forEach(warning => {
            const refs = warning.wcagReference.split(',').map(ref => ref.trim());
            refs.forEach(ref => {
                if (!categories[ref]) {
                    categories[ref] = { issues: 0, warnings: 0 };
                }
                categories[ref].warnings++;
            });
        });
        
        return categories;
    }
}

// Exécuter la vérification lorsque la page est complètement chargée
window.addEventListener('load', function() {
    // Attendre un peu pour s'assurer que tous les scripts sont chargés
    setTimeout(() => {
        const checker = new AccessibilityChecker();
        const results = checker.runAllChecks();
        
        // Afficher les résultats dans la console
        console.group('Rapport d\'accessibilité WCAG 2.1 AA / RGAA 4');
        console.log('Résumé:', results.summary);
        
        if (results.issues.length > 0) {
            console.group(`Problèmes (${results.issues.length})`);
            results.issues.forEach((issue, index) => {
                console.log(`${index + 1}. ${issue.message} - ${issue.wcagReference}`);
                console.log('Élément:', issue.element);
            });
            console.groupEnd();
        } else {
            console.log('✅ Aucun problème d\'accessibilité détecté');
        }
        
        if (results.warnings.length > 0) {
            console.group(`Avertissements (${results.warnings.length})`);
            results.warnings.forEach((warning, index) => {
                console.log(`${index + 1}. ${warning.message} - ${warning.wcagReference}`);
                console.log('Élément:', warning.element);
            });
            console.groupEnd();
        } else {
            console.log('✅ Aucun avertissement d\'accessibilité détecté');
        }
        
        console.groupEnd();
    }, 1000);
});
