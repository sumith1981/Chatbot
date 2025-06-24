document.addEventListener('DOMContentLoaded', () => {
    // Navigation with smooth transitions
    const navItems = document.querySelectorAll('nav ul li');
    const pages = document.querySelectorAll('.page');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Add click animation
            item.style.transform = 'scale(0.95)';
            setTimeout(() => {
                item.style.transform = '';
            }, 150);

            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            pages.forEach(page => {
                page.classList.remove('active');
                page.style.animation = 'fadeOut 0.3s ease-out';
            });

            // Add active class to clicked item
            item.classList.add('active');
            const pageId = item.getAttribute('data-page');
            const targetPage = document.getElementById(`${pageId}-page`);
            targetPage.classList.add('active');
            targetPage.style.animation = 'slideInUp 0.5s ease-out';

            // If history page is selected, load history
            if (pageId === 'history') {
                setTimeout(() => loadHistory(), 300);
            }
            
            // If learning page is selected, load learning data
            if (pageId === 'learning') {
                setTimeout(() => loadLearningData(), 300);
            }
        });
    });

    // Chat functionality with enhanced animations
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    const suggestionsContainer = document.getElementById('suggestions-container');
    const suggestionsGrid = document.getElementById('suggestions-grid');

    function addMessage(message, isUser = false, isLearning = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user' : 'bot');
        
        if (isLearning) {
            messageDiv.classList.add('learning');
        }
        
        // Create message structure
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-${isUser ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">
                    ${message}
                    ${isLearning ? '<div class="learning-indicator"><i class="fas fa-brain"></i> Learning from this question</div>' : ''}
                </div>
                <div class="message-time">${getCurrentTime()}</div>
            </div>
        `;

        // Add animation delay for staggered effect
        messageDiv.style.animationDelay = '0.1s';
        chatMessages.appendChild(messageDiv);
        
        // Smooth scroll to bottom
        setTimeout(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    function showTypingIndicator() {
        typingIndicator.style.display = 'flex';
        typingIndicator.style.animation = 'slideInUp 0.3s ease-out';
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    function hideTypingIndicator() {
        typingIndicator.style.animation = 'slideOutDown 0.3s ease-out';
        setTimeout(() => {
            typingIndicator.style.display = 'none';
        }, 300);
    }

    function showSuggestions(suggestions) {
        suggestionsGrid.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.classList.add('suggestion-button');
            button.textContent = suggestion;
            button.addEventListener('click', () => {
                // Add user message showing the selected question
                addMessage(suggestion, true);
                
                // Hide suggestions
                hideSuggestions();
                
                // Send the suggestion as a message
                sendSuggestionMessage(suggestion);
            });
            suggestionsGrid.appendChild(button);
        });
        
        suggestionsContainer.style.display = 'block';
        suggestionsContainer.style.animation = 'slideInUp 0.3s ease-out';
        
        // Scroll to suggestions
        setTimeout(() => {
            suggestionsContainer.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }

    function hideSuggestions() {
        suggestionsContainer.style.animation = 'slideOutDown 0.3s ease-out';
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 300);
    }

    async function sendSuggestionMessage(suggestion) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: suggestion }),
            });

            const data = await response.json();
            
            // Add bot response
            setTimeout(() => {
                addMessage(data.response, false, data.is_learning);
                
                // Show suggestions if available
                if (data.suggestions && data.suggestions.length > 0) {
                    showSuggestions(data.suggestions);
                } else {
                    hideSuggestions();
                }
            }, 500 + Math.random() * 1000);
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request. Please try again.');
        }
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            // Add user message with animation
            addMessage(message, true);
            userInput.value = '';
            
            // Hide suggestions when user sends a new message
            hideSuggestions();
            
            // Disable input while processing
            userInput.disabled = true;
            sendButton.disabled = true;
            sendButton.style.opacity = '0.5';

            // Show typing indicator
            showTypingIndicator();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });

                const data = await response.json();
                
                // Hide typing indicator
                hideTypingIndicator();
                
                // Add bot response with delay for realistic typing effect
                setTimeout(() => {
                    addMessage(data.response, false, data.is_learning);
                    
                    // Show suggestions if available
                    if (data.suggestions && data.suggestions.length > 0) {
                        showSuggestions(data.suggestions);
                    } else {
                        hideSuggestions();
                    }
                    
                    // Re-enable input
                    userInput.disabled = false;
                    sendButton.disabled = false;
                    sendButton.style.opacity = '1';
                    userInput.focus();
                }, 500 + Math.random() * 1000); // Random delay for natural feel

                // Special goodbye message
                if (data.response.toLowerCase().includes('goodbye') || 
                    data.response.toLowerCase().includes('bye')) {
                    setTimeout(() => {
                        addMessage('Thank you for chatting with me. Have a great day! 👋');
                    }, 2000);
                }
            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addMessage('Sorry, there was an error processing your message. Please try again.');
                
                // Re-enable input
                userInput.disabled = false;
                sendButton.disabled = false;
                sendButton.style.opacity = '1';
            }
        }
    }

    // Enhanced button interactions
    sendButton.addEventListener('click', () => {
        sendButton.style.transform = 'scale(0.95)';
        setTimeout(() => {
            sendButton.style.transform = '';
        }, 150);
        sendMessage();
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Input focus effects
    userInput.addEventListener('focus', () => {
        userInput.parentElement.style.transform = 'scale(1.02)';
    });

    userInput.addEventListener('blur', () => {
        userInput.parentElement.style.transform = 'scale(1)';
    });

    // Load chat history with animations
    async function loadHistory() {
        const historyContainer = document.getElementById('history-container');
        historyContainer.innerHTML = '<div class="loading">Loading history...</div>';

        try {
            const response = await fetch('/history');
            const history = await response.json();

            historyContainer.innerHTML = '';
            
            if (history.length === 0) {
                historyContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <h3>No chat history yet</h3>
                        <p>Start a conversation to see your chat history here!</p>
                    </div>
                `;
                return;
            }

            history.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.classList.add('history-item');
                historyItem.style.animationDelay = `${index * 0.1}s`;
                historyItem.innerHTML = `
                    <div class="history-content">
                        <div class="history-user">
                            <i class="fas fa-user"></i>
                            <span>${item.user_input}</span>
                        </div>
                        <div class="history-bot">
                            <i class="fas fa-robot"></i>
                            <span>${item.chatbot_response}</span>
                        </div>
                        <div class="history-time">
                            <i class="fas fa-clock"></i>
                            <span>${item.timestamp}</span>
                        </div>
                    </div>
                `;
                historyContainer.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Error loading history:', error);
            historyContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error loading chat history</h3>
                    <p>Please try again later.</p>
                </div>
            `;
        }
    }

    // Load learning data with animations
    async function loadLearningData() {
        const learningContainer = document.getElementById('learning-container');
        learningContainer.innerHTML = '<div class="loading">Loading learning data...</div>';

        try {
            const response = await fetch('/learning-data');
            const learningData = await response.json();

            learningContainer.innerHTML = '';
            
            if (learningData.length === 0) {
                learningContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-brain"></i>
                        <h3>No learning data yet</h3>
                        <p>I haven't encountered any questions I couldn't answer yet. Keep asking me questions!</p>
                    </div>
                `;
                return;
            }

            // Sort by count (most asked questions first)
            learningData.sort((a, b) => b.count - a.count);

            learningData.forEach((item, index) => {
                const learningItem = document.createElement('div');
                learningItem.classList.add('learning-item');
                learningItem.style.animationDelay = `${index * 0.1}s`;
                learningItem.innerHTML = `
                    <div class="learning-question">
                        <div class="question-header">
                            <i class="fas fa-question-circle"></i>
                            <span class="question-text">${item.question}</span>
                            <span class="question-count">Asked ${item.count} time${item.count > 1 ? 's' : ''}</span>
                        </div>
                        <div class="question-time">
                            <i class="fas fa-clock"></i>
                            <span>Last asked: ${item.timestamp}</span>
                        </div>
                    </div>
                `;
                learningContainer.appendChild(learningItem);
            });
        } catch (error) {
            console.error('Error loading learning data:', error);
            learningContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error loading learning data</h3>
                    <p>Please try again later.</p>
                </div>
            `;
        }
    }

    // Add some CSS animations dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-20px); }
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 16px;
        }
        
        .empty-state, .error-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .empty-state i, .error-state i {
            font-size: 48px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-state h3, .error-state h3 {
            margin-bottom: 10px;
            color: #1a1a2e;
        }
        
        .history-content {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .history-user, .history-bot, .history-time {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .history-user i {
            color: #4ade80;
        }
        
        .history-bot i {
            color: #667eea;
        }
        
        .history-time i {
            color: #999;
            font-size: 12px;
        }
        
        .history-time {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
    `;
    document.head.appendChild(style);

    // Auto-focus on input when page loads
    userInput.focus();

    // Add welcome animation
    setTimeout(() => {
        const welcomeMessage = document.querySelector('.message.bot');
        if (welcomeMessage) {
            welcomeMessage.style.animation = 'slideInUp 0.6s ease-out';
        }
    }, 500);
}); 