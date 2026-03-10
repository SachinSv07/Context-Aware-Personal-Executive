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
        self.conversations_file = self.data_dir / 'conversations.json'
        
        # Load existing data or create empty databases
        self.users_db = self._load_json(self.users_file, {})
        self.data_sources_db = self._load_json(self.data_sources_file, {})
        self.files_db = self._load_json(self.files_file, {})
        self.notes_db = self._load_json(self.notes_file, {})
        self.conversations_db = self._load_json(self.conversations_file, {})
    
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
    
    def get_conversations(self, email):
        """Retrieve all conversations for a user"""
        email = email.lower()
        return self.conversations_db.get(email, [])
    
    def save_conversation(self, email, conversation_data):
        """Save or update a conversation"""
        email = email.lower()
        if email not in self.conversations_db:
            self.conversations_db[email] = []
        
        # Check if conversation with this id already exists
        conversation_id = conversation_data.get('id')
        existing_conversations = self.conversations_db[email]
        
        for i, conv in enumerate(existing_conversations):
            if conv.get('id') == conversation_id:
                # Update existing conversation
                existing_conversations[i] = conversation_data
                self._save_json(self.conversations_file, self.conversations_db)
                return conversation_data
        
        # Add new conversation
        self.conversations_db[email].append(conversation_data)
        self._save_json(self.conversations_file, self.conversations_db)
        return conversation_data
    
    def delete_conversation(self, email, conversation_id):
        """Delete a conversation from user's collection"""
        email = email.lower()
        if email not in self.conversations_db:
            return None
        
        user_conversations = self.conversations_db[email]
        for i, conv in enumerate(user_conversations):
            if conv.get('id') == conversation_id:
                deleted_conversation = user_conversations.pop(i)
                self._save_json(self.conversations_file, self.conversations_db)
                return deleted_conversation
        
        return None
    
    def add_message_to_conversation(self, email, conversation_id, message):
        """Add a message to an existing conversation"""
        email = email.lower()
        if email not in self.conversations_db:
            return None
        
        user_conversations = self.conversations_db[email]
        for conv in user_conversations:
            if conv.get('id') == conversation_id:
                if 'messages' not in conv:
                    conv['messages'] = []
                conv['messages'].append(message)
                self._save_json(self.conversations_file, self.conversations_db)
                return conv
        
        return None
    
    def store_oauth_credentials(self, email, provider, credentials_dict):
        """
        Store OAuth credentials for a user
        
        Args:
            email: User's email address
            provider: OAuth provider (e.g., 'google', 'microsoft')
            credentials_dict: Dictionary containing OAuth credentials
        """
        email = email.lower()
        
        # Initialize oauth_credentials file if not exists
        oauth_file = self.data_dir / 'oauth_credentials.json'
        oauth_db = self._load_json(oauth_file, {})
        
        if email not in oauth_db:
            oauth_db[email] = {}
        
        oauth_db[email][provider] = {
            **credentials_dict,
            'stored_at': datetime.now().isoformat()
        }
        
        self._save_json(oauth_file, oauth_db)
        return True
    
    def get_oauth_credentials(self, email, provider):
        """
        Retrieve OAuth credentials for a user
        
        Args:
            email: User's email address
            provider: OAuth provider (e.g., 'google', 'microsoft')
            
        Returns:
            dict: OAuth credentials or None if not found
        """
        email = email.lower()
        
        oauth_file = self.data_dir / 'oauth_credentials.json'
        oauth_db = self._load_json(oauth_file, {})
        
        if email in oauth_db and provider in oauth_db[email]:
            return oauth_db[email][provider]
        
        return None
    
    def delete_oauth_credentials(self, email, provider):
        """
        Delete OAuth credentials for a user
        
        Args:
            email: User's email address
            provider: OAuth provider (e.g., 'google', 'microsoft')
            
        Returns:
            bool: True if deleted, False if not found
        """
        email = email.lower()
        
        oauth_file = self.data_dir / 'oauth_credentials.json'
        oauth_db = self._load_json(oauth_file, {})
        
        if email in oauth_db and provider in oauth_db[email]:
            del oauth_db[email][provider]
            self._save_json(oauth_file, oauth_db)
            return True
        
        return False
    
    def save_oauth_app_config(self, provider, config):
        """
        Save OAuth application configuration (Client ID, Secret, etc.)
        
        Args:
            provider: OAuth provider (e.g., 'google', 'microsoft')
            config: Dictionary with oauth app configuration
                    e.g., {'client_id': '...', 'client_secret': '...', 'redirect_uri': '...'}
            
        Returns:
            bool: True if saved successfully
        """
        oauth_config_file = self.data_dir / 'oauth_app_config.json'
        oauth_configs = self._load_json(oauth_config_file, {})
        
        oauth_configs[provider] = {
            **config,
            'updated_at': datetime.now().isoformat()
        }
        
        self._save_json(oauth_config_file, oauth_configs)
        return True
    
    def get_oauth_app_config(self, provider):
        """
        Get OAuth application configuration for a provider
        
        Args:
            provider: OAuth provider (e.g., 'google', 'microsoft')
            
        Returns:
            dict: OAuth app configuration or None if not found
        """
        oauth_config_file = self.data_dir / 'oauth_app_config.json'
        oauth_configs = self._load_json(oauth_config_file, {})
        
        return oauth_configs.get(provider)
    
    def is_oauth_app_configured(self, provider):
        """
        Check if OAuth app is configured for a provider
        
        Args:
            provider: OAuth provider (e.g., 'google', 'microsoft')
            
        Returns:
            bool: True if configured, False otherwise
        """
        config = self.get_oauth_app_config(provider)
        
        if not config:
            return False
        
        # Check if required fields are present
        required_fields = ['client_id', 'client_secret']
        return all(field in config and config[field] for field in required_fields)
    
    def save_temp_data(self, key, value):
        """
        Save temporary data (e.g., OAuth code_verifier)
        
        Args:
            key: Unique identifier for the data
            value: Data to store
            
        Returns:
            bool: True if saved successfully
        """
        temp_data_file = self.data_dir / 'temp_data.json'
        temp_db = self._load_json(temp_data_file, {})
        
        temp_db[key] = {
            'value': value,
            'stored_at': datetime.now().isoformat()
        }
        
        self._save_json(temp_data_file, temp_db)
        return True
    
    def get_temp_data(self, key):
        """
        Retrieve temporary data
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            The stored value or None if not found
        """
        temp_data_file = self.data_dir / 'temp_data.json'
        temp_db = self._load_json(temp_data_file, {})
        
        if key in temp_db:
            return temp_db[key]['value']
        
        return None
    
    def delete_temp_data(self, key):
        """
        Delete temporary data
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            bool: True if deleted, False if not found
        """
        temp_data_file = self.data_dir / 'temp_data.json'
        temp_db = self._load_json(temp_data_file, {})
        
        if key in temp_db:
            del temp_db[key]
            self._save_json(temp_data_file, temp_db)
            return True
        
        return False

