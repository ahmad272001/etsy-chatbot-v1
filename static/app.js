// Global variables
let currentUser = null;
let currentThread = null;
let authToken = null;

// API base URL
const API_BASE = '';

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
        authToken = token;
        validateToken();
    }
    
    // Add event listeners
    document.getElementById('loginFormElement').addEventListener('submit', handleLogin);
    document.getElementById('messageInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    document.getElementById('createUserForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createUser();
    });
});

// Admin Panel Functions
function toggleAdminPanel() {
    // Check if user is admin
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        alert('Access denied: Admin role required');
        return;
    }
    
    const adminPanel = document.getElementById('adminPanel');
    
    if (adminPanel) {
        if (adminPanel.style.display === 'block') {
            // Hide admin panel
            adminPanel.style.display = 'none';
            console.log('Admin panel hidden');
        } else {
            // Show admin panel (overlay on top of chat interface)
            adminPanel.style.display = 'block';
            console.log('Admin panel shown');
            
            // Load admin data when panel is first shown
            loadUsers();
            loadDocuments();
        }
    } else {
        console.error('Admin panel element not found');
    }
}

function showCreateUserModal() {
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        alert('Access denied: Admin role required');
        return;
    }
    if (window.createUserModal) {
        window.createUserModal.show();
    } else {
        const modalElement = document.getElementById('createUserModal');
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function showUploadDocumentModal() {
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        alert('Access denied: Admin role required');
        return;
    }
    if (window.uploadDocumentModal) {
        window.uploadDocumentModal.show();
    } else {
        const modalElement = document.getElementById('uploadDocumentModal');
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
    }
}

// Global function to properly close Bootstrap modals
function closeBootstrapModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;
    
    const modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
        modal.hide();
    } else {
        // Fallback: hide modal manually
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        document.body.classList.remove('modal-open');
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }
}

// Authentication functions
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            
            await loadUserInfo();
            showChatInterface();
        } else {
            const error = await response.json();
            alert('Login failed: ' + error.detail);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    }
}

async function validateToken() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            await loadUserInfo();
            showChatInterface();
        } else {
            localStorage.removeItem('authToken');
            authToken = null;
        }
    } catch (error) {
        console.error('Token validation error:', error);
        localStorage.removeItem('authToken');
        authToken = null;
    }
}

function showChatInterface() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('chatInterface').classList.remove('hidden');
    loadThreads();
}

function showLoginPage() {
    document.getElementById('chatInterface').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
}

function logout() {
    localStorage.removeItem('authToken');
    authToken = null;
    currentUser = null;
    currentThread = null;
    
    // Clear chat interface
    document.getElementById('chatInterface').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
    
    // Clear chat messages and threads
    document.getElementById('chatMessages').innerHTML = '';
    document.getElementById('threadsList').innerHTML = '';
    document.getElementById('currentThreadTitle').textContent = 'Select a thread to start chatting';
    document.getElementById('messageInput').disabled = true;
    document.getElementById('sendButton').disabled = true;
    
    // Clear forms
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
}

function updateUserInfo() {
    const userInfoElement = document.getElementById('userInfo');
    const userEmail = currentUser.email || 'Unknown';
    const userRole = currentUser.role || 'user';
    userInfoElement.textContent = `${userEmail} (${userRole})`;
}

