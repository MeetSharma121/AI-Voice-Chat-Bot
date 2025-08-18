/**
 * EMMA Healthcare Chatbot - Chat Interface JavaScript
 * Handles chat functionality, voice recording, and WebSocket communication
 */

class EMMAChat {
    constructor() {
        this.socket = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.sessionId = this.generateSessionId();
        this.conversationHistory = [];
        
        this.initializeElements();
        this.initializeSocket();
        this.bindEvents();
        this.loadConversationHistory();
        
        console.log('EMMA Chat initialized');
    }
    
    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.chatMessages = document.getElementById('chat-messages');
        this.voiceBtn = document.getElementById('voice-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.helpBtn = document.getElementById('help-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.loadingSpinner = document.getElementById('loading-spinner');
        this.connectionStatus = document.getElementById('connection-status');
        this.statusIndicator = document.querySelector('.status-indicator');
    }
    
    initializeSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.updateConnectionStatus('Connected', 'status-online');
                console.log('Connected to server');
            });
            
            this.socket.on('disconnect', () => {
                this.updateConnectionStatus('Disconnected', 'status-offline');
                console.log('Disconnected from server');
            });
            
            this.socket.on('chat_response', (data) => {
                this.handleChatResponse(data);
            });
            
            this.socket.on('voice_response', (data) => {
                this.handleVoiceResponse(data);
            });
            
            this.socket.on('error', (data) => {
                this.showError(data.error || 'An error occurred');
            });
            
        } catch (error) {
            console.error('Socket initialization failed:', error);
            this.updateConnectionStatus('Connection Failed', 'status-offline');
        }
    }
    
    bindEvents() {
        // Send button click
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Voice button click
        this.voiceBtn.addEventListener('click', () => {
            this.toggleVoiceRecording();
        });
        
        // Clear button click
        this.clearBtn.addEventListener('click', () => {
            this.clearConversation();
        });
        
        // Help button click
        this.helpBtn.addEventListener('click', () => {
            this.showHelp();
        });
        
        // Input focus for better UX
        this.messageInput.addEventListener('focus', () => {
            this.messageInput.style.borderColor = '#007bff';
        });
        
        this.messageInput.addEventListener('blur', () => {
            this.messageInput.style.borderColor = '#e9ecef';
        });
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send message via WebSocket if available
        if (this.socket && this.socket.connected) {
            this.socket.emit('chat_message', {
                message: message,
                session_id: this.sessionId
            });
        } else {
            // Fallback to HTTP API
            this.sendMessageViaHTTP(message);
        }
        
        // Store in conversation history
        this.conversationHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString()
        });
    }
    
    async sendMessageViaHTTP(message) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleChatResponse(data);
            } else {
                this.showError(data.error || 'Failed to send message');
            }
            
        } catch (error) {
            console.error('HTTP request failed:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideTypingIndicator();
        }
    }
    
    handleChatResponse(data) {
        this.hideTypingIndicator();
        
        if (data.response) {
            this.addMessage('assistant', data.response);
            
            // Store in conversation history
            this.conversationHistory.push({
                role: 'assistant',
                content: data.response,
                timestamp: data.timestamp || new Date().toISOString()
            });
            
            // Save conversation history
            this.saveConversationHistory();
            
            // Convert response to speech if voice is enabled
            if (this.isVoiceEnabled()) {
                this.speakResponse(data.response);
            }
        }
    }
    
    handleVoiceResponse(data) {
        this.hideTypingIndicator();
        
        if (data.transcribed_text) {
            this.addMessage('user', data.transcribed_text, true);
        }
        
        if (data.response) {
            this.addMessage('assistant', data.response);
            
            // Store in conversation history
            this.conversationHistory.push({
                role: 'assistant',
                content: data.response,
                timestamp: new Date().toISOString()
            });
            
            // Save conversation history
            this.saveConversationHistory();
        }
    }
    
    addMessage(role, content, isVoice = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        if (isVoice) {
            const voiceIcon = document.createElement('i');
            voiceIcon.className = 'fas fa-microphone me-2';
            voiceIcon.style.fontSize = '0.8em';
            messageContent.insertBefore(voiceIcon, messageContent.firstChild);
        }
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // Add animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        messageDiv.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 100);
    }
    
    async toggleVoiceRecording() {
        if (this.isRecording) {
            this.stopVoiceRecording();
        } else {
            await this.startVoiceRecording();
        }
    }
    
    async startVoiceRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processVoiceRecording();
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.voiceBtn.classList.add('recording');
            this.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.voiceBtn.title = 'Click to stop recording';
            
            console.log('Voice recording started');
            
        } catch (error) {
            console.error('Failed to start voice recording:', error);
            this.showError('Microphone access denied. Please allow microphone access and try again.');
        }
    }
    
    stopVoiceRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            this.voiceBtn.classList.remove('recording');
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            this.voiceBtn.title = 'Click to speak';
            
            console.log('Voice recording stopped');
        }
    }
    
    async processVoiceRecording() {
        if (this.audioChunks.length === 0) return;
        
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Show loading spinner
        this.showLoadingSpinner();
        
        try {
            // Send audio for transcription
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('session_id', this.sessionId);
            
            const response = await fetch('/api/voice/transcribe', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleVoiceResponse(data);
            } else {
                this.showError(data.error || 'Failed to transcribe audio');
            }
            
        } catch (error) {
            console.error('Voice processing failed:', error);
            this.showError('Failed to process voice input. Please try again.');
        } finally {
            this.hideLoadingSpinner();
        }
    }
    
    async speakResponse(text) {
        try {
            const response = await fetch('/api/voice/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });
            
            const data = await response.json();
            
            if (response.ok && data.audio_data) {
                // Convert base64 audio data to audio element
                const audio = new Audio(`data:audio/wav;base64,${data.audio_data}`);
                audio.play();
            }
            
        } catch (error) {
            console.error('Speech synthesis failed:', error);
        }
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    showLoadingSpinner() {
        this.loadingSpinner.style.display = 'block';
    }
    
    hideLoadingSpinner() {
        this.loadingSpinner.style.display = 'none';
    }
    
    updateConnectionStatus(status, statusClass) {
        this.connectionStatus.textContent = status;
        this.statusIndicator.className = `status-indicator ${statusClass}`;
    }
    
    clearConversation() {
        if (confirm('Are you sure you want to clear the conversation? This action cannot be undone.')) {
            // Clear chat messages
            this.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h3><i class="fas fa-comments me-2"></i>Welcome to EMMA</h3>
                    <p>I'm here to help with healthcare administrative tasks, appointment booking, and general information. How can I assist you today?</p>
                    <p><small>You can type your message or use voice commands below.</small></p>
                </div>
            `;
            
            // Clear conversation history
            this.conversationHistory = [];
            this.saveConversationHistory();
            
            // Reset session
            this.sessionId = this.generateSessionId();
            
            console.log('Conversation cleared');
        }
    }
    
    showHelp() {
        const helpMessage = `
            <h4>How to use EMMA:</h4>
            <ul>
                <li><strong>Type your message</strong> in the text box and press Enter or click Send</li>
                <li><strong>Use voice commands</strong> by clicking the microphone button</li>
                <li><strong>Clear conversation</strong> using the trash button</li>
                <li><strong>Get help</strong> anytime by clicking the question mark</li>
            </ul>
            <h4>What I can help with:</h4>
            <ul>
                <li>Appointment booking and scheduling</li>
                <li>General healthcare information</li>
                <li>NHS guidelines and policies</li>
                <li>Administrative questions</li>
            </ul>
            <p><strong>Note:</strong> For medical concerns, please consult with a healthcare professional.</p>
        `;
        
        this.addMessage('assistant', helpMessage);
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        this.chatMessages.appendChild(errorDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    isVoiceEnabled() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }
    
    saveConversationHistory() {
        try {
            localStorage.setItem('emma_conversation_history', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.error('Failed to save conversation history:', error);
        }
    }
    
    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('emma_conversation_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
                
                // Optionally restore recent messages (last 5)
                const recentMessages = this.conversationHistory.slice(-5);
                recentMessages.forEach(msg => {
                    this.addMessage(msg.role, msg.content);
                });
            }
        } catch (error) {
            console.error('Failed to load conversation history:', error);
        }
    }
    
    // Utility methods
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }
    
    sanitizeInput(input) {
        return input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.emmaChat = new EMMAChat();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, stop any ongoing voice recording
        if (window.emmaChat && window.emmaChat.isRecording) {
            window.emmaChat.stopVoiceRecording();
        }
    }
});

// Handle beforeunload to save conversation
window.addEventListener('beforeunload', () => {
    if (window.emmaChat) {
        window.emmaChat.saveConversationHistory();
    }
}); 