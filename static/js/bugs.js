// Script pour la page des bugs
document.addEventListener('DOMContentLoaded', function() {
    // Gestion du formulaire de rapport de bug
    const bugReportForm = document.getElementById('bug-report-form');
    const bugReportStatus = document.getElementById('bug-report-status');
    
    if (bugReportForm) {
        bugReportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Récupérer les données du formulaire
            const formData = {
                title: document.getElementById('bug-title').value,
                description: document.getElementById('bug-description').value,
                steps: document.getElementById('bug-steps').value,
                category: document.getElementById('bug-category').value,
                priority: document.getElementById('bug-priority').value
            };
            
            // Envoyer le rapport à l'API
            bugReportStatus.textContent = "Envoi du rapport en cours...";
            bugReportStatus.className = "";
            bugReportStatus.classList.add('success');
            bugReportStatus.style.display = 'block';
            
            fetch('/api/bug_tickets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    bugReportStatus.textContent = "Rapport de bug envoyé avec succès ! Merci pour votre contribution.";
                    bugReportStatus.className = "";
                    bugReportStatus.classList.add('success');
                    
                    // Réinitialiser le formulaire
                    bugReportForm.reset();
                    
                    // Ajouter le nouveau ticket à la liste
                    addTicketToList(data.ticket);
                    
                    // Masquer le message après 5 secondes
                    setTimeout(function() {
                        bugReportStatus.style.display = 'none';
                    }, 5000);
                } else {
                    bugReportStatus.textContent = "Erreur lors de l'envoi du rapport: " + data.error;
                    bugReportStatus.className = "";
                    bugReportStatus.classList.add('error');
                }
            })
            .catch(error => {
                bugReportStatus.textContent = "Erreur lors de l'envoi du rapport: " + error.message;
                bugReportStatus.className = "";
                bugReportStatus.classList.add('error');
            });
        });
    }
    
    // Animation pour les éléments de bug au survol
    const bugItems = document.querySelectorAll('.bug-item');
    bugItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px)';
            this.style.boxShadow = 'var(--shadow)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });
    
    // Fonction pour afficher/masquer les détails des bugs
    const bugDetails = document.querySelectorAll('.bug-details');
    bugDetails.forEach(detail => {
        // Ajouter un bouton pour afficher/masquer les détails
        const toggleButton = document.createElement('button');
        toggleButton.className = 'toggle-details';
        toggleButton.innerHTML = '<i class="fas fa-chevron-down"></i> Voir les détails';
        toggleButton.style.background = 'none';
        toggleButton.style.border = 'none';
        toggleButton.style.color = 'var(--primary-color)';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.padding = '4px 8px';
        toggleButton.style.marginTop = '8px';
        toggleButton.style.borderRadius = '4px';
        toggleButton.style.fontSize = '0.9rem';
        
        // Insérer le bouton avant les détails
        detail.parentNode.insertBefore(toggleButton, detail);
        
        // Masquer les détails par défaut
        detail.style.display = 'none';
        
        // Ajouter l'événement de clic
        toggleButton.addEventListener('click', function() {
            if (detail.style.display === 'none') {
                detail.style.display = 'block';
                this.innerHTML = '<i class="fas fa-chevron-up"></i> Masquer les détails';
            } else {
                detail.style.display = 'none';
                this.innerHTML = '<i class="fas fa-chevron-down"></i> Voir les détails';
            }
        });
    });
    
    // Gestion des tickets de bugs
    const ticketsList = document.getElementById('tickets-list');
    const ticketDetailModal = document.getElementById('ticket-detail-modal');
    const editTicketModal = document.getElementById('edit-ticket-modal');
    const newTicketBtn = document.getElementById('new-ticket-btn');
    
    // Filtres pour les tickets
    const statusFilter = document.getElementById('ticket-status-filter');
    const categoryFilter = document.getElementById('ticket-category-filter');
    const priorityFilter = document.getElementById('ticket-priority-filter');
    
    // Appliquer les filtres
    function applyFilters() {
        const status = statusFilter.value;
        const category = categoryFilter.value;
        const priority = priorityFilter.value;
        
        const tickets = document.querySelectorAll('.ticket-item');
        tickets.forEach(ticket => {
            let visible = true;
            
            if (status !== 'all' && ticket.dataset.status !== status) {
                visible = false;
            }
            
            if (category !== 'all' && ticket.dataset.category !== category) {
                visible = false;
            }
            
            if (priority !== 'all' && ticket.dataset.priority !== priority) {
                visible = false;
            }
            
            ticket.style.display = visible ? 'block' : 'none';
        });
    }
    
    // Ajouter les écouteurs d'événements pour les filtres
    if (statusFilter) statusFilter.addEventListener('change', applyFilters);
    if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);
    if (priorityFilter) priorityFilter.addEventListener('change', applyFilters);
    
    // Fonction pour ajouter un ticket à la liste
    function addTicketToList(ticket) {
        // Vérifier si la liste des tickets existe
        if (!ticketsList) return;
        
        // Vérifier s'il n'y a pas de tickets
        const noTickets = ticketsList.querySelector('.no-tickets');
        if (noTickets) {
            noTickets.remove();
        }
        
        // Créer l'élément de ticket
        const ticketItem = document.createElement('div');
        ticketItem.className = 'ticket-item';
        ticketItem.dataset.id = ticket.id;
        ticketItem.dataset.status = ticket.status;
        ticketItem.dataset.category = ticket.category;
        ticketItem.dataset.priority = ticket.priority;
        
        // Formater la date
        const createdAt = ticket.created_at.replace('T', ' ').substring(0, 16);
        
        ticketItem.innerHTML = `
            <div class="ticket-header">
                <div class="ticket-title">${ticket.title}</div>
                <div class="ticket-meta">
                    <span class="ticket-id">#${ticket.id.substring(0, 8)}</span>
                    <span class="ticket-date">${createdAt}</span>
                </div>
            </div>
            <div class="ticket-content">
                <div class="ticket-description">${ticket.description.length > 150 ? ticket.description.substring(0, 150) + '...' : ticket.description}</div>
                <div class="ticket-badges">
                    <span class="status-badge ${ticket.status}">${ticket.status}</span>
                    <span class="status-badge ${ticket.priority}">${ticket.priority}</span>
                    <span class="status-badge category">${ticket.category}</span>
                </div>
            </div>
            <div class="ticket-actions">
                <button class="btn-view-ticket" data-id="${ticket.id}">
                    <i class="fas fa-eye"></i> Voir
                </button>
                <button class="btn-edit-ticket" data-id="${ticket.id}">
                    <i class="fas fa-edit"></i> Modifier
                </button>
            </div>
        `;
        
        // Ajouter le ticket au début de la liste
        ticketsList.insertBefore(ticketItem, ticketsList.firstChild);
        
        // Ajouter les écouteurs d'événements
        const viewBtn = ticketItem.querySelector('.btn-view-ticket');
        const editBtn = ticketItem.querySelector('.btn-edit-ticket');
        
        viewBtn.addEventListener('click', function() {
            openTicketDetail(ticket.id);
        });
        
        editBtn.addEventListener('click', function() {
            openEditTicket(ticket.id);
        });
    }
    
    // Fonction pour ouvrir le modal de détail d'un ticket
    function openTicketDetail(ticketId) {
        fetch(`/api/bug_tickets/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ticket = data.ticket;
                    
                    // Mettre à jour le titre du modal
                    document.getElementById('modal-ticket-title').textContent = ticket.title;
                    
                    // Formater les dates
                    const createdAt = new Date(ticket.created_at).toLocaleString();
                    const updatedAt = new Date(ticket.updated_at).toLocaleString();
                    
                    // Remplir le contenu du ticket
                    const detailContent = document.getElementById('ticket-detail-content');
                    detailContent.innerHTML = `
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">ID</div>
                            <div class="ticket-detail-value">${ticket.id}</div>
                        </div>
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Statut</div>
                            <div class="ticket-detail-value">
                                <span class="status-badge ${ticket.status}">${ticket.status}</span>
                            </div>
                        </div>
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Priorité</div>
                            <div class="ticket-detail-value">
                                <span class="status-badge ${ticket.priority}">${ticket.priority}</span>
                            </div>
                        </div>
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Catégorie</div>
                            <div class="ticket-detail-value">
                                <span class="status-badge category">${ticket.category}</span>
                            </div>
                        </div>
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Description</div>
                            <div class="ticket-detail-value">${ticket.description}</div>
                        </div>
                        ${ticket.steps ? `
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Étapes pour reproduire</div>
                            <div class="ticket-detail-value">${ticket.steps.replace(/\n/g, '<br>')}</div>
                        </div>
                        ` : ''}
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Créé le</div>
                            <div class="ticket-detail-value">${createdAt}</div>
                        </div>
                        <div class="ticket-detail-row">
                            <div class="ticket-detail-label">Mis à jour le</div>
                            <div class="ticket-detail-value">${updatedAt}</div>
                        </div>
                    `;
                    
                    // Remplir les commentaires
                    const commentsContainer = document.getElementById('ticket-comments');
                    commentsContainer.innerHTML = '';
                    
                    if (ticket.comments && ticket.comments.length > 0) {
                        ticket.comments.forEach(comment => {
                            const commentDate = new Date(comment.created_at).toLocaleString();
                            const commentItem = document.createElement('div');
                            commentItem.className = 'comment-item';
                            commentItem.innerHTML = `
                                <div class="comment-header">
                                    <span class="comment-date">${commentDate}</span>
                                </div>
                                <div class="comment-text">${comment.text}</div>
                            `;
                            commentsContainer.appendChild(commentItem);
                        });
                    } else {
                        commentsContainer.innerHTML = '<div class="no-comments">Aucun commentaire pour ce ticket.</div>';
                    }
                    
                    // Configurer le bouton d'ajout de commentaire
                    const addCommentBtn = document.getElementById('add-comment-btn');
                    const newCommentText = document.getElementById('new-comment-text');
                    
                    addCommentBtn.onclick = function() {
                        const commentText = newCommentText.value.trim();
                        if (!commentText) return;
                        
                        fetch(`/api/bug_tickets/${ticketId}/comments`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ text: commentText }),
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Recharger les détails du ticket
                                openTicketDetail(ticketId);
                                // Effacer le champ de texte
                                newCommentText.value = '';
                            } else {
                                alert("Erreur lors de l'ajout du commentaire: " + data.error);
                            }
                        })
                        .catch(error => {
                            alert("Erreur lors de l'ajout du commentaire: " + error.message);
                        });
                    };
                    
                    // Configurer le bouton de suppression
                    const deleteTicketBtn = document.getElementById('delete-ticket-btn');
                    deleteTicketBtn.onclick = function() {
                        if (confirm("Êtes-vous sûr de vouloir supprimer ce ticket ?")) {
                            fetch(`/api/bug_tickets/${ticketId}`, {
                                method: 'DELETE',
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Fermer le modal
                                    ticketDetailModal.style.display = 'none';
                                    // Supprimer le ticket de la liste
                                    const ticketElement = document.querySelector(`.ticket-item[data-id="${ticketId}"]`);
                                    if (ticketElement) {
                                        ticketElement.remove();
                                    }
                                    // Vérifier s'il reste des tickets
                                    const tickets = document.querySelectorAll('.ticket-item');
                                    if (tickets.length === 0) {
                                        ticketsList.innerHTML = `
                                            <div class="no-tickets">
                                                <i class="fas fa-ticket-alt"></i>
                                                <p>Aucun ticket de bug n'a été créé.</p>
                                            </div>
                                        `;
                                    }
                                } else {
                                    alert("Erreur lors de la suppression du ticket: " + data.error);
                                }
                            })
                            .catch(error => {
                                alert("Erreur lors de la suppression du ticket: " + error.message);
                            });
                        }
                    };
                    
                    // Afficher le modal
                    ticketDetailModal.style.display = 'block';
                } else {
                    alert("Erreur lors du chargement du ticket: " + data.error);
                }
            })
            .catch(error => {
                alert("Erreur lors du chargement du ticket: " + error.message);
            });
    }
    
    // Fonction pour ouvrir le modal d'édition d'un ticket
    function openEditTicket(ticketId) {
        fetch(`/api/bug_tickets/${ticketId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const ticket = data.ticket;
                    
                    // Remplir le formulaire d'édition
                    document.getElementById('edit-ticket-id').value = ticket.id;
                    document.getElementById('edit-ticket-title').value = ticket.title;
                    document.getElementById('edit-ticket-description').value = ticket.description;
                    document.getElementById('edit-ticket-steps').value = ticket.steps || '';
                    document.getElementById('edit-ticket-category').value = ticket.category;
                    document.getElementById('edit-ticket-priority').value = ticket.priority;
                    document.getElementById('edit-ticket-status').value = ticket.status;
                    
                    // Afficher le modal
                    editTicketModal.style.display = 'block';
                } else {
                    alert("Erreur lors du chargement du ticket: " + data.error);
                }
            })
            .catch(error => {
                alert("Erreur lors du chargement du ticket: " + error.message);
            });
    }
    
    // Configurer le bouton de sauvegarde du ticket
    const saveTicketBtn = document.getElementById('save-ticket-btn');
    if (saveTicketBtn) {
        saveTicketBtn.addEventListener('click', function() {
            const ticketId = document.getElementById('edit-ticket-id').value;
            
            const formData = {
                title: document.getElementById('edit-ticket-title').value,
                description: document.getElementById('edit-ticket-description').value,
                steps: document.getElementById('edit-ticket-steps').value,
                category: document.getElementById('edit-ticket-category').value,
                priority: document.getElementById('edit-ticket-priority').value,
                status: document.getElementById('edit-ticket-status').value
            };
            
            fetch(`/api/bug_tickets/${ticketId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fermer le modal
                    editTicketModal.style.display = 'none';
                    
                    // Mettre à jour le ticket dans la liste
                    const ticketElement = document.querySelector(`.ticket-item[data-id="${ticketId}"]`);
                    if (ticketElement) {
                        ticketElement.dataset.status = formData.status;
                        ticketElement.dataset.category = formData.category;
                        ticketElement.dataset.priority = formData.priority;
                        
                        const titleElement = ticketElement.querySelector('.ticket-title');
                        const descriptionElement = ticketElement.querySelector('.ticket-description');
                        const statusBadge = ticketElement.querySelector('.status-badge:nth-child(1)');
                        const priorityBadge = ticketElement.querySelector('.status-badge:nth-child(2)');
                        const categoryBadge = ticketElement.querySelector('.status-badge:nth-child(3)');
                        
                        titleElement.textContent = formData.title;
                        descriptionElement.textContent = formData.description.length > 150 ? formData.description.substring(0, 150) + '...' : formData.description;
                        
                        statusBadge.className = `status-badge ${formData.status}`;
                        statusBadge.textContent = formData.status;
                        
                        priorityBadge.className = `status-badge ${formData.priority}`;
                        priorityBadge.textContent = formData.priority;
                        
                        categoryBadge.className = 'status-badge category';
                        categoryBadge.textContent = formData.category;
                    }
                    
                    // Appliquer les filtres
                    applyFilters();
                } else {
                    alert("Erreur lors de la mise à jour du ticket: " + data.error);
                }
            })
            .catch(error => {
                alert("Erreur lors de la mise à jour du ticket: " + error.message);
            });
        });
    }
    
    // Configurer le bouton d'annulation d'édition
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            editTicketModal.style.display = 'none';
        });
    }
    
    // Configurer le bouton de fermeture du modal de détail
    const closeTicketBtn = document.getElementById('close-ticket-btn');
    if (closeTicketBtn) {
        closeTicketBtn.addEventListener('click', function() {
            ticketDetailModal.style.display = 'none';
        });
    }
    
    // Configurer les boutons de fermeture des modals
    const closeButtons = document.querySelectorAll('.close-modal');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            ticketDetailModal.style.display = 'none';
            editTicketModal.style.display = 'none';
        });
    });
    
    // Fermer les modals en cliquant en dehors
    window.addEventListener('click', function(event) {
        if (event.target === ticketDetailModal) {
            ticketDetailModal.style.display = 'none';
        }
        if (event.target === editTicketModal) {
            editTicketModal.style.display = 'none';
        }
    });
    
    // Configurer le bouton pour créer un nouveau ticket
    if (newTicketBtn) {
        newTicketBtn.addEventListener('click', function() {
            // Faire défiler jusqu'au formulaire de rapport de bug
            document.querySelector('.report-bug').scrollIntoView({ behavior: 'smooth' });
        });
    }
    
    // Ajouter des écouteurs d'événements pour les boutons de visualisation et d'édition
    document.querySelectorAll('.btn-view-ticket').forEach(button => {
        button.addEventListener('click', function() {
            openTicketDetail(this.dataset.id);
        });
    });
    
    document.querySelectorAll('.btn-edit-ticket').forEach(button => {
        button.addEventListener('click', function() {
            openEditTicket(this.dataset.id);
        });
    });
});
