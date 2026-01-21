# JWT Authentication Implementation

## Overview

FadMann uses **JWT (JSON Web Tokens)** for authentication. This is a simple, secure, and stateless authentication system.

## What is JWT?

JWT stands for JSON Web Token. It's a standard way to securely transmit information between parties.

**Key Benefits:**
- **Stateless**: Server doesn't need to store tokens
- **Signed**: Cryptographically signed, can't be tampered with
- **Self-contained**: Includes user info in the token itself
- **Standard**: Widely used and well-supported

## How It Works

### 1. Token Creation (Login)

When a user logs in:

```python
# backend/auth.py - create_access_token()
token = jwt.encode({
    "sub": user_id,      # User ID
    "username": username,
    "exp": expiration,   # Expires in 7 days
    "iat": issued_at     # When token was created
}, SECRET_KEY, algorithm="HS256")
```

The token is a string like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhbGljZSIsImV4cCI6MTY5OTk5OTk5OX0.signature
```

### 2. Token Validation (Every Request)

When a request comes in with a token:

```python
# backend/auth.py - verify_token()
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
# This automatically checks:
# - Signature is valid
# - Token hasn't expired
# - Token format is correct
```

### 3. User Extraction

```python
# Extract user_id from token
user_id = payload.get("sub")
# Query database for user
user = db.query(User).filter(User.id == user_id).first()
```

## Files Involved

### `backend/auth.py`
- `create_access_token()` - Creates JWT tokens
- `verify_token()` - Validates JWT tokens
- `get_user_from_token()` - Gets user from token
- `get_current_user()` - FastAPI dependency for protected routes

### `backend/routes.py`
- Uses `get_current_user` dependency for protected endpoints
- WebSocket endpoint validates JWT tokens from query parameter

## Protected Endpoints

These endpoints require a valid JWT token:

1. **GET /api/auth/me** - Get current user
   ```python
   @router.get("/auth/me")
   async def get_me(user: User = Depends(get_current_user)):
       # user is automatically validated
   ```

2. **POST /api/rooms** - Create room
   ```python
   @router.post("/rooms")
   async def create_room(user: User = Depends(get_current_user)):
       # user is automatically validated
   ```

3. **PUT /api/users/{id}/profile** - Update profile
   ```python
   @router.put("/users/{id}/profile")
   async def update_profile(current_user: User = Depends(get_current_user)):
       # current_user is automatically validated
   ```

4. **WebSocket /api/ws/{room_id}** - Real-time chat
   ```python
   @router.websocket("/ws/{room_id}")
   async def websocket_endpoint(token: str = Query(None)):
       # Token validated manually in function
   ```

## Frontend Usage

### Storing Token
```javascript
// After login
localStorage.setItem('auth_token', data.token);
```

### Using in REST Requests
```javascript
fetch('/api/auth/me', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
    }
});
```

### Using in WebSocket
```javascript
const token = localStorage.getItem('auth_token');
const ws = new WebSocket(`ws://localhost:8000/api/ws/1?token=${token}`);
```

## Security Notes

1. **Secret Key**: Change `SECRET_KEY` in `backend/auth.py` for production
2. **Token Expiration**: Tokens expire after 7 days
3. **HTTPS**: Always use HTTPS in production
4. **Token Storage**: localStorage is fine for this app

## Token Expiration

When a token expires:
- User gets 401 Unauthorized
- Frontend should redirect to login
- User logs in again to get new token

## Troubleshooting

**"Invalid or expired token"**
- Token has expired (7 days old)
- Token signature is invalid
- Solution: User needs to log in again

**"Not authenticated"**
- No Authorization header
- Header doesn't start with "Bearer "
- Solution: Check frontend is sending token correctly