// User and Threads functions
async function loadUserInfo() {
    try {
        // First, try to get user info from the auth endpoint
        try {
            const userResponse = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
            if (userResponse.ok) {
                const userData = await userResponse.json();
                currentUser = userData;
            } else {
                // Fallback: try to determine role from admin endpoint
                try {
            const adminResponse = await fetch(`${API_BASE}/admin/users`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (adminResponse.ok) {
                        currentUser = { role: 'admin' };
                } else {
                        currentUser = { role: 'user' };
                    }
                } catch (adminError) {
                    currentUser = { role: 'user' };
                }
            }
        } catch (error) {
            currentUser = { role: 'user' };
        }
        
        // Update user info display
        updateUserInfo();
        
        // Clear admin panel data for new user
        const adminPanel = document.getElementById('adminPanel');
        if (adminPanel) {
            adminPanel.style.display = 'none';
        }
        
        // Clear admin lists
        document.getElementById('usersList').innerHTML = '';
        document.getElementById('documentsList').innerHTML = '';
        
        // Show/hide admin elements based on role
        const adminElements = document.querySelectorAll('.admin-only');
        if (currentUser.role === 'admin' || currentUser.role === 'UserRole.ADMIN') {
            adminElements.forEach(element => {
                // Keep admin elements hidden initially, but allow them to be shown
                element.style.display = 'none';
            });
        } else {
            adminElements.forEach(element => {
                element.style.display = 'none';
            });
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

async function loadThreads() {
    try {
        console.log('Loading threads for user:', currentUser);
        
        const response = await fetch(`${API_BASE}/threads`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const threads = await response.json();
            console.log('Loaded threads from API:', threads);
            
            const threadsList = document.getElementById('threadsList');
            threadsList.innerHTML = '';
            
            threads.forEach(thread => {
                const threadItem = document.createElement('div');
                threadItem.className = 'thread-item';
                threadItem.setAttribute('data-thread-id', thread.id);
                
                // Ensure thread title is not undefined
                const threadTitle = thread.title || 'New Chat';
                const threadDate = thread.created_at ? new Date(thread.created_at).toLocaleString() : 'Unknown date';
                
                const threadHtml = `
                    <div class="thread-header">
                        <h4 class="thread-title">${threadTitle}</h4>
                        <div class="thread-actions">
                            <button class="btn-icon thread-rename-btn" onclick="event.stopPropagation(); renameThread('${thread.id}', '${threadTitle}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-icon thread-delete-btn" onclick="event.stopPropagation(); deleteThread('${thread.id}')" style="background: #ff6b6b !important; color: white !important; border: 1px solid #ff6b6b !important; padding: 6px 10px !important; border-radius: 4px !important; margin-left: 5px !important;">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <p class="thread-date">${threadDate}</p>
                `;
                
                threadItem.innerHTML = threadHtml;
                threadItem.addEventListener('click', () => loadThreadMessages(thread.id));
                threadsList.appendChild(threadItem);
            });
            
            // If no current thread is selected, select the first one
            if (threads.length > 0 && !currentThread) {
                loadThreadMessages(threads[0].id);
            }
        } else {
            const error = await response.json();
            console.error('Failed to load threads:', error);
            alert('Failed to load threads: ' + error.detail);
        }
    } catch (error) {
        console.error('Error loading threads:', error);
        alert('Error loading threads. Please try again.');
    }
}

async function createNewThread() {
    try {
        console.log('Creating new thread...');
        const response = await fetch(`${API_BASE}/threads`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            const newThread = await response.json();
            console.log('New thread created:', newThread);
            await loadThreads();
            loadThreadMessages(newThread.id);
        } else {
            const error = await response.json();
            console.error('Failed to create thread:', error);
            alert('Failed to create new thread: ' + error.detail);
        }
    } catch (error) {
        console.error('Error creating new thread:', error);
        alert('Error creating new thread. Please try again.');
    }
}

async function loadThreadMessages(threadId) {
    try {
        currentThread = threadId;
        const messagesList = document.getElementById('chatMessages');
        
        const response = await fetch(`${API_BASE}/chat/${threadId}/messages`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const messages = await response.json();
            console.log('Loaded messages:', messages);
            
            messagesList.innerHTML = '';
            
            messages.forEach(msg => {
                const messageElement = createMessageElement(msg);
                messagesList.appendChild(messageElement);
            });
            
            // Enable input fields
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
            
            // Highlight active thread
            document.querySelectorAll('.thread-item').forEach(item => {
                if (item.getAttribute('data-thread-id') === threadId) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            
            // Update thread title
            updateThreadTitle(threadId);
            
            // Scroll to bottom
            messagesList.scrollTop = messagesList.scrollHeight;
        } else {
            console.error('Failed to load messages');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function createMessageElement(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;
    
    // Ensure content is not undefined
    const content = msg.content || '';
    
    // Robust date parsing
    let timeString = 'Just now';
    try {
        if (msg.created_at) {
            const date = new Date(msg.created_at);
            if (!isNaN(date.getTime())) {
                timeString = date.toLocaleTimeString();
            }
        }
    } catch (error) {
        console.error('Error parsing date:', error);
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${content}</p>
            <small class="message-time">${timeString}</small>
        </div>
    `;
    
    return messageDiv;
}

function updateThreadTitle(threadId) {
    const threadItem = document.querySelector(`[data-thread-id="${threadId}"]`);
    if (threadItem) {
        const titleElement = threadItem.querySelector('.thread-title');
        if (titleElement && titleElement.textContent) {
            document.getElementById('currentThreadTitle').textContent = titleElement.textContent;
        } else {
            // Fallback if title is missing
            document.getElementById('currentThreadTitle').textContent = `Chat ID: ${threadId.substring(0, 8)}...`;
        }
    }
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || !currentThread) return;
    
    // Clear input
    messageInput.value = '';
    
    // Create temporary user message
    const tempUserMessage = {
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
    };
    
    // Append user message immediately
    const messagesList = document.getElementById('chatMessages');
    const userMessageElement = createMessageElement(tempUserMessage);
    messagesList.appendChild(userMessageElement);
    messagesList.scrollTop = messagesList.scrollHeight;
    
    try {
        const response = await fetch(`${API_BASE}/chat/${currentThread}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message: message })
        });
        
        if (response.ok) {
            const chatResponse = await response.json();
            console.log('Chat response:', chatResponse);
            
            // Replace temporary user message with real one
            const realUserMessage = {
                role: 'user',
                content: message,
                created_at: new Date().toISOString()
            };
            const realUserElement = createMessageElement(realUserMessage);
            messagesList.replaceChild(realUserElement, userMessageElement);
            
            // Create and append assistant message
            const assistantMessage = {
                role: 'assistant',
                content: chatResponse.message,
                created_at: new Date().toISOString()
            };
            const assistantElement = createMessageElement(assistantMessage);
            messagesList.appendChild(assistantElement);
            
            // Scroll to bottom
            messagesList.scrollTop = messagesList.scrollHeight;
        } else {
            console.error('Failed to send message');
            alert('Failed to send message. Please try again.');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Error sending message. Please try again.');
    }
}

async function renameThread(threadId, currentTitle) {
    const newTitle = prompt('Enter new thread title:', currentTitle);
    
    if (!newTitle || newTitle.trim() === '') {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/threads/${threadId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ title: newTitle.trim() })
        });
        
        if (response.ok) {
            // Update the thread title in the sidebar immediately
            const threadItem = document.querySelector(`[data-thread-id="${threadId}"]`);
            if (threadItem) {
                const titleElement = threadItem.querySelector('.thread-title');
                if (titleElement) {
                    titleElement.textContent = newTitle.trim();
                }
            }
            
            // Update the chat header title if this is the current thread
            const currentThreadTitleElement = document.getElementById('currentThreadTitle');
            if (currentThreadTitleElement && currentThread === threadId) {
                currentThreadTitleElement.textContent = newTitle.trim();
            }
            
            // Refresh threads to ensure consistency and proper ordering
            await loadThreads();
            
            console.log('Thread renamed successfully');
        } else {
            console.error('Failed to rename thread');
            alert('Failed to rename thread');
        }
    } catch (error) {
        console.error('Error renaming thread:', error);
        alert('Error renaming thread');
    }
}

async function deleteThread(threadId) {
    if (!confirm('Are you sure you want to delete this thread?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/threads/${threadId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            console.log('Thread deleted successfully');
            await loadThreads();
            
            // If the deleted thread was the current thread, clear the chat
            if (currentThread === threadId) {
                currentThread = null;
                document.getElementById('chatMessages').innerHTML = '';
                document.getElementById('currentThreadTitle').textContent = 'Select a thread to start chatting';
                document.getElementById('messageInput').disabled = true;
                document.getElementById('sendButton').disabled = true;
            }
        } else {
            console.error('Failed to delete thread');
            alert('Failed to delete thread');
        }
    } catch (error) {
        console.error('Error deleting thread:', error);
        alert('Error deleting thread');
    }
}

async function deleteMessage(messageId) {
    try {
        const response = await fetch(`${API_BASE}/chat/messages/${messageId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            console.log('Message deleted successfully');
            // Reload messages to reflect the change
            if (currentThread) {
                await loadThreadMessages(currentThread);
            }
        } else {
            console.error('Failed to delete message');
            alert('Failed to delete message');
        }
    } catch (error) {
        console.error('Error deleting message:', error);
        alert('Error deleting message');
    }
}

// Admin functions
async function loadUsers() {
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const users = await response.json();
        
        const usersList = document.getElementById('usersList');
        usersList.innerHTML = '';
        
        users.forEach(user => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item mb-3 p-3 border rounded';
            
            const userInfoHtml = `
                <div class="user-info d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <span class="fw-bold">${user.email}</span> 
                        <span class="badge bg-${user.role === 'admin' ? 'danger' : 'primary'} ms-2">${user.role}</span>
                        <br>
                        <small class="text-muted">Created: ${new Date(user.created_at).toLocaleString()}</small>
                    </div>
                    <div class="user-actions">
                        <button class="btn btn-sm btn-warning me-2" onclick="toggleUserStatus('${user.id}', ${user.is_active})">
                            ${user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.id}')">Delete</button>
                    </div>
                </div>
            `;
            
            const chatThreadsHtml = `
                <div class="chat-threads-section">
                    <button class="btn btn-sm btn-outline-info mb-2" onclick="toggleUserChatThreads('${user.id}', this)">
                        <i class="fas fa-chevron-down"></i> Show Chat Threads
                    </button>
                    <div id="chat-threads-${user.id}" class="chat-threads-content" style="display: none;">
                        <div class="text-center">
                            <div class="spinner-border spinner-border-sm" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            userItem.innerHTML = userInfoHtml + chatThreadsHtml;
            usersList.appendChild(userItem);
        });
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function toggleUserChatThreads(userId, buttonElement) {
    const threadsContent = document.getElementById(`chat-threads-${userId}`);
    const isVisible = threadsContent.style.display !== 'none';
    
    if (isVisible) {
        // Hide threads
        threadsContent.style.display = 'none';
        buttonElement.innerHTML = '<i class="fas fa-chevron-down"></i> Show Chat Threads';
    } else {
        // Show threads
        threadsContent.style.display = 'block';
        buttonElement.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Chat Threads';
        
        // Load user chat threads
        await loadUserChatThreads(userId, threadsContent);
    }
}

async function loadUserChatThreads(userId, containerElement) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/chat-history`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const chatHistory = await response.json();
            displayUserChatThreads(chatHistory, containerElement);
        } else {
            const error = await response.json();
            containerElement.innerHTML = `<p class="text-danger">Failed to load chat history: ${error.detail}</p>`;
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
        containerElement.innerHTML = '<p class="text-danger">Failed to load chat history. Please try again.</p>';
    }
}

function displayUserChatThreads(chatHistory, containerElement) {
    if (chatHistory.length === 0) {
        containerElement.innerHTML = '<p class="text-muted">No chat threads found for this user.</p>';
        return;
    }
    
    let html = '<div class="chat-threads-list">';
    
    chatHistory.forEach(thread => {
        html += `
            <div class="thread-item-admin mb-3 p-3 border rounded bg-light">
                <div class="thread-header-admin d-flex justify-content-between align-items-center mb-2">
                    <h6 class="thread-title-admin mb-1">${thread.title || 'Untitled Thread'}</h6>
                    <small class="text-muted">${new Date(thread.created_at).toLocaleString()}</small>
                </div>
                <div class="messages-preview-admin">
        `;
        
        if (thread.messages && thread.messages.length > 0) {
            // Show ALL messages instead of just first 3
            thread.messages.forEach(msg => {
                const roleClass = msg.role === 'user' ? 'text-primary' : 'text-success';
                const roleIcon = msg.role === 'user' ? '👤' : '🤖';
                const messageContent = msg.content.length > 150 ? msg.content.substring(0, 150) + '...' : msg.content;
                
                html += `
                    <div class="message-preview-admin ${roleClass} mb-2 p-2 border rounded" style="background-color: ${msg.role === 'user' ? '#e3f2fd' : '#f1f8e9'}">
                        <div class="d-flex align-items-center mb-1">
                            <strong class="me-2">${roleIcon} ${msg.role === 'user' ? 'User' : 'Assistant'}</strong>
                            <small class="text-muted">${new Date(msg.created_at).toLocaleString()}</small>
                        </div>
                        <div class="message-content-full">
                            ${messageContent}
                        </div>
                    </div>
                `;
            });
            
            html += `<div class="text-center mt-2"><small class="text-muted">Total: ${thread.messages.length} messages</small></div>`;
        } else {
            html += '<small class="text-muted">No messages in this thread</small>';
        }
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    containerElement.innerHTML = html;
}

async function createUser() {
    const email = document.getElementById('createEmail').value;
    const password = document.getElementById('createPassword').value;
    
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        alert('Access denied: Admin role required');
        return;
    }
    
    if (!email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ email, password, role: 'user' })
        });
        
        if (response.ok) {
            alert('User created successfully!');
            document.getElementById('createUserForm').reset();
            closeBootstrapModal('createUserModal');
            loadUsers();
        } else {
            const error = await response.json();
            alert('Failed to create user: ' + error.detail);
        }
    } catch (error) {
        console.error('Error creating user:', error);
        alert('Failed to create user. Please try again.');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            alert('User deleted successfully!');
            loadUsers();
        } else {
            const error = await response.json();
            alert('Failed to delete user: ' + error.detail);
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Failed to delete user. Please try again.');
    }
}

async function toggleUserStatus(userId, currentStatus) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}/toggle-status`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            alert('User status updated successfully!');
            loadUsers();
        } else {
            const error = await response.json();
            alert('Failed to update user status: ' + error.detail);
        }
    } catch (error) {
        console.error('Error updating user status:', error);
        alert('Failed to update user status. Please try again.');
    }
}

async function loadDocuments() {
    if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'UserRole.ADMIN')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/documents`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const documents = await response.json();
        
        const documentsList = document.getElementById('documentsList');
        documentsList.innerHTML = '';
        
        documents.forEach(doc => {
            const docItem = document.createElement('div');
            docItem.className = 'document-item mb-3 p-3 border rounded';
            docItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${doc.filename}</h6>
                        <small class="text-muted">Uploaded: ${new Date(doc.uploaded_at).toLocaleString()}</small>
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="deleteDocument('${doc.id}')">Delete</button>
                </div>
            `;
            documentsList.appendChild(docItem);
        });
        
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

