"""
Flask Web Interface (Alternative to Streamlit)
Developer 3: Build a Flask-based web UI here

To run: python frontend/flask_app.py
"""

from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_agent import ContextAwareAgent
from config import FLASK_PORT, FLASK_DEBUG
from utils.helpers import log_info, log_error

# Initialize Flask app
app = Flask(__name__)
agent = ContextAwareAgent()

# Store conversation history (in production, use a database)
conversations = {}


@app.route('/')
def index():
    """
    Render the main chat interface
    
    Developer 3 TODO:
        1. Create an HTML template (templates/index.html)
        2. Design a clean chat interface
        3. Add JavaScript for real-time interaction
        4. Style with CSS
    """
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """
    Handle user queries
    
    Developer 3 TODO:
        1. Get query from request
        2. Call agent to process query
        3. Return response as JSON
        4. Handle errors gracefully
    """
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        session_id = data.get('session_id', 'default')
        
        if not user_query:
            return jsonify({'error': 'No query provided'}), 400
        
        log_info(f"Received query: {user_query}")
        
        # Process query with agent
        response = agent.process_query(user_query)
        
        # Store in conversation history
        if session_id not in conversations:
            conversations[session_id] = []
        
        conversations[session_id].append({
            'query': user_query,
            'response': response
        })
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    
    except Exception as e:
        log_error("Error processing query", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Get conversation history for a session"""
    history = conversations.get(session_id, [])
    return jsonify({'history': history})


@app.route('/api/clear/<session_id>', methods=['POST'])
def clear_history(session_id):
    """Clear conversation history for a session"""
    if session_id in conversations:
        conversations[session_id] = []
    agent.reset_conversation()
    return jsonify({'status': 'cleared'})


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'available_tools': agent.get_available_tools()
    })


# Developer 3: Create this template file
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Context-Aware Personal Executive</title>
    <style>
        /* Developer 3: Add your CSS styling here */
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .chat-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .messages {
            height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .assistant-message {
            background-color: #f5f5f5;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #1976D2;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>🤖 Context-Aware Personal Executive</h1>
        <p>Ask questions about your emails, documents, and notes!</p>
        
        <div class="messages" id="messages"></div>
        
        <div class="input-container">
            <input type="text" id="queryInput" placeholder="Type your question here..." />
            <button onclick="sendQuery()">Send</button>
            <button onclick="clearChat()">Clear</button>
        </div>
    </div>
    
    <script>
        // Developer 3: Add your JavaScript here
        const sessionId = 'user-' + Date.now();
        
        function addMessage(text, isUser) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (isUser ? 'user-message' : 'assistant-message');
            messageDiv.textContent = text;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendQuery() {
            const input = document.getElementById('queryInput');
            const query = input.value.trim();
            
            if (!query) return;
            
            addMessage(query, true);
            input.value = '';
            
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query, session_id: sessionId})
                });
                
                const data = await response.json();
                addMessage(data.response, false);
            } catch (error) {
                addMessage('Error: ' + error.message, false);
            }
        }
        
        async function clearChat() {
            await fetch('/api/clear/' + sessionId, {method: 'POST'});
            document.getElementById('messages').innerHTML = '';
        }
        
        // Allow Enter key to send message
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendQuery();
        });
    </script>
</body>
</html>
"""


def create_template():
    """Create the HTML template file"""
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)
    
    template_file = template_dir / 'index.html'
    if not template_file.exists():
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(HTML_TEMPLATE)
        log_info(f"Created template file: {template_file}")


if __name__ == '__main__':
    # Create template if it doesn't exist
    create_template()
    
    log_info(f"Starting Flask server on port {FLASK_PORT}")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
