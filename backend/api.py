"""
Flask API Backend for React Frontend
Connects React UI to Python Agent
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import process_query

app = Flask(__name__)
CORS(app)  # Allow React frontend to call this API


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})


@app.route('/api/query', methods=['POST'])
def query():
    """
    Main query endpoint for React frontend
    
    Request body:
    {
        "query": "What emails are about meetings?"
    }
    
    Response:
    {
        "response": "Tool Selected: email\nSearching...\n\nResult: ..."
    }
    """
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Call your agent
        response = process_query(user_query)
        
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Flask API Backend...")
    print("React frontend should connect to: http://localhost:5000")
    app.run(debug=True, port=5000)
