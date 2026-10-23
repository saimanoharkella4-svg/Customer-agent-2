const loginOverlay = document.getElementById('login-overlay');
const loginForm = document.getElementById('login-form');
const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const typingIndicator = document.getElementById('typing-indicator');
const chatContainer = document.getElementById('chat-container');
const openLoginBtn = document.getElementById('open-login-btn');
const closeLoginBtn = document.getElementById('close-login-btn');
const userStatus = document.getElementById('user-status');

// Chat history to maintain context
let chatHistory = [];
let loggedInCustomer = null;
let loggedInPhone = null;

openLoginBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'flex';
});

closeLoginBtn.addEventListener('click', () => {
    loginOverlay.style.display = 'none';
});

loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    loggedInCustomer = document.getElementById('customer-name').value.trim();
    loggedInPhone = document.getElementById('phone-number').value.trim();
    
    if (loggedInCustomer && loggedInPhone) {
        loginOverlay.style.display = 'none';
        userStatus.innerText = `Logged in as ${loggedInCustomer}`;
        openLoginBtn.style.display = 'none'; // hide login button
        userInput.focus();
        
        appendMessage('bot', `Welcome ${loggedInCustomer}! I am fetching your account details and order history securely... ✨`);
        typingIndicator.classList.remove('hidden');
        
        // Automatically ask the AI for the customer's full details and order history behind the scenes
        chatHistory.push({
            "role": "user",
            "content": "I have just logged in. Please greet me, provide a full summary of my customer profile details, and list all my recent orders with their statuses."
        });
        
        const combinedInput = chatHistory.map(msg => `${msg.role}: ${msg.content}`).join('\n');
        
        fetchAgentResponse(combinedInput).then(responseText => {
            typingIndicator.classList.add('hidden');
            appendMessage('bot', responseText);
            chatHistory.push({
                "role": "assistant",
                "content": responseText
            });
        }).catch(error => {
            typingIndicator.classList.add('hidden');
            appendMessage('bot', `⚠️ Error: ${error.message}`);
        });
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to UI
    appendMessage('user', message);
    userInput.value = '';
    
    // Add user message to history payload
    chatHistory.push({
        "role": "user",
        "content": message
    });

    // Show typing indicator
    typingIndicator.classList.remove('hidden');
    scrollToBottom();

    try {
        const combinedInput = chatHistory.map(msg => `${msg.role}: ${msg.content}`).join('\n');
        const responseText = await fetchAgentResponse(combinedInput);
        
        typingIndicator.classList.add('hidden');
        appendMessage('bot', responseText);
        
        chatHistory.push({
            "role": "assistant",
            "content": responseText
        });
        
    } catch (error) {
        typingIndicator.classList.add('hidden');
        appendMessage('bot', `⚠️ Error: ${error.message}`);
    }
});

function appendMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    
    let formattedText = escapeHTML(text)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/```(?:html|css|js|javascript|python)?\n([\s\S]*?)```/gi, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n(?![^<]*<\/pre>)/g, '<br>');
        
    contentDiv.innerHTML = formattedText;
    
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag])
    );
}

function scrollToBottom() {
    chatBox.scrollTo({
        top: chatBox.scrollHeight,
        behavior: 'smooth'
    });
}

async function fetchAgentResponse(inputText) {
    const response = await fetch('http://localhost:8005/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer super_secret_token_123'
        },
        body: JSON.stringify({
            input: inputText,
            customer_name: loggedInCustomer,
            phone_number: loggedInPhone
        })
    });

    if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to communicate with RAG backend');
    }

    const data = await response.json();
    return data.output;
}

