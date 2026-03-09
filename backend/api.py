"""
Flask API Backend for React Frontend
Connects React UI to Python Agent
"""

from flask import Flask, request, jsonify
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
    """Get current user from request (simplified - use JWT in production)"""
    # In production, decode JWT token from Authorization header
    # For now, return demo user
    return 'user@example.com'


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


# ==================== Server Startup ====================

if __name__ == '__main__':
    print("Starting Flask API Backend...")
    print("React frontend should connect to: http://localhost:5000")
    app.run(debug=True, port=5000)
