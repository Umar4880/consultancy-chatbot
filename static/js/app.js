

let sessionId = null;
let userId = null;
let chatSessions = [];



// Initialize session and chat list on load


window.onload = async () => {
    // Always ensure userId exists and is persistent
    await initializeUserId();
    // On first load, fetch chat list and show branding, but do NOT load any chat automatically.
    await fetchChatSessions();
    // Show branding message
    const chatArea = document.getElementById('chatArea');
    const branding = document.getElementById('brandingMessage');
    if (chatArea && branding) {
        chatArea.innerHTML = '';
        branding.style.display = 'flex';
        chatArea.appendChild(branding);
    }
    // Add event listener for mode change
    const modeSelector = document.getElementById('modeSelector');
    if (modeSelector) {
        modeSelector.addEventListener('change', async () => {
            if (sessionId) {
                console.log('Mode changed to:', modeSelector.value);
                await loadChatHistory();
                await fetchChatSessions();
            }
        });
    }
    // Always render chat list on load
    renderChatList();
};

// Initialize userId - create once and keep forever for this browser
async function initializeUserId() {
    userId = localStorage.getItem('userId');
    if (!userId) {
        // Generate a unique, persistent userId for this browser
        userId = 'user-' + Math.random().toString(36).substring(2, 15) + '-' + Date.now();
        localStorage.setItem('userId', userId);
        console.log('Created new userId:', userId);
    } else {
        console.log('Using existing userId:', userId);
    }
}




