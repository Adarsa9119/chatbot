# API Reference

Base URL: `http://localhost:8000/api/v1`

All authenticated endpoints require the header:
```
Authorization: Bearer <access_token>
```

---

## Authentication

### POST /auth/register
Register a new user account.

**Request body**
```json
{
  "user_name": "Alice",
  "user_email": "alice@example.com",
  "user_password": "StrongPass1!"
}
```

**Response `201`**
```json
{ "message": "Registration successful. Please verify your email.", "user_id": 1 }
```

---

### POST /auth/login
Authenticate and receive tokens.

**Request body**
```json
{ "user_email": "alice@example.com", "user_password": "StrongPass1!" }
```

**Response `200`**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "user": { "user_id": 1, "user_name": "Alice", "user_role": "user" }
}
```

---

### POST /auth/refresh
Exchange a refresh token for a new access token.

**Request body**
```json
{ "refresh_token": "<jwt>" }
```

**Response `200`**
```json
{ "access_token": "<new_jwt>", "token_type": "bearer" }
```

---

### POST /auth/logout
Revoke the current refresh token.  *(Requires auth)*

**Response `200`**
```json
{ "message": "Logged out successfully." }
```

---

### GET /auth/me
Return the current authenticated user's profile.  *(Requires auth)*

**Response `200`**
```json
{
  "user_id": 1,
  "user_name": "Alice",
  "user_email": "alice@example.com",
  "user_role": "user",
  "is_verified": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

## Password

### POST /password/forgot
Send a password reset email.

**Request body**
```json
{ "user_email": "alice@example.com" }
```

**Response `200`**
```json
{ "message": "If that email exists, a reset link has been sent." }
```

---

### POST /password/reset
Set a new password using a reset token.

**Request body**
```json
{ "token": "<reset_token>", "new_password": "NewPass2!" }
```

**Response `200`**
```json
{ "message": "Password reset successfully." }
```

---

## Documents

### GET /documents
List all documents owned by the current user.  *(Requires auth)*

**Query params**
| Param  | Type | Default | Description           |
|--------|------|---------|-----------------------|
| skip   | int  | 0       | Pagination offset     |
| limit  | int  | 20      | Page size (max 100)   |
| status | str  | —       | Filter by doc status  |

**Response `200`**
```json
[
  {
    "document_id": 1,
    "filename": "report.pdf",
    "status": "ready",
    "page_count": 12,
    "file_size_mb": 1.4,
    "created_at": "2024-01-02T09:00:00Z"
  }
]
```

---

### POST /documents/upload
Upload a new document.  *(Requires auth)*

**Content-Type:** `multipart/form-data`

**Form fields**
| Field | Type | Description               |
|-------|------|---------------------------|
| file  | File | PDF or image (max 50 MB)  |

**Response `202`**
```json
{ "document_id": 2, "status": "pending", "message": "Document queued for processing." }
```

---

### GET /documents/{document_id}
Get metadata for a single document.  *(Requires auth)*

**Response `200`** — same shape as list item above.

---

### DELETE /documents/{document_id}
Delete a document and all associated chunks.  *(Requires auth)*

**Response `200`**
```json
{ "message": "Document deleted." }
```

---

## Chat

### POST /chat/query
Ask a question against selected documents.  *(Requires auth)*

**Request body**
```json
{
  "session_id": 1,
  "question": "What are the key findings in Q3?",
  "document_ids": [1, 2]
}
```

**Response `200`**
```json
{
  "answer": "The key findings in Q3 are...",
  "sources": [
    { "document_id": 1, "filename": "report.pdf", "page": 4, "chunk": "..." }
  ],
  "session_id": 1,
  "message_id": 15
}
```

---

## Sessions

### GET /sessions
List all chat sessions for the current user.  *(Requires auth)*

### POST /sessions
Create a new chat session.

**Request body** *(optional)*
```json
{ "title": "Q3 Analysis" }
```

### PATCH /sessions/{session_id}
Rename a session.

### DELETE /sessions/{session_id}
Delete a session and all its messages.

---

## Admin

All admin endpoints require `user_role == "admin"`.

### GET /admin/users — List all users
### PATCH /admin/users/{user_id} — Update user (role, active status)
### DELETE /admin/users/{user_id} — Delete user
### GET /admin/documents — List all documents across users
### GET /admin/stats — System statistics

---

## Audit Logs

### GET /audit
*(Admin only)* Retrieve audit log entries.

**Query params**
| Param     | Type | Default | Description               |
|-----------|------|---------|---------------------------|
| skip      | int  | 0       |                           |
| limit     | int  | 50      | Max 200                   |
| user_id   | int  | —       | Filter by user            |
| action    | str  | —       | Filter by action type     |

---

## Health

### GET /health
Returns system health status (no auth required).

**Response `200`**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```