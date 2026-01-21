// FadMann - Frontend JavaScript Application
// Simple, framework-free chat application

// ============================================================================
// GLOBAL STATE
// ============================================================================

let currentUser = null;
let currentRoom = null;
let websocket = null;
let rooms = [];
let onlineCounts = {}; // Track online users per room
let replyingTo = null; // Track which message we're replying to

// ============================================================================
// INITIALIZATION
// ============================================================================

const appContainer = document.getElementById('app');

document.addEventListener('DOMContentLoaded', () => {
    if (!appContainer) {
        console.error('App container not found!');
        return;
    }
    checkAuth();
});

// ============================================================================
// AUTHENTICATION
// ============================================================================

async function checkAuth() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        showLogin();
        return;
    }
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            showChat();
        } else {
            localStorage.removeItem('auth_token');
            showLogin();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLogin();
    }
}

// ============================================================================
// LOGIN SCREEN
// ============================================================================

function showLogin() {
    appContainer.innerHTML = `
        <div class="login-container">
            <div class="login-card">
                <h1>FadMann</h1>
                <p class="tagline">Reconnect with your campus community</p>
                <div id="errorMessage"></div>
                <form id="loginForm">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input 
                            type="text" 
                            id="username" 
                            placeholder="Enter your username"
                            required
                            autocomplete="username"
                        >
                    </div>
                    <div class="form-group">
                        <label for="displayName">Display Name</label>
                        <input 
                            type="text" 
                            id="displayName" 
                            placeholder="How should we call you?"
                            required
                            autocomplete="name"
                        >
                    </div>
                    <button type="submit" class="submit-button">Enter Chat</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // Focus on username field
    document.getElementById('username').focus();
}

async function handleLogin(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.innerHTML = '';
    
    const username = document.getElementById('username').value.trim();
    const displayName = document.getElementById('displayName').value.trim();
    
    if (!username || !displayName) {
        errorDiv.innerHTML = '<div class="error-message">Please fill in all fields</div>';
        return;
    }
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, display_name: displayName })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('auth_token', data.token);
            currentUser = data.user;
            showChat();
        } else {
            errorDiv.innerHTML = `<div class="error-message">${data.detail || 'Login failed'}</div>`;
        }
    } catch (error) {
        errorDiv.innerHTML = '<div class="error-message">Connection error. Please try again.</div>';
        console.error('Login error:', error);
    }
}

// ============================================================================
// CHAT INTERFACE
// ============================================================================

async function showChat() {
    await loadRooms();
    renderChat();
    if (currentRoom) {
        connectWebSocket();
    }
}

async function loadRooms() {
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/rooms', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            rooms = await response.json();
        }
    } catch (error) {
        console.error('Failed to load rooms:', error);
    }
}

function renderChat() {
    const roomListHTML = rooms.map(room => {
        const onlineCount = onlineCounts[room.id] || 0;
        const isActive = room.id === currentRoom?.id;
        return `
            <li class="room-item ${isActive ? 'active' : ''}" 
                onclick="selectRoom(${room.id})">
                <div class="room-icon">${room.name.charAt(0).toUpperCase()}</div>
                <div class="room-info">
                    <h4>${escapeHtml(room.name)}</h4>
                    <p>${escapeHtml(room.description || 'Chat room')}</p>
                    ${onlineCount > 0 ? `<span class="online-count">${onlineCount} online</span>` : ''}
                </div>
            </li>
        `;
    }).join('');
    
    appContainer.innerHTML = `
        <div class="sidebar">
            <div class="sidebar-header">
                <h1>FadMann</h1>
                <p>Campus Chat</p>
            </div>
            <div class="user-profile">
                <div class="user-avatar">${getInitials(currentUser.display_name)}</div>
                <div class="user-info">
                    <h3>${escapeHtml(currentUser.display_name)}</h3>
                    <p>@${escapeHtml(currentUser.username)}</p>
                </div>
            </div>
            <div class="rooms-section">
                <div class="rooms-header">
                    <h2>Rooms</h2>
                    <button class="create-room-btn" onclick="showCreateRoomModal()" title="Create new room">
                        <span>+</span>
                    </button>
                </div>
                <ul class="room-list">
                    ${roomListHTML}
                </ul>
            </div>
        </div>
        <div class="chat-area">
            <div class="chat-header">
                <div>
                    <h2 id="roomName">${currentRoom ? escapeHtml(currentRoom.name) : 'Select a room to start chatting'}</h2>
                    ${currentRoom ? `<p class="room-description">${escapeHtml(currentRoom.description || '')}</p>` : ''}
                </div>
                <div id="typingIndicator" class="typing-indicator"></div>
            </div>
            <div id="messagesContainer" class="messages-container"></div>
            <div class="message-input-area">
                <div class="input-wrapper">
                    <textarea 
                        id="messageInput" 
                        placeholder="${currentRoom ? 'Type a message...' : 'Select a room first'}" 
                        rows="1"
                        ${!currentRoom ? 'disabled' : ''}
                        onkeydown="handleKeyDown(event)"
                        oninput="handleTyping()"
                    ></textarea>
                    <button 
                        id="sendButton" 
                        class="send-button" 
                        onclick="sendMessage()"
                        ${!currentRoom ? 'disabled' : ''}
                    >Send</button>
                </div>
            </div>
        </div>
        <footer class="app-footer">
            <p>Reconnect with your campus community, one message at a time.</p>
        </footer>
    `;
    
    if (currentRoom) {
        loadMessageHistory();
    }
}

// ============================================================================
// ROOM MANAGEMENT
// ============================================================================

async function selectRoom(roomId) {
    const room = rooms.find(r => r.id === roomId);
    if (!room) return;
    
    // Disconnect from previous room
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
    }
    
    currentRoom = room;
    renderChat();
    connectWebSocket();
}

function showCreateRoomModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Create New Room</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <form id="createRoomForm" onsubmit="handleCreateRoom(event)">
                <div class="form-group">
                    <label for="roomName">Room Name</label>
                    <input 
                        type="text" 
                        id="roomName" 
                        placeholder="e.g., Study Group 1"
                        required
                        autofocus
                    >
                </div>
                <div class="form-group">
                    <label for="roomDescription">Description (optional)</label>
                    <textarea 
                        id="roomDescription" 
                        placeholder="What's this room about?"
                        rows="3"
                    ></textarea>
                </div>
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="roomPublic" checked>
                        <span>Public room (anyone can join)</span>
                    </label>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                    <button type="submit" class="btn-primary">Create Room</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.getElementById('roomName').focus();
}

async function handleCreateRoom(e) {
    e.preventDefault();
    
    const name = document.getElementById('roomName').value.trim();
    const description = document.getElementById('roomDescription').value.trim();
    const isPublic = document.getElementById('roomPublic').checked;
    
    if (!name) {
        alert('Please enter a room name');
        return;
    }
    
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch('/api/rooms', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                description,
                is_public: isPublic
            })
        });
        
        if (response.ok) {
            const newRoom = await response.json();
            rooms.push(newRoom);
            document.querySelector('.modal-overlay').remove();
            renderChat();
            // Auto-select the new room
            selectRoom(newRoom.id);
        } else {
            const data = await response.json();
            alert(data.detail || 'Failed to create room');
        }
    } catch (error) {
        console.error('Create room error:', error);
        alert('Connection error. Please try again.');
    }
}

// ============================================================================
// WEBSOCKET CONNECTION
// ============================================================================

function connectWebSocket() {
    if (!currentRoom || !currentUser) return;
    
    const token = localStorage.getItem('auth_token');
    if (!token) {
        console.error('No auth token found');
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/${currentRoom.id}?token=${token}`;
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
    }
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
        console.log('WebSocket connected to room:', currentRoom.name);
        // Update online count when we connect
        updateOnlineCount();
    };
    
    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    websocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        
        // Handle reconnection gracefully
        // 1000 = normal closure (user closed browser, etc.)
        // 1001 = going away (server restart, etc.)
        // 1006 = abnormal closure (network error, etc.)
        // 4001 = authentication error (token invalid)
        
        if (event.code === 4001) {
            // Authentication error - token expired or invalid
            console.error('Authentication failed. Please log in again.');
            localStorage.removeItem('auth_token');
            showLogin();
            return;
        }
        
        // Try to reconnect for network errors (not normal closure or auth errors)
        if (event.code !== 1000 && event.code !== 4001 && currentRoom && currentUser) {
            console.log('Attempting to reconnect in 3 seconds...');
            setTimeout(() => {
                if (currentRoom && currentUser) {
                    connectWebSocket();
                }
            }, 3000);
        }
    };
}

