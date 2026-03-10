# Quick Start: Google OAuth Setup

## Step 1: Install Required Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv
```

## Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to **APIs & Services** > **Library**
   - Search for "Gmail API" and click **Enable**

4. Create OAuth credentials:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth client ID**
   - If prompted, configure OAuth consent screen first
   - Choose **Web application**
   - Add authorized redirect URI: `http://localhost:5000/api/auth/google/callback`
   - Click **Create**
   - Copy the **Client ID** and **Client Secret**

## Step 3: Create .env File

Create a `.env` file in the project root:

```env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

## Step 4: Start the Backend Server

```bash
python backend/api.py
```

## Step 5: Test Gmail Integration

1. Open the React app at http://localhost:3000
2. Navigate to Dashboard
3. Click **Connect Gmail**
4. Authorize with your Google account
5. You'll be redirected back to the dashboard
6. Click **Fetch Emails** to retrieve your Gmail messages

## Troubleshooting

**"OAuth not configured" error:**
- Make sure all Google packages are installed
- Check that .env file exists with correct credentials
- Restart the backend server after adding .env

**"Redirect URI mismatch" error:**
- Verify redirect URI in Google Cloud Console matches: `http://localhost:5000/api/auth/google/callback`
- Check for typos or extra characters

**App shows "unverified" warning:**
- This is normal during development
- Click "Advanced" > "Go to [app name] (unsafe)" to proceed
- For production, complete OAuth consent screen verification

For detailed setup instructions, see [OAUTH_SETUP.md](backend/OAUTH_SETUP.md)
