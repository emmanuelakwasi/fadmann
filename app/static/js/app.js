// FadMann - Frontend JavaScript Application

// Global state
let currentUser = null;
let currentRoom = null;
let websocket = null;
let rooms = [];

// DOM elements
const appContainer = document.getElementById('app');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Check if user is authenticated
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

// Show login form
function showLogin() {
    appContainer.innerHTML = `
        <div class="login-container">
            <div class="login-card">
                <h1>FadMann</h1>
                <p>Reconnect with your campus community</p>
                <div id="errorMessage"></div>
                <form id="loginForm">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="username" required>
                    </div>
                    <div class="form-group">
                        <label>Display Name</label>
                        <input type="text" id="displayName" required>
                    </div>
                    <button type="submit" class="submit-button">Enter Chat</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
}

// Handle login
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

// Show main chat interface
async function showChat() {
    await loadRooms();
    renderChat();
    connectWebSocket();
}

// Load rooms from API
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

// Render chat interface
function renderChat() {
    const roomListHTML = rooms.map(room => `
        <li class="room-item ${room.id === currentRoom?.id ? 'active' : ''}" 
            onclick="selectRoom(${room.id})">
            <div class="room-icon">${room.name.charAt(0).toUpperCase()}</div>
            <div class="room-info">
                <h4>${escapeHtml(room.name)}</h4>
                <p>${escapeHtml(room.description || 'Chat room')}</p>
            </div>
        </li>
    `).join('');
    
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
                <h2>Rooms</h2>
                <ul class="room-list">
                    ${roomListHTML}
                </ul>
            </div>
        </div>
        <div class="chat-area">
            <div class="chat-header">
                <h2 id="roomName">Select a room to start chatting</h2>
                <div id="typingIndicator" class="typing-indicator"></div>
            </div>
            <div id="messagesContainer" class="messages-container"></div>
            <div class="message-input-area">
                <div class="input-wrapper">
                    <textarea 
                        id="messageInput" 
                        placeholder="Type a message..." 
                        rows="1"
                        onkeydown="handleKeyDown(event)"
                        oninput="handleTyping()">
                    </textarea>
                    <button id="sendButton" class="send-button" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    `;
    
    if (currentRoom) {
        loadMessageHistory();
    }
}

// Select a room
async function selectRoom(roomId) {
    const room = rooms.find(r => r.id === roomId);
    if (!room) return;
    
    currentRoom = room;
    document.getElementById('roomName').textContent = room.name;
    renderChat();
    connectWebSocket();
}

// Connect to WebSocket
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
        // Optionally try to reconnect
        if (event.code !== 1000) {  // Not a normal closure
            setTimeout(() => {
                if (currentRoom && currentUser) {
                    connectWebSocket();
                }
            }, 3000);
        }
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'message':
            addMessage(data.message);
            break;
        case 'typing':
            updateTypingIndicator(data.user_id, data.is_typing, data.username);
            break;
        case 'user_joined':
            console.log(`User ${data.user_id} joined`);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

// Load message history
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

// Add message to UI
function addMessage(message, animate = true) {
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    const isOwn = message.user_id === currentUser.id;
    const messageClass = isOwn ? 'message own' : 'message';
    
    const messageHTML = `
        <div class="${messageClass}">
            <div class="message-avatar">${getInitials(message.username || 'U')}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-author">${escapeHtml(message.display_name || message.username || 'Unknown')}</span>
                    <span>${formatTime(message.created_at)}</span>
                </div>
                <div class="message-bubble">${escapeHtml(message.content)}</div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
}

// Send message
function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();
    
    if (!content || !websocket || websocket.readyState !== WebSocket.OPEN) {
        return;
    }
    
    const message = {
        type: 'message',
        room_id: currentRoom.id,
        content: content
    };
    
    websocket.send(JSON.stringify(message));
    input.value = '';
    input.style.height = 'auto';
    
    // Stop typing indicator
    handleTypingStop();
}

// Handle typing indicator
let typingTimeout = null;
function handleTyping() {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) return;
    
    // Send typing start
    if (!typingTimeout) {
        websocket.send(JSON.stringify({
            type: 'typing',
            room_id: currentRoom.id,
            is_typing: true
        }));
    }
    
    // Clear previous timeout
    clearTimeout(typingTimeout);
    
    // Set timeout to stop typing
    typingTimeout = setTimeout(() => {
        handleTypingStop();
    }, 2000);
}

function handleTypingStop() {
    if (typingTimeout) {
        clearTimeout(typingTimeout);
        typingTimeout = null;
    }
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
            type: 'typing',
            room_id: currentRoom.id,
            is_typing: false
        }));
    }
}

// Update typing indicator UI
function updateTypingIndicator(userId, isTyping, username) {
    const indicator = document.getElementById('typingIndicator');
    if (!indicator) return;
    
    if (userId === currentUser.id) return; // Don't show own typing
    
    if (isTyping) {
        indicator.textContent = `${username || 'Someone'} is typing...`;
    } else {
        indicator.textContent = '';
    }
}

// Handle Enter key
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}
