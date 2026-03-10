# Backend API Documentation

Base URL: `http://localhost:5000/api`

## Table of Contents

- [Health & Query](#health--query)
- [Authentication](#authentication)
- [User Profile](#user-profile)
- [Data Sources](#data-sources)
- [File Management](#file-management)
- [Notes Management](#notes-management)

---

## Health & Query

### Health Check

Check if the backend API is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "message": "Backend is running"
}
```

---

### Query Agent

Send a query to the AI agent for processing.

**Endpoint:** `POST /api/query`

**Request Body:**
```json
{
  "query": "What emails are about meetings?"
}
```

**Response:**
```json
{
  "response": "Tool Selected: email\nSearching email records...\n\nResult: [...]"
}
```

**Error Response:**
```json
{
  "error": "Query is required"
}
```

---

## Authentication

### Login

Authenticate a user and receive a token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "token": "demo_token_user@example.com",
  "user": {
    "email": "user@example.com",
    "name": "Alex Johnson",
    "avatar": "https://ui-avatars.com/api/?name=Alex+Johnson"
  }
}
```

**Error Responses:**
- `400`: Missing email or password
- `401`: Invalid credentials

---

### Sign Up

Create a new user account.

**Endpoint:** `POST /api/auth/signup`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "name": "New User",
  "password": "password123"
}
```

**Success Response (201):**
```json
{
  "token": "demo_token_newuser@example.com",
  "user": {
    "email": "newuser@example.com",
    "name": "New User",
    "avatar": "https://ui-avatars.com/api/?name=New+User"
  }
}
```

**Error Responses:**
- `400`: Missing required fields
- `409`: User already exists

---

## User Profile

### Get User Profile

Get the current user's profile data, including connected data sources, files, and notes.

**Endpoint:** `GET /api/user/profile`

**Response:**
```json
{
  "user": {
    "email": "user@example.com",
    "name": "Alex Johnson",
    "avatar": "https://ui-avatars.com/api/?name=Alex+Johnson"
  },
  "data_sources": {
    "gmail": {
      "connected": true,
      "email": "user@gmail.com",
      "last_sync": "2026-03-09T10:30:00"
    },
    "drive": {
      "connected": false,
      "last_sync": null
    },
    "calendar": {
      "connected": false,
      "last_sync": null
    }
  },
  "files": [
    {
      "id": 1,
      "name": "document.pdf",
      "source": "Upload",
      "uploaded_at": "2026-03-09T10:00:00",
      "size": "1024 KB"
    }
  ],
  "notes": [
    {
      "id": 1,
      "content": "Important meeting notes",
      "created_at": "2026-03-09T09:00:00"
    }
  ]
}
```

---

## Data Sources

### Get All Data Sources

Get the connection status of all data sources.

**Endpoint:** `GET /api/data-sources`

**Response:**
```json
{
  "data_sources": {
    "gmail": {
      "connected": false,
      "last_sync": null
    },
    "drive": {
      "connected": false,
      "last_sync": null
    },
    "calendar": {
      "connected": false,
      "last_sync": null
    }
  }
}
```

---

### Connect Gmail

Connect a Gmail account to the application.

**Endpoint:** `POST /api/data-sources/gmail/connect`

**Request Body:**
```json
{
  "email": "user@gmail.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Gmail connected successfully",
  "data_source": {
    "connected": true,
    "email": "user@gmail.com",
    "last_sync": "2026-03-09T10:30:00"
  }
}
```

**Note:** In production, this would initiate an OAuth flow. Currently, it's a simplified implementation.

---

### Connect Calendar

Connect Google Calendar to the application.

**Endpoint:** `POST /api/data-sources/calendar/connect`

**Response:**
```json
{
  "success": true,
  "message": "Calendar connected successfully",
  "data_source": {
    "connected": true,
    "last_sync": "2026-03-09T10:30:00"
  }
}
```

---

### Connect Google Drive

Add a file from Google Drive to the application.

**Endpoint:** `POST /api/data-sources/drive/connect`

**Request Body:**
```json
{
  "file_id": "1abc123def456",
  "file_name": "document.pdf"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Google Drive file added successfully",
  "file": {
    "id": 1,
    "name": "document.pdf",
    "source": "Google Drive",
    "drive_file_id": "1abc123def456",
    "uploaded_at": "2026-03-09T10:30:00",
    "size": "Unknown"
  }
}
```

---

## File Management

### Upload File

Upload a file (PDF, TXT, DOC, DOCX) to the application.

**Endpoint:** `POST /api/files/upload`

**Request:** Multipart form data
- `file`: The file to upload

**Example using curl:**
```bash
curl -X POST \
  http://localhost:5000/api/files/upload \
  -F "file=@/path/to/document.pdf"
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "id": 1,
    "name": "document.pdf",
    "source": "Upload",
    "path": "20260309103000_document.pdf",
    "uploaded_at": "2026-03-09T10:30:00",
    "size": "1024.5 KB"
  }
}
```

**Error Responses:**
- `400`: No file provided / Invalid file type
- Max file size: 16MB

---

### Get All Files

Get all uploaded files for the current user.

**Endpoint:** `GET /api/files`

**Response:**
```json
{
  "files": [
    {
      "id": 1,
      "name": "document.pdf",
      "source": "Upload",
      "uploaded_at": "2026-03-09T10:00:00",
      "size": "1024 KB"
    },
    {
      "id": 2,
      "name": "report.pdf",
      "source": "Google Drive",
      "drive_file_id": "1abc123",
      "uploaded_at": "2026-03-09T11:00:00",
      "size": "Unknown"
    }
  ]
}
```

---

### Delete File

Delete a file by ID.

**Endpoint:** `DELETE /api/files/{file_id}`

**Example:** `DELETE /api/files/1`

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "File not found"
}
```

---

## Notes Management

### Get All Notes

Get all notes for the current user.

**Endpoint:** `GET /api/notes`

**Response:**
```json
{
  "notes": [
    {
      "id": 1,
      "content": "Important meeting notes from today",
      "created_at": "2026-03-09T09:00:00"
    },
    {
      "id": 2,
      "content": "Remember to follow up with client",
      "created_at": "2026-03-09T10:00:00"
    }
  ]
}
```

---

### Save Note

Save a new note.

**Endpoint:** `POST /api/notes`

**Request Body:**
```json
{
  "content": "This is my note content"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Note saved successfully",
  "note": {
    "id": 1,
    "content": "This is my note content",
    "created_at": "2026-03-09T10:30:00"
  }
}
```

**Error Response (400):**
```json
{
  "error": "Note content is required"
}
```

---

### Delete Note

Delete a note by ID.

**Endpoint:** `DELETE /api/notes/{note_id}`

**Example:** `DELETE /api/notes/1`

**Response:**
```json
{
  "success": true,
  "message": "Note deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "Note not found"
}
```

---

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created successfully
- `400` - Bad request (missing or invalid parameters)
- `401` - Unauthorized (authentication required)
- `404` - Resource not found
- `409` - Conflict (e.g., user already exists)
- `500` - Internal server error

---

## Authentication

**Current Implementation:** Simplified token-based authentication

The `get_current_user()` helper currently returns a demo user (`user@example.com`).

**Production Implementation:** 
- Use JWT (JSON Web Tokens) for authentication
- Include token in `Authorization` header: `Authorization: Bearer {token}`
- Implement token refresh mechanism
- Store tokens securely on the client side

**Example with JWT:**
```javascript
fetch('http://localhost:5000/api/user/profile', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

---

## Testing

### Using curl

Test the health endpoint:
```bash
curl http://localhost:5000/api/health
```

Test login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"demo123"}'
```

Test query:
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What emails are about meetings?"}'
```

---

## Running the Backend

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_key_here
   # or
   GEMINI_API_KEY=your_key_here
   ```

3. **Run the server:**
   ```bash
   python backend/api.py
   ```

   The server will start at `http://localhost:5000`

4. **Test the connection:**
   Open http://localhost:5000/api/health in your browser

---

## Next Steps

1. **Implement real OAuth flows** - See [OAUTH_SETUP.md](OAUTH_SETUP.md)
2. **Add JWT authentication** - Replace demo tokens with proper JWT
3. **Connect to a database** - Replace in-memory storage
4. **Add rate limiting** - Prevent API abuse
5. **Implement file processing** - Extract text from PDFs for querying
6. **Add WebSocket support** - For real-time updates
7. **Deploy to production** - Use gunicorn/uvicorn with HTTPS
