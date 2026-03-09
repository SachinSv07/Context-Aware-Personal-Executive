"""
Flask API Backend for React Frontend
Connects React UI to Python Agent
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import sys
from pathlib import Path
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import process_query
from backend.auth_manager import AuthManager

try:
    from backend.oauth_helper import (
        get_authorization_url,
        get_credentials_from_code,
        credentials_to_dict,
        dict_to_credentials,
        fetch_gmail_messages
    )
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    print("Warning: Google OAuth dependencies not installed. Gmail integration disabled.")
    print("Run: pip install -r requirements.txt to enable OAuth features.")

app = Flask(__name__)
CORS(app)  # Allow React frontend to call this API

# Configuration
UPLOAD_FOLDER = Path(__file__).parent.parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Authentication Manager with persistent storage
auth_manager = AuthManager()


# Helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user():
    """
    Get current user email from request Authorization header
    
    Token format: token_{email}_{timestamp}
    
    Returns:
        str: User email address
        
    Raises:
        Exception: If no valid token is provided
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        raise Exception('No authorization token provided')
    
    # Extract token (format: "Bearer token_{email}_{timestamp}" or just "token_{email}_{timestamp}")
    token = auth_header.replace('Bearer ', '').strip()
    
    # Parse token to extract email
    # Token format: token_{email}_{timestamp}
    if not token.startswith('token_'):
        raise Exception('Invalid token format')
    
    parts = token.split('_')
    if len(parts) < 3:
        raise Exception('Invalid token format')
    
    # Email is between "token_" and the timestamp
    # Join all parts except first (token) and last (timestamp)
    email = '_'.join(parts[1:-1])
    
    if not email:
        raise Exception('No user email in token')
    
    return email


# ==================== Health & Query Endpoints ====================

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