function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'message':
            addMessage(data.message);
            break;
        case 'reaction_update':
            updateMessageReactions(data.message_id, data.reactions);
            break;
        case 'typing':
            updateTypingIndicator(data.user_id, data.is_typing, data.username);
            break;
        case 'user_joined':
            updateOnlineCount();
            break;
        case 'user_left':
            updateOnlineCount();
            break;
        case 'error':
            // Handle server-side errors (validation, rate limit, etc.)
            console.error('Server error:', data.message);
            // Show error to user (you could add a toast notification here)
            alert(data.message || 'An error occurred');
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// ============================================================================
// MESSAGES
// ============================================================================

async function loadMessageHistory() {
    if (!currentRoom) return;
    
    try {
        const token = localStorage.getItem('auth_token');
        const response = await fetch(`/api/rooms/${currentRoom.id}/messages`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const messages = await response.json();
            const container = document.getElementById('messagesContainer');
            container.innerHTML = '';
            
            messages.forEach(message => {
                addMessage(message, false);
            });
            
            scrollToBottom();
        }
    } catch (error) {
        console.error('Failed to load messages:', error);
    }
}

function addMessage(message, animate = true) {
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    const isOwn = message.user_id === currentUser.id;
    const messageClass = isOwn ? 'message own' : 'message';
    
    // Build reply preview if this is a reply
    let replyPreview = '';
    if (message.reply_to_message) {
        replyPreview = `
            <div class="reply-preview" onclick="scrollToMessage(${message.reply_to})">
                <span class="reply-author">${escapeHtml(message.reply_to_message.display_name)}</span>
                <span class="reply-content">${escapeHtml(message.reply_to_message.content)}</span>
            </div>
        `;
    }
    
    // Build reactions HTML
    const reactions = message.reactions || {};
    let reactionsHTML = '';
    const reactionEmojis = Object.keys(reactions);
    if (reactionEmojis.length > 0) {
        reactionsHTML = '<div class="message-reactions">';
        reactionEmojis.forEach(emoji => {
            const userIds = reactions[emoji] || [];
            const hasReacted = userIds.includes(currentUser.id);
            reactionsHTML += `
                <button class="reaction-btn ${hasReacted ? 'reacted' : ''}" 
                        onclick="toggleReaction(${message.id}, '${emoji}')"
                        title="${userIds.length} reaction${userIds.length !== 1 ? 's' : ''}">
                    ${emoji} <span class="reaction-count">${userIds.length}</span>
                </button>
            `;
        });
        reactionsHTML += '</div>';
    }
    
    const messageHTML = `
        <div class="${messageClass}" id="message-${message.id}">
            <div class="message-avatar">${getInitials(message.display_name || message.username || 'U')}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">${escapeHtml(message.display_name || message.username || 'Unknown')}</span>
                    <span class="message-time">${formatTime(message.created_at)}</span>
                </div>
                ${replyPreview}
                <div class="message-bubble">${escapeHtml(message.content)}</div>
                ${reactionsHTML}
                <div class="message-actions">
                    <button class="action-btn" onclick="startReply(${message.id})" title="Reply">Reply</button>
                    <button class="action-btn" onclick="showReactionPicker(${message.id})" title="Add reaction">React</button>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
}

function updateMessageReactions(messageId, reactions) {
    const messageEl = document.getElementById(`message-${messageId}`);
    if (!messageEl) return;
    
    const reactionsContainer = messageEl.querySelector('.message-reactions');
    const reactionsHTML = document.createElement('div');
    reactionsHTML.className = 'message-reactions';
    
    const reactionEmojis = Object.keys(reactions || {});
    if (reactionEmojis.length > 0) {
        reactionEmojis.forEach(emoji => {
            const userIds = reactions[emoji] || [];
            const hasReacted = userIds.includes(currentUser.id);
            reactionsHTML.innerHTML += `
                <button class="reaction-btn ${hasReacted ? 'reacted' : ''}" 
                        onclick="toggleReaction(${messageId}, '${emoji}')"
                        title="${userIds.length} reaction${userIds.length !== 1 ? 's' : ''}">
                    ${emoji} <span class="reaction-count">${userIds.length}</span>
                </button>
            `;
        });
    }
    
    const oldReactions = messageEl.querySelector('.message-reactions');
    if (oldReactions) {
        oldReactions.replaceWith(reactionsHTML);
    } else if (reactionEmojis.length > 0) {
        const messageContent = messageEl.querySelector('.message-content');
        const messageBubble = messageEl.querySelector('.message-bubble');
        messageBubble.after(reactionsHTML);
    }
}

function toggleReaction(messageId, emoji) {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) return;
    
    websocket.send(JSON.stringify({
        type: 'reaction',
        message_id: messageId,
        emoji: emoji
    }));
}

function showReactionPicker(messageId) {
    const commonEmojis = ['👍', '❤️', '😂', '😮', '😢', '🔥', '👏', '🎉'];
    const picker = document.createElement('div');
    picker.className = 'reaction-picker';
    picker.innerHTML = commonEmojis.map(emoji => 
        `<button onclick="toggleReaction(${messageId}, '${emoji}'); this.closest('.reaction-picker').remove();">${emoji}</button>`
    ).join('');
    
    // Position picker near the message
    const messageEl = document.getElementById(`message-${messageId}`);
    if (messageEl) {
        messageEl.querySelector('.message-actions').appendChild(picker);
        setTimeout(() => {
            if (picker.parentNode) {
                picker.remove();
            }
        }, 5000);
    }
}

function startReply(messageId) {
    replyingTo = messageId;
    const messageEl = document.getElementById(`message-${messageId}`);
    if (messageEl) {
        const content = messageEl.querySelector('.message-bubble').textContent;
        const author = messageEl.querySelector('.message-author').textContent;
        showReplyIndicator(author, content.substring(0, 50));
    }
    document.getElementById('messageInput').focus();
}

function cancelReply() {
    replyingTo = null;
    const indicator = document.querySelector('.reply-indicator');
    if (indicator) indicator.remove();
}

function showReplyIndicator(author, content) {
    // Remove existing indicator
    const existing = document.querySelector('.reply-indicator');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.className = 'reply-indicator';
    indicator.innerHTML = `
        <span>Replying to <strong>${escapeHtml(author)}</strong>: ${escapeHtml(content)}...</span>
        <button onclick="cancelReply()">✕</button>
    `;
    
    const inputArea = document.querySelector('.message-input-area');
    inputArea.insertBefore(indicator, inputArea.firstChild);
}

function scrollToMessage(messageId) {
    const messageEl = document.getElementById(`message-${messageId}`);
    if (messageEl) {
        messageEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        messageEl.style.animation = 'highlight 2s';
        setTimeout(() => {
            messageEl.style.animation = '';
        }, 2000);
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();
    
    // Client-side validation: prevent empty messages
    if (!content) {
        return; // Don't send empty messages
    }
    
    // Check WebSocket connection
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        // Try to reconnect
        if (currentRoom && currentUser) {
            connectWebSocket();
        }
        return;
    }
    
    if (!currentRoom) {
        return;
    }
    
    const message = {
        type: 'message',
        room_id: currentRoom.id,
        content: content,
        reply_to: replyingTo || null
    };
    
    // Clear reply state
    if (replyingTo) {
        cancelReply();
    }
    
    try {
        websocket.send(JSON.stringify(message));
        input.value = '';
        input.style.height = 'auto';
        handleTypingStop();
    } catch (error) {
        console.error('Failed to send message:', error);
        // Connection might be dead, try to reconnect
        if (currentRoom && currentUser) {
            connectWebSocket();
        }
    }
}

// ============================================================================
// TYPING INDICATOR
// ============================================================================

let typingTimeout = null;
function handleTyping() {
    if (!websocket || websocket.readyState !== WebSocket.OPEN || !currentRoom) return;
    
    if (!typingTimeout) {
        websocket.send(JSON.stringify({
            type: 'typing',
            room_id: currentRoom.id,
            is_typing: true
        }));
    }
    
    clearTimeout(typingTimeout);
    
    typingTimeout = setTimeout(() => {
        handleTypingStop();
    }, 2000);
}

function handleTypingStop() {
    if (typingTimeout) {
        clearTimeout(typingTimeout);
        typingTimeout = null;
    }
    
    if (websocket && websocket.readyState === WebSocket.OPEN && currentRoom) {
        websocket.send(JSON.stringify({
            type: 'typing',
            room_id: currentRoom.id,
            is_typing: false
        }));
    }
}

function updateTypingIndicator(userId, isTyping, username) {
    const indicator = document.getElementById('typingIndicator');
    if (!indicator) return;
    
    if (userId === currentUser.id) return;
    
    if (isTyping) {
        indicator.textContent = `${username || 'Someone'} is typing...`;
    } else {
        indicator.textContent = '';
    }
}

// ============================================================================
// ONLINE COUNT
// ============================================================================

async function updateOnlineCount() {
    if (!currentRoom) return;
    
    // For now, we'll estimate based on WebSocket connections
    // In a real app, you'd query the backend for actual count
    // For simplicity, we'll show a count when we know users are connected
    const count = Object.keys(onlineCounts).length > 0 ? onlineCounts[currentRoom.id] || 0 : 0;
    
    // Update the room list to show online count
    const roomItems = document.querySelectorAll('.room-item');
    roomItems.forEach(item => {
        const roomId = parseInt(item.getAttribute('onclick').match(/\d+/)[0]);
        if (roomId === currentRoom.id) {
            const roomInfo = item.querySelector('.room-info');
            let onlineBadge = roomInfo.querySelector('.online-count');
            if (count > 0) {
                if (!onlineBadge) {
                    onlineBadge = document.createElement('span');
                    onlineBadge.className = 'online-count';
                    roomInfo.appendChild(onlineBadge);
                }
                onlineBadge.textContent = `${count} online`;
            } else if (onlineBadge) {
                onlineBadge.remove();
            }
        }
    });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function formatTime(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    // Show relative time for recent messages
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    // Show date for older messages
    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = date.toDateString() === new Date(now.getTime() - 86400000).toDateString();
    
    if (isToday) {
        return `Today ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else if (isYesterday) {
        return `Yesterday ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`;
    } else {
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    }
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}
