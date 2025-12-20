document.addEventListener('DOMContentLoaded', function () {
    const chatWidgetContainer = document.getElementById('chat-widget-container');
    if (!chatWidgetContainer) return;

    // Elementi
    const toggleButton = document.getElementById('chat-toggle-button');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('close-chat-btn');
    const backBtn = document.getElementById('chat-back-btn');
    const messagesDiv = document.getElementById('chat-messages');
    const messageForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('chat-message-input');
    const unreadBadge = document.getElementById('chat-unread-badge');
    const notificationSound = document.getElementById('chat-notification-sound');
    const adminUserListDiv = document.getElementById('admin-user-list');
    const chatTitle = document.getElementById('chat-title');
    const chatInputArea = document.getElementById('chat-input-area');

    // Stanje chata
    let isAdmin = false;
    let activeRecipientId = null;
    let pollingInterval = null;
    let lastKnownMessageId = 0;

    const currentUserId = document.body.dataset.currentUserId;

    // --- Inicijalizacija ---
    async function initializeChat() {
        try {
            const response = await fetch('/chat/widget_data');
            const data = await response.json();

            isAdmin = data.is_admin;

            if (isAdmin) {
                chatTitle.textContent = 'Podrška Korisnicima';
                displayAdminUserList(data.users);
            } else {
                activeRecipientId = data.admin_id;
                // --- IZMJENA JE OVDJE ---
                chatTitle.textContent = 'Podrška Korisnicima';
                // --- KRAJ IZMJENE ---
                messagesDiv.classList.remove('d-none');
                chatInputArea.classList.remove('d-none');

                if (data.unread_count > 0) {
                    showUnreadBadge(data.unread_count);
                }
            }
            startPollingForNewMessages();
        } catch (error) {
            console.error('Greška pri inicijalizaciji chata:', error);
        }
    }

    // --- Event listeneri ---
    toggleButton.addEventListener('click', toggleChatWindow);
    closeBtn.addEventListener('click', closeChatWindow);
    messageForm.addEventListener('submit', sendMessage);
    if (backBtn) {
        backBtn.addEventListener('click', showAdminUserList);
    }


    // --- Funkcije ---
    function toggleChatWindow() {
        chatWindow.classList.toggle('d-none');
        if (!chatWindow.classList.contains('d-none')) {
            if (isAdmin) {
                showAdminUserList();
            } else if (!isAdmin && activeRecipientId) {
                messagesDiv.classList.remove('d-none');
                chatInputArea.classList.remove('d-none');
                fetchHistory(activeRecipientId);
            }
            hideUnreadBadge();
        }
    }

    function closeChatWindow() {
        chatWindow.classList.add('d-none');
    }

    function showUnreadBadge(count) {
        unreadBadge.textContent = count > 9 ? '9+' : count;
        unreadBadge.classList.remove('d-none');
    }

    function hideUnreadBadge() {
        unreadBadge.classList.add('d-none');
    }

    function playNotificationSound() {
        notificationSound.play().catch(e => console.error("Greška pri puštanju zvuka:", e));
    }

    function displayMessages(messages, clear = true) {
        if (clear) {
            messagesDiv.innerHTML = '<p class="text-center text-muted">Učitavanje poruka...</p>';
        }

        if (!messages || messages.length === 0) {
            messagesDiv.innerHTML = '<p class="text-center text-muted">Nema poruka u ovom razgovoru.</p>';
            return;
        }

        if (clear) {
            messagesDiv.innerHTML = '';
        }

        messages.forEach(msg => {
            appendMessage(msg);
        });
        scrollToBottom();
    }

    function appendMessage(msg, isNew = false) {
        const messageElement = document.createElement('div');
        const isSender = msg.sender_id == currentUserId;
        messageElement.classList.add('message', isSender ? 'sent' : 'received');
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${escapeHTML(msg.content)}</p>
                <span class="timestamp">${msg.timestamp}</span>
            </div>
        `;
        messagesDiv.appendChild(messageElement);

        if (isNew && !isSender) {
            playNotificationSound();
        }
        scrollToBottom();
    }

    async function fetchHistory(userId) {
        try {
            const response = await fetch(`/chat/history/${userId}`);
            const messages = await response.json();
            lastKnownMessageId = messages.length > 0 ? messages[messages.length - 1].id : 0;
            displayMessages(messages);
        } catch (error) {
            console.error("Greška pri dohvatanju istorije:", error);
        }
    }

    async function sendMessage(e) {
        e.preventDefault();
        const content = messageInput.value.trim();
        if (!content || !activeRecipientId) return;

        try {
            const response = await fetch('/chat/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify({ recipient_id: activeRecipientId, content: content })
            });
            const data = await response.json();
            if (data.success) {
                messageInput.value = '';
                appendMessage({
                    sender_id: currentUserId,
                    content: content,
                    timestamp: 'Sada'
                });
            } else {
                showModalAlert('Greška: ' + data.error, 'Greška', 'danger');
            }
        } catch (error) {
            console.error('Greška pri slanju:', error);
        }
    }

    function startPollingForNewMessages() {
        if (pollingInterval) clearInterval(pollingInterval);
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/chat/unread_check?last_id=${lastKnownMessageId}`);
                const data = await response.json();
                if (data.has_new) {
                    lastKnownMessageId = data.last_id;
                    const isChatOpen = !chatWindow.classList.contains('d-none');

                    for (const senderId in data.senders) {
                        if (isChatOpen && senderId == activeRecipientId) {
                            data.senders[senderId].forEach(msg => appendMessage(msg, true));
                            fetchHistory(activeRecipientId);
                        } else {
                            playNotificationSound();
                            const badge = document.querySelector(`#user-${senderId}-badge`);
                            if(badge){
                                let currentCount = parseInt(badge.textContent || '0');
                                badge.textContent = currentCount + data.senders[senderId].length;
                                badge.classList.remove('d-none');
                            }
                        }
                    }
                }
            } catch (error) {
                console.error("Polling greška:", error);
            }
        }, 15000);
    }

    // --- Adminove funkcije ---
    function displayAdminUserList(users) {
        adminUserListDiv.innerHTML = '';
        users.forEach(user => {
            const userElement = document.createElement('div');
            userElement.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            userElement.style.cursor = 'pointer';

            const userInfo = document.createElement('div');
            userInfo.classList.add('user-info');
            userInfo.textContent = user.username;
            userInfo.dataset.userId = user.id;
            userInfo.dataset.userName = user.username;

            const controls = document.createElement('div');
            controls.innerHTML = `
                <span id="user-${user.id}-badge" class="badge bg-danger me-2 ${user.unread_count > 0 ? '' : 'd-none'}">${user.unread_count}</span>
                <span class="delete-conversation-btn" data-user-id="${user.id}">&times;</span>
            `;

            userElement.appendChild(userInfo);
            userElement.appendChild(controls);

            userInfo.addEventListener('click', (e) => {
                showConversation(user.id, user.username);
            });

            controls.querySelector('.delete-conversation-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteConversation(user.id, user.username, userElement);
            });

            adminUserListDiv.appendChild(userElement);
        });
    }

    async function deleteConversation(userId, username, elementToRemove) {
        showModalConfirm(
            `Da li ste sigurni da želite obrisati cijeli razgovor sa korisnikom ${username}?`,
            async function() {
                try {
                    const response = await fetch(`/chat/delete/${userId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() }
                    });
                    const data = await response.json();
                    if (data.success) {
                        elementToRemove.remove();
                        if (userId === activeRecipientId) {
                            showAdminUserList();
                        }
                    } else {
                        showModalAlert('Greška pri brisanju: ' + data.error, 'Greška', 'danger');
                    }
                } catch (error) {
                    console.error('Greška pri brisanju razgovora:', error);
                }
            },
            null,
            'Potvrda brisanja',
            'Da, obriši',
            'Otkaži'
        );
    }

    function showAdminUserList() {
        if (!isAdmin) return;
        adminUserListDiv.classList.remove('d-none');
        messagesDiv.classList.add('d-none');
        chatInputArea.classList.add('d-none');
        backBtn.classList.add('d-none');
        chatTitle.textContent = 'Podrška Korisnicima';
        activeRecipientId = null;
    }

    function showConversation(userId, username) {
        if (!isAdmin) return;
        adminUserListDiv.classList.add('d-none');
        messagesDiv.classList.remove('d-none');
        chatInputArea.classList.remove('d-none');
        backBtn.classList.remove('d-none');
        chatTitle.textContent = `Razgovor sa: ${username}`;
        activeRecipientId = userId;
        fetchHistory(userId);
    }

    // --- Pomoćne funkcije ---
    function getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g,
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
    function scrollToBottom() {
        if (messagesDiv) {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    }

    // Inicijalizacija
    initializeChat();
});