async function createAndStoreNewSession(switchToNew = true) {
    try {
        console.log('Creating new session for userId:', userId);
        // Always use the same userId for this browser
        const response = await fetch('/api/session/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });
        const data = await response.json();
        console.log('New session created:', data);
        if (switchToNew) {
            sessionId = data.session_id;
            localStorage.setItem('sessionId', sessionId);
            // userId does not change
            console.log('Switched to new session:', sessionId);

            // Immediately add to chatSessions with default name
            chatSessions.unshift({
                sessionId: sessionId,
                name: "New Chat"
            });

            // // Clear chat area and show branding message
            // const chatArea = document.getElementById('chatArea');
            // if (chatArea) chatArea.innerHTML = '';
            // const branding = document.getElementById('brandingMessage');
            // if (branding) {
            //     branding.style.display = 'flex';
            //     chatArea.appendChild(branding);
            // }

            // Render immediately so user sees the new chat
            renderChatList();
            // Show branding until user sends a message
            const chatArea = document.getElementById('chatArea');
            if (chatArea) chatArea.innerHTML = '';
            const branding = document.getElementById('brandingMessage');
            if (branding) {
                branding.style.display = 'flex';
                chatArea.appendChild(branding);
            }
        }
        // Don't fetch all sessions here - just show the immediate update
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Failed to create new session');
    }
}


// Create a new chat and switch to it in the same window
async function newSession() {
    await createAndStoreNewSession(true);
    // Do not load history until user sends a message
}

// Fetch chat sessions from backend and render chat list
async function fetchChatSessions() {
    if (!userId) return;
    try {
        console.log('Fetching sessions for userId:', userId);
        const response = await fetch(`/api/sessions?user_id=${userId}`);
        if (!response.ok) throw new Error('Failed to fetch chat sessions');
        const data = await response.json();
        console.log('Fetched sessions:', data);
        chatSessions = (data.sessions || []).map(s => ({
            sessionId: s.session_id,
            name: s.session_name
        }));
        console.log('Processed sessions:', chatSessions);
        renderChatList();
    } catch (e) {
        console.error('Error fetching chat sessions:', e);
        // Still render chat list (empty)
        renderChatList();
    }
}

// Render the chat session list under the chat section
function renderChatList() {
    const chatListDiv = document.getElementById('chatList');
    if (!chatListDiv) return;
    chatListDiv.innerHTML = '';
    chatSessions.forEach((chat, idx) => {
        const chatBtn = document.createElement('button');
        chatBtn.className = 'chat-list-item';
        const displayName = chat.name || `Chat ${idx + 1}`;
        chatBtn.textContent = displayName + (chat.sessionId === sessionId ? ' (active)' : '');
        chatBtn.onclick = () => switchToChat(idx);
        chatListDiv.appendChild(chatBtn);
    });
}


// Switch to a selected chat session

function switchToChat(idx) {
    const chat = chatSessions[idx];
    if (!chat) return;
    sessionId = chat.sessionId;
    localStorage.setItem('sessionId', sessionId);
    // userId does not change

    // Clear chat area and show branding message until history loads
    const chatArea = document.getElementById('chatArea');
    if (chatArea) chatArea.innerHTML = '';
    const branding = document.getElementById('brandingMessage');
    if (branding) {
        branding.style.display = 'flex';
        chatArea.appendChild(branding);
    }

    renderChatList();
    // Only load chat history when user clicks a chat
    loadChatHistory();
}

// No longer needed: session names are fetched with fetchChatSessions

// Load chat history for the current session
async function loadChatHistory() {
    if (!sessionId || !userId) return;
    try {
        const modeSelector = document.getElementById('modeSelector');
        let mode = modeSelector.value;
        const response = await fetch(`/api/session/${sessionId}/history?user_id=${userId}&mode=${mode}`);
        if (!response.ok) throw new Error('Failed to load chat history');
        const data = await response.json();

        // If last_mode is present and different, set and reload
        if (data.last_mode && modeSelector && data.last_mode !== mode) {
            modeSelector.value = data.last_mode;
            // Reload chat history for the correct mode, but avoid infinite loop
            await loadChatHistory();
            return;
        }

        const chatArea = document.getElementById('chatArea');
        // Only clear chat area if there are messages
        if (data.messages && data.messages.length > 0) {
            chatArea.innerHTML = '';
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role === 'ai' ? 'bot' : 'user');
            });
            // Hide branding if any chat
            const branding = document.getElementById('brandingMessage');
            if (branding) branding.style.display = 'none';
        } else {
            // Show branding if no chat
            const branding = document.getElementById('brandingMessage');
            if (branding) {
                branding.style.display = 'flex';
                chatArea.appendChild(branding);
            }
        }
    } catch (e) {
        console.error('Error loading chat history:', e);
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Hide branding message on first user message (always)
    setTimeout(() => {
        const branding = document.getElementById('brandingMessage');
        if (branding) branding.style.display = 'none';
    }, 10);
    
    // Add user message to chat
    addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable send button
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    
    try {
        const mode = document.getElementById('modeSelector').value;
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                user_id: userId,
                mode: mode
            })
        });
        if (!response.ok) {
            console.error('Fetch failed, status:', response.status, 'statusText:', response.statusText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        let data;
        try {
            data = await response.json();
        } catch (jsonErr) {
            console.error('Failed to parse JSON from response:', jsonErr);
            const text = await response.text();
            console.error('Raw response text:', text);
            throw new Error('Invalid JSON in response');
        }
        // Update session info if new session was created
        if (!sessionId) {
            sessionId = data.session_id;
            userId = data.user_id;
            // Removed buggy line: document.getElementById('sessionId').textContent = sessionId.substring(0, 8) + '...';
        }
        // Remove typing indicator and add bot response
        hideTypingIndicator();
        addMessage(data.response, 'bot');
        // Refresh chat list in case session name was updated (for first messages)
        await fetchChatSessions();
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('Sorry, there was an error processing your request. Please try again.\nDetails: ' + error, 'bot');
    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}

function addMessage(content, sender) {
    const chatArea = document.getElementById('chatArea');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Parse markdown for bot messages, escape HTML for user messages
    let processedContent;
    if (sender === 'bot') {
        // Configure marked for safe rendering
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: false,
            smartLists: true,
            smartypants: true
        });
        processedContent = marked.parse(content);
    } else {
        processedContent = escapeHtml(content);
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">${processedContent}</div>
    `;
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function showTypingIndicator() {
    const chatArea = document.getElementById('chatArea');
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typingIndicator';
    indicator.style.display = 'block';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    chatArea.appendChild(indicator);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function clearHistory() {
    if (!sessionId || !userId) {
        alert('No active session');
        return;
    }
    
    if (!confirm('Are you sure you want to clear chat history?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/session/${sessionId}/clear?user_id=${userId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const chatArea = document.getElementById('chatArea');
        chatArea.innerHTML = `
            <div class="message bot">
                <div class="message-content">
                    Chat history cleared!
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error clearing history:', error);
        alert('Failed to clear history');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
