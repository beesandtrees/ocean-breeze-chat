const textarea = document.querySelector('.message-input');
const sendButton = document.querySelector('.submit-button');
const chatHistory = document.getElementById("chatHistory");
const chatBody = document.getElementById('chatBody');

function formatMessage(message) {
    // Replace code blocks
    message = message.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'plaintext';
        return `<pre><code class="language-${language}">${code.trim()}</code></pre>`;
    });

    // Replace inline code
    message = message.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Replace lists
    message = message.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    message = message.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Replace numbered lists
    message = message.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
    message = message.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');

    // Replace blockquotes
    message = message.replace(/^\s*>\s*(.+)$/gm, '<blockquote>$1</blockquote>');

    // Replace bold text
    message = message.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Replace italic text
    message = message.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Replace line breaks with <br> tags
    message = message.replace(/\n/g, '<br>');

    return message;
}

const setLoading = isLoading => {
    var botLoading = document.getElementById('bot-loading');
    botLoading.style.display = isLoading ? 'flex' : 'none';
}

// Get chat type from URL path (e.g., /bedrock -> bedrock, / -> bedrock, /ocean -> ocean)
const getChatType = () => {
    const path = window.location.pathname;
    if (path === '/') return 'bedrock';
    return path.substring(1) || 'bedrock';
};

async function sendMessage() {
    const message = textarea.value.trim();
    if (message) {
        // Create and append user message
        const messageDiv = document.createElement("div");
        messageDiv.className = "chat-message user-message";
        messageDiv.innerHTML = formatMessage(message);
        chatHistory.appendChild(messageDiv);
        
        // Clear input and disable while waiting
        textarea.value = '';
        textarea.disabled = true;
        sendButton.disabled = true;
        setLoading(true);
        
        try {
            // Send POST request
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    chat_type: getChatType()
                })
            });
            
            const data = await response.json();
            
            // Create and append assistant message
            const assistantDiv = document.createElement("div");
            assistantDiv.className = "chat-message ai-response";
            assistantDiv.innerHTML = formatMessage(data.response);
            chatHistory.appendChild(assistantDiv);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            // Re-enable input and hide loading
            textarea.disabled = false;
            sendButton.disabled = false;
            setLoading(false);
            textarea.focus();
        }
        
        // Scroll to bottom
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

// Handle Enter key
textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Handle button click
sendButton.addEventListener('click', sendMessage);

// Auto-resize textarea as user types
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
}); 