async function uploadDocument() {
    const fileInput = document.getElementById('documentFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress bar
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const uploadStatus = document.getElementById('uploadStatus');
    
    progressDiv.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.textContent = '0%';
    uploadStatus.textContent = 'Starting upload...';
    
    try {
        const response = await fetch(`${API_BASE}/admin/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            body: formData
        });
        
        if (response.ok) {
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';
            uploadStatus.textContent = 'Upload completed successfully!';
            setTimeout(() => {
                alert('Document uploaded successfully!');
                document.getElementById('uploadDocumentForm').reset();
                progressDiv.style.display = 'none';
                closeBootstrapModal('uploadDocumentModal');
                loadDocuments();
            }, 1000);
        } else {
            const error = await response.json();
            uploadStatus.textContent = 'Upload failed: ' + error.detail;
            setTimeout(() => {
                alert('Failed to upload document: ' + error.detail);
                progressDiv.style.display = 'none';
            }, 2000);
        }
    } catch (error) {
        console.error('Error uploading document:', error);
        uploadStatus.textContent = 'Upload failed. Please try again.';
        setTimeout(() => {
            alert('Failed to upload document. Please try again.');
            progressDiv.style.display = 'none';
        }, 2000);
    }
}

async function deleteDocument(documentId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/documents/${documentId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            alert('Document deleted successfully!');
            loadDocuments();
        } else {
            const error = await response.json();
            alert('Failed to delete document: ' + error.detail);
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        alert('Failed to delete document. Please try again.');
    }
}
