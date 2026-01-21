# Backend Architecture Explanation

This document explains each file in the backend and how they work together.

## File Structure

```
backend/
├── __init__.py      # Makes backend a Python package
├── app.py          # Main FastAPI application (entry point)
├── database.py     # Database connection and setup
├── models.py       # Database table definitions (SQLAlchemy models)
├── routes.py       # REST API endpoints and WebSocket handler
└── websocket.py    # In-memory connection manager for real-time chat
```

## File-by-File Explanation

### 1. `app.py` - Main Application
**Purpose:** Creates and configures the FastAPI application.

**What it does:**
- Creates the FastAPI app instance
- Configures CORS (allows frontend to connect)
- Registers all API routes
- Initializes database on startup
- Creates default rooms
- Serves static frontend files

**Key concepts:**
- `@app.on_event("startup")` - Runs code when server starts
- Middleware - Processes requests before they reach routes
- Router inclusion - Adds routes from `routes.py`

---

### 2. `database.py` - Database Setup
**Purpose:** Configures SQLite database connection using SQLAlchemy.

**What it does:**
- Creates database engine (connection to SQLite file)
- Creates session factory (for database transactions)
- Provides `get_db()` function for routes to use
- Provides `init_db()` function to create tables

**Key concepts:**
- **Engine:** Manages database connections
- **Session:** Represents a database transaction
- **Base:** Base class that all models inherit from
- **Dependency injection:** `get_db()` is automatically called by FastAPI

**Why SQLite?**
- No separate database server needed
- Database is just a file (`data/fadmann.db`)
- Perfect for beginners and small apps
- Can migrate to PostgreSQL later easily

---

### 3. `models.py` - Database Models
**Purpose:** Defines database tables as Python classes.

**What it does:**
- Defines User, Room, RoomMember, Message tables
- Sets up relationships between tables
- Defines column types and constraints

**Key concepts:**
- **ORM (Object-Relational Mapping):** Tables as Python classes
- **Primary Key:** Unique identifier (`id`)
- **Foreign Key:** Reference to another table (`user_id`, `room_id`)
- **Relationships:** Easy access to related data (`user.messages`)

**Tables:**
1. **User** - Stores user accounts
2. **Room** - Stores chat rooms
3. **RoomMember** - Links users to rooms (many-to-many)
4. **Message** - Stores all chat messages

---

### 4. `routes.py` - API Endpoints
**Purpose:** Defines all HTTP endpoints and WebSocket handler.

**What it does:**
- Handles authentication (login, token validation)
- Provides REST endpoints (list rooms, create room, etc.)
- Handles WebSocket connections for real-time chat
- Manages user profiles

**REST Endpoints:**
- `POST /api/auth/login` - Login or create user
- `GET /api/auth/me` - Get current user
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create new room
- `GET /api/rooms/{id}/messages` - Get message history
- `GET /api/users/{id}/profile` - Get user profile
- `PUT /api/users/{id}/profile` - Update user profile

**WebSocket Endpoint:**
- `WS /api/ws/{room_id}` - Real-time chat connection

**Key concepts:**
- **Dependencies:** `Depends(get_db)` automatically provides database session
- **Pydantic models:** Validate request data
- **HTTPException:** Return error responses
- **Query parameters:** `?token=xyz` in WebSocket URL

---

### 5. `websocket.py` - Connection Manager
**Purpose:** Manages WebSocket connections in memory.

**What it does:**
- Tracks which users are connected to which rooms
- Broadcasts messages to all users in a room
- Handles typing indicators
- Cleans up dead connections

**Key concepts:**
- **In-memory storage:** Fast, no database queries needed
- **Connection tracking:** `{room_id: {user_id: websocket}}`
- **Broadcasting:** Send message to all users in room
- **Connection lifecycle:** Connect → Listen → Disconnect

**Why in-memory?**
- Fast: No database queries for real-time operations
- Simple: Perfect for beginners
- Good enough for small to medium deployments
- For large scale, consider Redis

---

## How It All Works Together

### 1. User Login Flow
```
User → POST /api/auth/login
     → routes.py creates/updates user in database
     → Returns token
     → Frontend stores token
```

### 2. Joining a Room Flow
```
User → GET /api/rooms
     → routes.py queries database for rooms
     → Returns list of rooms
     → User clicks room
     → Frontend connects to WebSocket
```

### 3. Sending a Message Flow
```
User types message → Frontend sends via WebSocket
                  → routes.py receives in websocket_endpoint
                  → Saves message to database (models.py)
                  → Broadcasts to all users in room (websocket.py)
                  → All connected users receive message instantly
```

### 4. Database Flow
```
Route needs data → Calls get_db() (database.py)
                → Gets database session
                → Queries models (models.py)
                → Returns data
                → Session automatically closed
```

---

## Key Design Decisions

### Why SQLAlchemy?
- Easy to use: Python classes instead of SQL
- Type-safe: Catches errors early
- Database-agnostic: Can switch databases easily

### Why In-Memory Connections?
- Fast: No database queries for real-time
- Simple: Perfect for beginners
- Good enough: Works for small to medium apps

### Why Token-Based Auth?
- Simple: Easy to understand
- Stateless: No server-side sessions
- Note: For production, use JWT with expiration

### Why Separate Files?
- **app.py:** Configuration and setup
- **database.py:** Database connection
- **models.py:** Data structure
- **routes.py:** API logic
- **websocket.py:** Real-time logic

This separation makes code:
- Easy to understand
- Easy to test
- Easy to maintain

---

## Next Steps

To extend the backend:

1. **Add file uploads:** Add file handling in `routes.py`
2. **Add voice messages:** Extend Message model in `models.py`
3. **Add reactions:** Create Reaction model in `models.py`
4. **Add notifications:** Create Notification model in `models.py`
5. **Add Redis:** Replace in-memory storage in `websocket.py` for scale

Each file has a clear purpose, making it easy to add features!
