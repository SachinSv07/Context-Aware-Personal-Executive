"""Flask API Backend for React Frontend"""

from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from agent import process_query
from google_auth_oauthlib.flow import Flow
from config import GMAIL_TOKEN_PATH

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')
CORS(app, supports_credentials=True)

# ── Google OAuth config ────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
FRONTEND_URL         = os.getenv('FRONTEND_URL', 'http://localhost:3000')
BACKEND_URL          = os.getenv('BACKEND_URL',  'http://localhost:5000')

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
]

def _save_gmail_token(payload: dict) -> None:
    token_path = Path(GMAIL_TOKEN_PATH)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(payload), encoding="utf-8")


def _has_gmail_token() -> bool:
    return Path(GMAIL_TOKEN_PATH).exists()


def _delete_gmail_token() -> None:
    token_path = Path(GMAIL_TOKEN_PATH)
    if token_path.exists():
        token_path.unlink()


def _build_flow(scopes):
    """Build an OAuth Flow from env credentials."""
    client_config = {
        'web': {
            'client_id':     GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'auth_uri':      'https://accounts.google.com/o/oauth2/auth',
            'token_uri':     'https://oauth2.googleapis.com/token',
            'redirect_uris': [f'{BACKEND_URL}/auth/google/callback'],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=scopes,
        redirect_uri=f'{BACKEND_URL}/auth/google/callback',
    )


# ── Auth routes ────────────────────────────────────────────────────────────

@app.route('/auth/google')
def auth_google():
    """
    Step 1 – Redirect user to Google's OAuth consent screen.
    React triggers this with: window.location.href = 'http://localhost:5000/auth/google'
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({'error': 'GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set in .env'}), 500

    flow = _build_flow(GMAIL_SCOPES)
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    
    # Store state and code_verifier in session for use in callback
    session['oauth_state'] = state
    if hasattr(flow, 'code_verifier'):
        session['oauth_code_verifier'] = flow.code_verifier
    
    return redirect(auth_url)


@app.route('/auth/google/callback')
def auth_google_callback():
    """
    Step 2 – Google redirects here after the user approves.
    We exchange the code for tokens, store them, and redirect back to React.
    """
    # Verify state matches
    state = request.args.get('state')
    if not state or state != session.get('oauth_state'):
        return jsonify({'error': 'State mismatch. OAuth request may have been tampered with.'}), 400
    
    flow = _build_flow(GMAIL_SCOPES)
    
    # Restore code_verifier from session if it was stored (for PKCE)
    if 'oauth_code_verifier' in session:
        flow.code_verifier = session['oauth_code_verifier']
    
    try:
        # Exchange authorization code for tokens
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        print(f"Error fetching token: {e}")
        return jsonify({'error': f'Failed to exchange code for token: {str(e)}'}), 400

    creds = flow.credentials
    gmail_token_payload = {
        'token':         creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri':     creds.token_uri,
        'client_id':     creds.client_id,
        'client_secret': creds.client_secret,
        'scopes':        list(creds.scopes or []),
    }
    _save_gmail_token(gmail_token_payload)

    # Clear state from session
    session.pop('oauth_state', None)

    # Redirect React front-end back with a success flag
    return redirect(f'{FRONTEND_URL}/dashboard?gmail=connected')


@app.route('/auth/status')
def auth_status():
    """Return which services are currently connected."""
    return jsonify({"gmail": _has_gmail_token()})


@app.route('/auth/disconnect/<service>', methods=['POST'])
def auth_disconnect(service):
    """Remove stored token for a service."""
    if service == "gmail":
        _delete_gmail_token()
    return jsonify({'disconnected': service})


# ── Existing routes ────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'message': 'Backend is running'})


@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        response = process_query(user_query)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Allow OAuth over plain HTTP during local development
    os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')
    print('Starting Flask API Backend on http://localhost:5000')
    app.run(debug=True, port=5000)
