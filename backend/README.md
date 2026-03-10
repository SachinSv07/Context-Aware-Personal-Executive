# Backend Folder

This folder contains the Flask API backend that powers the React frontend UI.

## Structure

```
backend/
├── api.py                 # Main Flask API server with all endpoints
├── API_DOCUMENTATION.md   # Comprehensive API documentation
├── OAUTH_SETUP.md        # Google OAuth setup guide
├── test_api.py           # API testing script
└── README.md             # This file
```

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

Required packages:
- `flask>=3.0.0` - Web framework
- `flask-cors>=4.0.0` - CORS support for React frontend
- `werkzeug>=3.0.0` - Secure file uploads

### 2. Set Up Environment

Create a `.env` file in the project root:

```env
# Required: Choose one
OPENAI_API_KEY=your_openai_key_here
# OR
GEMINI_API_KEY=your_gemini_key_here

# Optional: For Google OAuth (see OAUTH_SETUP.md)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_API_KEY=your_api_key
```

### 3. Run the Backend

```bash
# From project root
python backend/api.py
```

The server will start at: **http://localhost:5000**

### 4. Test the Backend

Open http://localhost:5000/api/health in your browser, or run the test script:

```bash
python backend/test_api.py
```

## API Endpoints

The backend provides comprehensive REST API endpoints for:

### 🔐 Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration

### 👤 User Management
- `GET /api/user/profile` - Get user profile and data

### 🤖 AI Query
- `POST /api/query` - Send query to AI agent
- `GET /api/health` - Health check

### 📊 Data Sources
- `GET /api/data-sources` - List all data source connections
- `POST /api/data-sources/gmail/connect` - Connect Gmail
- `POST /api/data-sources/calendar/connect` - Connect Calendar
- `POST /api/data-sources/drive/connect` - Connect Google Drive

### 📁 File Management
- `GET /api/files` - List all uploaded files
- `POST /api/files/upload` - Upload a file (PDF, TXT, DOC, DOCX)
- `DELETE /api/files/{id}` - Delete a file

### 📝 Notes Management
- `GET /api/notes` - List all notes
- `POST /api/notes` - Save a new note
- `DELETE /api/notes/{id}` - Delete a note

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Features

### Current Implementation

✅ **REST API** - Full CRUD operations for all resources
✅ **CORS Support** - React frontend can call the API
✅ **File Uploads** - Secure file upload with size limits
✅ **In-Memory Storage** - Quick development without database setup
✅ **AI Agent Integration** - Process queries using LLM
✅ **Error Handling** - Consistent error responses

### Production Considerations

⚠️ **Authentication** - Currently simplified; implement JWT in production
⚠️ **Database** - Replace in-memory storage with PostgreSQL/MongoDB
⚠️ **OAuth** - Google OAuth flows ready to implement (see OAUTH_SETUP.md)
⚠️ **File Storage** - Consider cloud storage (S3, GCS) for uploaded files
⚠️ **Rate Limiting** - Add rate limiting to prevent API abuse
⚠️ **Logging** - Add structured logging for production monitoring
⚠️ **HTTPS** - Use HTTPS in production with proper certificates

## Architecture

### Request Flow

```
React Frontend (http://localhost:3000)
    ↓
CORS-enabled API (http://localhost:5000)
    ↓
Flask Route Handler
    ↓
├─→ Agent (for /api/query)
│   ├─→ choose_tool() - Select email/pdf/csv tool
│   └─→ process_query() - Execute and return results
│
├─→ In-Memory Database (users, files, notes)
│
└─→ File System (uploads/ folder)
```

### Data Storage

Current implementation uses Python dictionaries for fast development:

- **users_db** - User accounts and credentials
- **data_sources_db** - Connection status for Gmail/Drive/Calendar
- **files_db** - Uploaded file metadata
- **notes_db** - User notes

**Production:** Replace with:
- PostgreSQL for structured data (users, metadata)
- MongoDB for unstructured data (notes, documents)
- Redis for session/cache management
- S3/GCS for file storage

## Configuration

### File Upload Settings

```python
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

### CORS Settings

Currently allows all origins. In production, restrict to your domain:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"]
    }
})
```

## Development

### Running Tests

```bash
# Run all API tests
python backend/test_api.py
```

### Adding New Endpoints

1. Define route in `api.py`:
```python
@app.route('/api/your-endpoint', methods=['POST'])
def your_endpoint():
    try:
        data = request.get_json()
        # Your logic here
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

2. Update `API_DOCUMENTATION.md`
3. Add test in `test_api.py`
4. Test with React frontend

### Debugging

Enable debug mode (development only):

```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

View logs in terminal where backend is running.

## Connecting React Frontend

The React frontend connects to these endpoints. Make sure:

1. Backend is running at `http://localhost:5000`
2. Frontend is running at `http://localhost:3000`
3. CORS is enabled (already configured)

Example React fetch:

```javascript
const response = await fetch('http://localhost:5000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Your query here' })
});
const data = await response.json();
```

## Google OAuth Integration

To enable real Gmail/Drive/Calendar integration:

1. Follow the detailed setup guide in [OAUTH_SETUP.md](OAUTH_SETUP.md)
2. Get credentials from Google Cloud Console
3. Add credentials to `.env` file
4. Install additional packages:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```
5. Uncomment OAuth code sections in `api.py`

## Troubleshooting

### Backend won't start

```bash
# Check if port 5000 is already in use
netstat -ano | findstr :5000

# Kill process using port 5000 (Windows)
taskkill /PID <PID> /F

# Or use a different port
app.run(debug=True, port=5001)
```

### CORS errors

- Ensure `flask-cors` is installed: `pip install flask-cors`
- Check CORS is enabled: `CORS(app)` in `api.py`
- Verify frontend is calling correct URL

### File upload fails

- Check file size (max 16MB)
- Verify file extension is allowed
- Ensure `uploads/` folder exists (created automatically)
- Check permissions on `uploads/` folder

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install flask flask-cors werkzeug
```

## Next Steps

1. **Implement JWT Authentication**
   - Replace demo tokens with real JWT
   - Add token validation middleware
   - Implement token refresh

2. **Add Database**
   - Set up PostgreSQL or MongoDB
   - Create database models
   - Migrate from in-memory storage

3. **Google OAuth**
   - Follow [OAUTH_SETUP.md](OAUTH_SETUP.md)
   - Implement OAuth flows
   - Test with real Google accounts

4. **File Processing**
   - Extract text from PDFs
   - Index documents for search
   - Implement semantic search

5. **Deploy to Production**
   - Use gunicorn or uvicorn
   - Set up HTTPS
   - Configure environment variables
   - Add monitoring and logging

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)
- [Google OAuth Guide](OAUTH_SETUP.md)
- [API Documentation](API_DOCUMENTATION.md)

## Support

For issues or questions:
1. Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details
2. Run `python backend/test_api.py` to verify all endpoints
3. Check terminal logs for error messages
4. Review agent code in `../agent/` folder
