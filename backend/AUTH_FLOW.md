# Authentication Flow Documentation

This document explains how JWT authentication works in FadMann.

## Overview

FadMann uses **JWT (JSON Web Tokens)** for authentication. JWT tokens are:
- **Signed**: Cryptographically signed, can't be tampered with
- **Self-contained**: Include user info, no database lookup needed
- **Stateless**: Server doesn't store tokens
- **Expiring**: Tokens expire after 7 days

## Authentication Flow

### 1. User Registration/Login

```
User → Frontend (login form)
    → POST /api/auth/login
    → Backend creates/updates user
    → Backend creates JWT token
    → Token returned to frontend
    → Frontend stores token in localStorage
```

**Request:**
```json
POST /api/auth/login
{
  "username": "alice",
  "display_name": "Alice"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "alice",
    "display_name": "Alice"
  }
}
```

### 2. Making Authenticated Requests

```
Frontend → GET /api/auth/me
         → Includes: Authorization: "Bearer {token}"
         → Backend validates token
         → If valid: returns user info
         → If invalid: returns 401 Unauthorized
```

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (if valid):**
```json
{
  "id": 1,
  "username": "alice",
  "display_name": "Alice",
  "bio": "",
  "avatar_url": ""
}
```

**Response (if invalid):**
```json
{
  "detail": "Invalid or expired token"
}
```
Status: 401 Unauthorized

### 3. WebSocket Connection

```
Frontend → WebSocket connection
         → URL: ws://localhost:8000/api/ws/{room_id}?token={jwt_token}
         → Backend validates token
         → If valid: connection accepted
         → If invalid: connection closed with error
```

**Connection URL:**
```
ws://localhost:8000/api/ws/1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Structure

A JWT token has 3 parts separated by dots:

```
header.payload.signature
```

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload
```json
{
  "sub": "1",           // User ID
  "username": "alice",  // Username
  "exp": 1234567890,    // Expiration timestamp
  "iat": 1234567890     // Issued at timestamp
}
```

### Signature
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret_key
)
```

## Token Validation Process

When a request comes in with a token:

1. **Extract token** from Authorization header
2. **Verify signature** - ensures token hasn't been tampered with
3. **Check expiration** - ensures token hasn't expired
4. **Extract user_id** from token payload
5. **Query database** for user (if needed)
6. **Return user object** or raise 401 error

## Protected Endpoints

These endpoints require a valid JWT token:

- `GET /api/auth/me` - Get current user
- `POST /api/rooms` - Create room
- `PUT /api/users/{id}/profile` - Update profile
- `WebSocket /api/ws/{room_id}` - Real-time chat

## Unprotected Endpoints

These endpoints don't require authentication:

- `POST /api/auth/login` - Login/register
- `GET /api/rooms` - List rooms (public)
- `GET /api/rooms/{id}/messages` - Get messages (public)
- `GET /api/users/{id}/profile` - Get profile (public)

## Frontend Implementation

### Storing Token
```javascript
// After login
localStorage.setItem('auth_token', data.token);
```

### Using Token in Requests
```javascript
// REST API requests
fetch('/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
  }
});

// WebSocket connection
const token = localStorage.getItem('auth_token');
const ws = new WebSocket(`ws://localhost:8000/api/ws/1?token=${token}`);
```

### Handling Expired Tokens
```javascript
// If you get 401, token is expired
if (response.status === 401) {
  localStorage.removeItem('auth_token');
  // Redirect to login
  showLogin();
}
```

## Security Notes

1. **Secret Key**: Change `SECRET_KEY` in `backend/auth.py` for production
2. **HTTPS**: Always use HTTPS in production (tokens in URLs are visible)
3. **Token Expiration**: Tokens expire after 7 days (configurable)
4. **Token Storage**: localStorage is fine for this app, but consider httpOnly cookies for production
5. **No Password**: This app doesn't use passwords (simplified for beginners)

## Token Expiration

Tokens expire after **7 days**. When a token expires:

1. User gets 401 Unauthorized on next request
2. Frontend should redirect to login
3. User logs in again to get new token

To implement token refresh:
- Add a refresh token endpoint
- Store refresh token separately
- Use refresh token to get new access token before expiration

## Troubleshooting

### "Invalid or expired token"
- Token has expired (7 days old)
- Token signature is invalid
- Token format is incorrect
- Solution: User needs to log in again

### "Not authenticated"
- No Authorization header sent
- Authorization header doesn't start with "Bearer "
- Solution: Check frontend is sending token correctly

### WebSocket connection fails
- Token not included in URL query parameter
- Token is expired
- Solution: Check token is in URL: `?token={token}`
