"""
Authentication Manager
Handles user authentication, password validation, and data persistence
"""

import json
import re
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class AuthManager:
    """Manage user authentication and data persistence"""
    
    def __init__(self, data_dir='backend/data'):
        """Initialize auth manager with persistent storage"""
        self.data_dir = Path(__file__).parent / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        self.users_file = self.data_dir / 'users.json'
        self.data_sources_file = self.data_dir / 'data_sources.json'
        self.files_file = self.data_dir / 'files.json'
        self.notes_file = self.data_dir / 'notes.json'
        
        # Load existing data or create empty databases
        self.users_db = self._load_json(self.users_file, {})
        self.data_sources_db = self._load_json(self.data_sources_file, {})
        self.files_db = self._load_json(self.files_file, {})
        self.notes_db = self._load_json(self.notes_file, {})
    
    def _load_json(self, filepath, default=None):
        """Load JSON file or return default"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else {}
        return default if default is not None else {}
    
    def _save_json(self, filepath, data):
        """Save data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, indent=2, fp=f)
    
    def validate_password_strength(self, password):
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character (!@#$%^&* etc.)"
        
        return True, ""
    
    def validate_email(self, email):
        """
        Validate email format
        
        Returns:
            tuple: (is_valid, error_message)
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        return True, ""
    
    def user_exists(self, email):
        """Check if user already exists"""
        return email.lower() in self.users_db
    
    def create_user(self, email, name, password):
        """
        Create a new user with hashed password
        
        Returns:
            tuple: (success, message, user_data or None)
        """
        email = email.lower().strip()
        name = name.strip()
        
        # Validate email
        valid_email, email_error = self.validate_email(email)
        if not valid_email:
            return False, email_error, None
        
        # Check if user already exists
        if self.user_exists(email):
            return False, "User with this email already exists. Please login instead.", None
        
        # Validate password strength
        valid_password, password_error = self.validate_password_strength(password)
        if not valid_password:
            return False, password_error, None
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        user_data = {
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'avatar': f'https://ui-avatars.com/api/?name={name.replace(" ", "+")}',
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.users_db[email] = user_data
        self._save_json(self.users_file, self.users_db)
        
        # Initialize data sources for new user
        self.data_sources_db[email] = {
            'gmail': {'connected': False, 'last_sync': None},
            'drive': {'connected': False, 'last_sync': None},
            'calendar': {'connected': False, 'last_sync': None}
        }
        self._save_json(self.data_sources_file, self.data_sources_db)
        
        # Initialize empty files and notes
        self.files_db[email] = []
        self.notes_db[email] = []
        self._save_json(self.files_file, self.files_db)
        self._save_json(self.notes_file, self.notes_db)
        
        # Return user data without password hash
        safe_user_data = {
            'email': user_data['email'],
            'name': user_data['name'],
            'avatar': user_data['avatar']
        }
        
        return True, "User created successfully", safe_user_data
    
    def authenticate_user(self, email, password):
        """
        Authenticate user with email and password
        
        Returns:
            tuple: (success, message, user_data or None)
        """
        email = email.lower().strip()
        
        # Check if user exists
        if not self.user_exists(email):
            return False, "Invalid email or password", None
        
        user_data = self.users_db[email]
        
        # Verify password
        if not check_password_hash(user_data['password_hash'], password):
            return False, "Invalid email or password", None
        
        # Update last login
        user_data['last_login'] = datetime.now().isoformat()
        self.users_db[email] = user_data
        self._save_json(self.users_file, self.users_db)
        
        # Return safe user data (without password hash)
        safe_user_data = {
            'email': user_data['email'],
            'name': user_data['name'],
            'avatar': user_data['avatar'],
            'last_login': user_data['last_login']
        }
        
        return True, "Login successful", safe_user_data
    
    def get_user(self, email):
        """Get user data (without password hash)"""
        email = email.lower().strip()
        
        if not self.user_exists(email):
            return None
        
        user_data = self.users_db[email]
        return {
            'email': user_data['email'],
            'name': user_data['name'],
            'avatar': user_data['avatar'],
            'created_at': user_data.get('created_at'),
            'last_login': user_data.get('last_login')
        }
    
    def get_data_sources(self, email):
        """Get user's data sources"""
        return self.data_sources_db.get(email.lower(), {})
    
    def get_files(self, email):
        """Get user's files"""
        return self.files_db.get(email.lower(), [])
    
    def get_notes(self, email):
        """Get user's notes"""
        return self.notes_db.get(email.lower(), [])
    
    def add_file(self, email, file_data):
        """Add file to user's collection"""
        email = email.lower()
        if email not in self.files_db:
            self.files_db[email] = []
        
        self.files_db[email].append(file_data)
        self._save_json(self.files_file, self.files_db)
    
    def delete_file(self, email, file_id):
        """Delete file from user's collection"""
        email = email.lower()
        if email not in self.files_db:
            return False
        
        user_files = self.files_db[email]
        for i, f in enumerate(user_files):
            if f['id'] == file_id:
                deleted_file = user_files.pop(i)
                self._save_json(self.files_file, self.files_db)
                return deleted_file
        
        return None
    
    def add_note(self, email, note_data):
        """Add note to user's collection"""
        email = email.lower()
        if email not in self.notes_db:
            self.notes_db[email] = []
        
        self.notes_db[email].append(note_data)
        self._save_json(self.notes_file, self.notes_db)
    
    def delete_note(self, email, note_id):
        """Delete note from user's collection"""
        email = email.lower()
        if email not in self.notes_db:
            return None
        
        user_notes = self.notes_db[email]
        for i, n in enumerate(user_notes):
            if n['id'] == note_id:
                deleted_note = user_notes.pop(i)
                self._save_json(self.notes_file, self.notes_db)
                return deleted_note
        
        return None
    
    def update_data_source(self, email, source_name, source_data):
        """Update data source connection status"""
        email = email.lower()
        if email not in self.data_sources_db:
            self.data_sources_db[email] = {}
        
        self.data_sources_db[email][source_name] = source_data
        self._save_json(self.data_sources_file, self.data_sources_db)