# ==================== Authentication Endpoints ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login endpoint with secure password verification
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user with hashed password
        success, message, user_data = auth_manager.authenticate_user(email, password)
        
        if not success:
            return jsonify({'error': message}), 401
        
        # In production, generate JWT token here
        token = f'token_{email}_{datetime.now().timestamp()}'
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user_data,
            'message': message
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """
    Signup endpoint with password validation and duplicate checking
    
    Request body:
    {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "SecurePass123!"
    }
    
    Password Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not name or not password:
            return jsonify({'error': 'Email, name, and password are required'}), 400
        
        # Create user with validation
        success, message, user_data = auth_manager.create_user(email, name, password)
        
        if not success:
            # Return specific error (duplicate user, weak password, etc.)
            status_code = 409 if 'already exists' in message else 400
            return jsonify({'error': message}), status_code
        
        # Generate token
        token = f'token_{email}_{datetime.now().timestamp()}'
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user_data,
            'message': message
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== User Profile Endpoints ====================

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get user profile data"""
    try:
        user_email = get_current_user()
        user = auth_manager.get_user(user_email)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get data sources status
        sources = auth_manager.get_data_sources(user_email)
        
        # Get files
        user_files = auth_manager.get_files(user_email)
        
        # Get notes
        user_notes = auth_manager.get_notes(user_email)
        
        return jsonify({
            'user': user,
            'data_sources': sources,
            'files': user_files,
            'notes': user_notes
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Data Sources Endpoints ====================

@app.route('/api/data-sources', methods=['GET'])
def get_data_sources():
    """Get all connected data sources status"""
    try:
        user_email = get_current_user()
        sources = auth_manager.get_data_sources(user_email)
        
        return jsonify({'data_sources': sources})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data-sources/gmail/connect', methods=['POST'])
def connect_gmail():
    """
    Connect Gmail account
    
    Request body:
    {
        "email": "user@gmail.com"
    }
    
    Note: In production, this would initiate OAuth flow
    """
    try:
        user_email = get_current_user()
        data = request.get_json()
        gmail_address = data.get('email', '').strip()
        
        if not gmail_address:
            return jsonify({'error': 'Gmail address is required'}), 400
        
        # Update Gmail connection status
        gmail_data = {
            'connected': True,
            'email': gmail_address,
            'last_sync': datetime.now().isoformat()
        }
        
        auth_manager.update_data_source(user_email, 'gmail', gmail_data)
        
        return jsonify({
            'success': True,
            'message': 'Gmail connected successfully',
            'data_source': gmail_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data-sources/calendar/connect', methods=['POST'])
def connect_calendar():
    """
    Connect Google Calendar
    
    Note: In production, this would initiate OAuth flow
    """
    try:
        user_email = get_current_user()
        
        # Update Calendar connection status
        calendar_data = {
            'connected': True,
            'last_sync': datetime.now().isoformat()
        }
        
        auth_manager.update_data_source(user_email, 'calendar', calendar_data)
        
        return jsonify({
            'success': True,
            'message': 'Calendar connected successfully',
            'data_source': calendar_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data-sources/drive/connect', methods=['POST'])
def connect_drive():
    """
    Connect Google Drive
    
    Request body:
    {
        "file_id": "google_drive_file_id",
        "file_name": "document.pdf"
    }
    
    Note: In production, this would use Google Drive API
    """
    try:
        user_email = get_current_user()
        data = request.get_json()
        
        file_id = data.get('file_id', '').strip()
        file_name = data.get('file_name', '').strip()
        
        if not file_id or not file_name:
            return jsonify({'error': 'File ID and name are required'}), 400
        
        # Update Drive connection status
        drive_data = {
            'connected': True,
            'last_sync': datetime.now().isoformat()
        }
        auth_manager.update_data_source(user_email, 'drive', drive_data)
        
        # Add file to user's files
        user_files = auth_manager.get_files(user_email)
        file_obj = {
            'id': len(user_files) + 1,
            'name': file_name,
            'source': 'Google Drive',
            'drive_file_id': file_id,
            'uploaded_at': datetime.now().isoformat(),
            'size': 'Unknown'
        }
        auth_manager.add_file(user_email, file_obj)
        
        return jsonify({
            'success': True,
            'message': 'Google Drive file added successfully',
            'file': file_obj
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== File Upload Endpoints ====================

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """
    Upload a file (PDF, TXT, DOC, DOCX)
    
    Form data:
        file: The file to upload
    """
    try:
        user_email = get_current_user()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        size_kb = round(file_size / 1024, 2)
        
        # Get current files to generate ID
        user_files = auth_manager.get_files(user_email)
        
        # Add to database
        file_obj = {
            'id': len(user_files) + 1,
            'name': filename,
            'source': 'Upload',
            'path': unique_filename,
            'uploaded_at': datetime.now().isoformat(),
            'size': f'{size_kb} KB'
        }
        auth_manager.add_file(user_email, file_obj)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file': file_obj
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files', methods=['GET'])
def get_files():
    """Get all uploaded files for current user"""
    try:
        user_email = get_current_user()
        user_files = auth_manager.get_files(user_email)
        
        return jsonify({'files': user_files})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    try:
        user_email = get_current_user()
        
        # Delete from database
        file_to_delete = auth_manager.delete_file(user_email, file_id)
        
        if not file_to_delete:
            return jsonify({'error': 'File not found'}), 404
        
        # Delete physical file if it's an upload
        if file_to_delete.get('source') == 'Upload' and file_to_delete.get('path'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_to_delete['path'])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Notes Endpoints ====================

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes for current user"""
    try:
        user_email = get_current_user()
        user_notes = auth_manager.get_notes(user_email)
        
        return jsonify({'notes': user_notes})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes', methods=['POST'])
def save_note():
    """
    Save a new note
    
    Request body:
    {
        "content": "My note content here"
    }
    """
    try:
        user_email = get_current_user()
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Note content is required'}), 400
        
        # Get current notes to generate ID
        user_notes = auth_manager.get_notes(user_email)
        
        # Create note
        note_obj = {
            'id': len(user_notes) + 1,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        auth_manager.add_note(user_email, note_obj)
        
        return jsonify({
            'success': True,
            'message': 'Note saved successfully',
            'note': note_obj
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    try:
        user_email = get_current_user()
        
        # Delete from database
        note_to_delete = auth_manager.delete_note(user_email, note_id)
        
        if not note_to_delete:
            return jsonify({'error': 'Note not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Note deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Google OAuth Endpoints ====================

@app.route('/api/auth/google/initiate', methods=['POST'])
def initiate_google_oauth():
    """
    Initiate Google OAuth flow
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
        "success": true
    }
    """
    if not OAUTH_AVAILABLE:
        return jsonify({
            'error': 'Google OAuth not configured. Please install required packages and set up credentials.',
            'setup_guide': 'See backend/OAUTH_SETUP.md for instructions'
        }), 503
    
    try:
        data = request.get_json()
        user_email = data.get('email') or get_current_user()
        
        # Generate authorization URL
        authorization_url, state = get_authorization_url(user_email, auth_manager)
        
        return jsonify({
            'authorization_url': authorization_url,
            'success': True
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/google/callback', methods=['GET'])
def google_oauth_callback():
    """
    Handle Google OAuth callback
    
    This endpoint receives the authorization code from Google
    and exchanges it for access tokens
    """
    if not OAUTH_AVAILABLE:
        return redirect('http://localhost:3000/dashboard?oauth=error&message=OAuth+not+configured')
    
    try:
        code = request.args.get('code')
        state = request.args.get('state')  # This contains the user_email
        error = request.args.get('error')
        
        if error:
            return redirect(f'http://localhost:3000/dashboard?oauth=error&message={error}')
        
        if not code or not state:
            return redirect('http://localhost:3000/dashboard?oauth=error&message=Missing+authorization+code')
        
        # Exchange code for credentials
        credentials = get_credentials_from_code(code, state, auth_manager)
        
        # Convert credentials to dictionary for storage
        creds_dict = credentials_to_dict(credentials)
        
        # Store credentials in auth_manager
        user_email = state  # We passed user_email as state
        auth_manager.store_oauth_credentials(user_email, 'google', creds_dict)
        
        # Redirect to frontend success page
        return redirect('http://localhost:3000/dashboard?oauth=success')
    
    except Exception as e:
        error_message = str(e).replace(' ', '+')
        return redirect(f'http://localhost:3000/dashboard?oauth=error&message={error_message}')


@app.route('/api/auth/google/status', methods=['GET'])
def google_oauth_status():
    """
    Check if user has connected Google OAuth and if OAuth is configured
    
    Response:
    {
        "connected": true,
        "oauth_configured": true,
        "provider": "google"
    }
    """
    try:
        user_email = get_current_user()
        
        # Check if OAuth credentials are configured
        oauth_configured = auth_manager.is_oauth_app_configured('google')
        
        # Check if user has connected their account
        credentials = auth_manager.get_oauth_credentials(user_email, 'google')
        
        return jsonify({
            'connected': bool(credentials),
            'oauth_configured': oauth_configured,
            'provider': 'google'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/google/configure', methods=['POST'])
def configure_google_oauth():
    """
    Save Google OAuth app credentials (Client ID and Secret)
    
    Request body:
    {
        "client_id": "your-client-id.apps.googleusercontent.com",
        "client_secret": "your-client-secret",
        "redirect_uri": "http://localhost:5000/api/auth/google/callback"
    }
    
    Response:
    {
        "success": true,
        "message": "OAuth credentials saved successfully"
    }
    """
    try:
        data = request.get_json()
        
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()
        redirect_uri = data.get('redirect_uri', 'http://localhost:5000/api/auth/google/callback').strip()
        
        if not client_id or not client_secret:
            return jsonify({'error': 'Client ID and Client Secret are required'}), 400
        
        # Save OAuth app credentials
        success = auth_manager.save_oauth_app_config('google', {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        })
        
        if not success:
            return jsonify({'error': 'Failed to save OAuth credentials'}), 500
        
        return jsonify({
            'success': True,
            'message': 'OAuth credentials saved successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gmail/fetch', methods=['POST'])
def fetch_gmail():
    """
    Fetch Gmail messages for the authenticated user
    
    Request body:
    {
        "max_results": 20,
        "query": "is:unread"  // optional Gmail search query
    }
    
    Response:
    {
        "messages": [...],
        "count": 20
    }
    """
    if not OAUTH_AVAILABLE:
        return jsonify({'error': 'Gmail integration not available'}), 503
    
    try:
        user_email = get_current_user()
        
        # Check if user has OAuth credentials
        creds_dict = auth_manager.get_oauth_credentials(user_email, 'google')
        
        if not creds_dict:
            return jsonify({
                'error': 'Not authenticated with Gmail. Please connect your Google account first.',
                'auth_required': True
            }), 401
        
        # Convert dict back to Credentials object
        credentials = dict_to_credentials(creds_dict)
        
        # Get request parameters
        data = request.get_json() or {}
        max_results = data.get('max_results', 20)
        query = data.get('query', '')
        
        # Fetch messages
        messages = fetch_gmail_messages(credentials, max_results, query)
        
        # Update stored credentials if they were refreshed
        updated_creds = credentials_to_dict(credentials)
        auth_manager.store_oauth_credentials(user_email, 'google', updated_creds)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Conversation Endpoints ====================

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the current user"""
    try:
        user_email = get_current_user()
        conversations = auth_manager.get_conversations(user_email)
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/save', methods=['POST'])
def save_conversation():
    """
    Save or update a conversation
    
    Request body:
    {
        "id": "unique-conversation-id",
        "title": "Conversation Title",
        "messages": [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00Z"},
            {"role": "assistant", "content": "Hi!", "timestamp": "2024-01-01T00:00:01Z"}
        ],
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:01Z"
    }
    """
    try:
        user_email = get_current_user()
        conversation_data = request.get_json()
        
        if not conversation_data or 'id' not in conversation_data:
            return jsonify({'error': 'Invalid conversation data'}), 400
        
        saved_conversation = auth_manager.save_conversation(user_email, conversation_data)
        
        return jsonify({
            'success': True,
            'conversation': saved_conversation
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        user_email = get_current_user()
        
        deleted_conversation = auth_manager.delete_conversation(user_email, conversation_id)
        
        if not deleted_conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<conversation_id>/message', methods=['POST'])
def add_message_to_conversation(conversation_id):
    """
    Add a message to an existing conversation
    
    Request body:
    {
        "role": "user" or "assistant",
        "content": "Message content",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    try:
        user_email = get_current_user()
        message_data = request.get_json()
        
        if not message_data or 'content' not in message_data or 'role' not in message_data:
            return jsonify({'error': 'Invalid message data'}), 400
        
        updated_conversation = auth_manager.add_message_to_conversation(
            user_email, 
            conversation_id, 
            message_data
        )
        
        if not updated_conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify({
            'success': True,
            'conversation': updated_conversation
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Server Startup ====================

if __name__ == '__main__':
    print("Starting Flask API Backend...")
    print("React frontend should connect to: http://localhost:5000")
    app.run(debug=True, port=5000)
