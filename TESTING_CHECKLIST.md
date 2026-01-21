# Manual Testing Checklist for FadMann

Use this checklist to manually test all features of the chat application.

## Prerequisites
- [ ] Server is running (`python run.py`)
- [ ] Browser console is open (F12) to see errors
- [ ] Two browser windows/tabs open (to test multi-user features)

---

## 1. Health Check Endpoint

### Test: `/health` endpoint
- [ ] Open `http://localhost:8000/health` in browser
- [ ] Should return JSON with `status: "ok"` and `database: "connected"`
- [ ] Verify `timestamp` field is present and current

**Expected Result:** 
```json
{
  "status": "ok",
  "message": "FadMann is running",
  "timestamp": "2024-01-01T12:00:00.000000",
  "database": "connected"
}
```

---

## 2. Authentication & User Registration

### Test: Login with new username
- [ ] Go to `http://localhost:8000`
- [ ] Enter username: `testuser1`
- [ ] Enter display name: `Test User`
- [ ] Click "Enter Chat"
- [ ] Should successfully log in and show chat interface
- [ ] Check browser console - no errors
- [ ] Check localStorage - should have `auth_token`

### Test: Login with existing username
- [ ] Log out (clear localStorage or use different browser)
- [ ] Login with same username: `testuser1`
- [ ] Change display name to: `Test User Updated`
- [ ] Should log in successfully
- [ ] Display name should be updated

### Test: Username validation
- [ ] Try username: `ab` (too short)
- [ ] Should show error: "Username must be at least 3 characters"
- [ ] Try username: `test user` (with space)
- [ ] Should show error: "Username can only contain letters, numbers, underscores, and hyphens"
- [ ] Try username: `valid_user123`
- [ ] Should work correctly

### Test: Display name validation
- [ ] Try display name: `` (empty)
- [ ] Should show error
- [ ] Try display name: `A` (valid)
- [ ] Should work correctly

---

## 3. Room Management

### Test: List rooms
- [ ] After login, should see default rooms in sidebar:
  - General
  - Study Groups
  - Campus Events
- [ ] Rooms should show descriptions

### Test: Create room
- [ ] Click "+" button next to "Rooms" header
- [ ] Modal should appear
- [ ] Enter room name: `Test Room`
- [ ] Enter description: `This is a test room`
- [ ] Check "Public room" checkbox
- [ ] Click "Create Room"
- [ ] Room should appear in room list
- [ ] Should automatically select the new room

### Test: Room name validation
- [ ] Click "+" to create room
- [ ] Try room name: `A` (too short)
- [ ] Should show error: "Room name must be at least 2 characters"
- [ ] Try room name: `   ` (only spaces)
- [ ] Should show error: "Room name cannot be only spaces"
- [ ] Try room name: `Valid Room Name`
- [ ] Should work correctly

### Test: Duplicate room name
- [ ] Try to create room with name: `General` (existing room)
- [ ] Should show error: "Room with name 'General' already exists"

---

## 4. Message Sending & Receiving

### Test: Send message
- [ ] Select a room (e.g., "General")
- [ ] Type message: `Hello, world!`
- [ ] Press Enter or click Send
- [ ] Message should appear in chat
- [ ] Message should show your display name
- [ ] Message should show timestamp

### Test: Empty message prevention
- [ ] Try to send empty message (just spaces)
- [ ] Should not send (client-side validation)
- [ ] Try to send empty message via console: `websocket.send(JSON.stringify({type: "message", content: ""}))`
- [ ] Should receive error from server

### Test: Message too long
- [ ] Try to send message with 2001 characters
- [ ] Should show error: "Message must be no more than 2000 characters"

### Test: Receive messages (multi-user)
- [ ] Open two browser windows
- [ ] Login as different users in each
- [ ] Both join same room
- [ ] Send message from Window 1
- [ ] Message should appear in Window 2 immediately
- [ ] Message should show correct sender name

### Test: Message history
- [ ] Send several messages in a room
- [ ] Refresh the page
- [ ] Rejoin the room
- [ ] Previous messages should load
- [ ] Messages should be in chronological order

---

## 5. Rate Limiting

### Test: Rate limit spam prevention
- [ ] Select a room
- [ ] Send 10 messages quickly (within 60 seconds)
- [ ] All 10 should send successfully
- [ ] Try to send 11th message immediately
- [ ] Should receive error: "Rate limit exceeded. Maximum 10 messages per 60 seconds."
- [ ] Wait 60 seconds
- [ ] Should be able to send messages again

---

## 6. Typing Indicator

### Test: Typing indicator
- [ ] Open two browser windows with different users
- [ ] Both in same room
- [ ] Start typing in Window 1
- [ ] Window 2 should show: "[Username] is typing..."
- [ ] Stop typing for 2 seconds
- [ ] Typing indicator should disappear in Window 2

---

## 7. WebSocket Connection & Reconnection

### Test: Normal disconnect
- [ ] Join a room
- [ ] Close browser tab
- [ ] Check server console - should log "WebSocket disconnected"
- [ ] No errors should occur

### Test: Network interruption
- [ ] Join a room and send a message
- [ ] Disable network (turn off WiFi or unplug ethernet)
- [ ] Try to send message
- [ ] Re-enable network
- [ ] Should automatically reconnect within 3 seconds
- [ ] Should be able to send messages again

### Test: Server restart
- [ ] Join a room and send messages
- [ ] Stop server (Ctrl+C)
- [ ] Browser should detect disconnect
- [ ] Start server again (`python run.py`)
- [ ] Browser should attempt to reconnect
- [ ] Should be able to send messages after reconnection

### Test: Reconnection handling
- [ ] Join a room
- [ ] Refresh the page
- [ ] Should reconnect automatically
- [ ] Should not create duplicate connections
- [ ] Should load message history

---

## 8. Timestamps

### Test: Message timestamps
- [ ] Send a message
- [ ] Check timestamp format
- [ ] Recent messages should show: "just now", "5m ago", "2h ago"
- [ ] Older messages should show date: "Jan 1", "Yesterday 3:45 PM"
- [ ] Timestamps should use server time (not client time)

### Test: Timestamp accuracy
- [ ] Send message at 12:00:00
- [ ] Check message timestamp
- [ ] Should match server time (within 1-2 seconds)

---

## 9. Online Count (if implemented)

### Test: Online count display
- [ ] Open two browser windows
- [ ] Both users join same room
- [ ] Room list should show "2 online" for that room
- [ ] One user leaves
- [ ] Should update to "1 online" or remove count

---

## 10. Error Handling

### Test: Invalid token
- [ ] Manually set invalid token: `localStorage.setItem('auth_token', 'invalid')`
- [ ] Refresh page
- [ ] Should redirect to login screen
- [ ] Should clear invalid token

### Test: Expired token (simulate)
- [ ] Login successfully
- [ ] Manually expire token in database (if possible)
- [ ] Try to send message
- [ ] Should handle gracefully and prompt re-login

### Test: Server error handling
- [ ] Stop database (if possible)
- [ ] Try to send message
- [ ] Should show appropriate error message
- [ ] Should not crash the application

---

## 11. UI/UX

### Test: Responsive design
- [ ] Resize browser window
- [ ] UI should adapt (basic responsive)
- [ ] No elements should overflow

### Test: Footer tagline
- [ ] Scroll to bottom
- [ ] Should see footer with tagline: "Reconnect with your campus community, one message at a time."

### Test: Room selection
- [ ] Click different rooms
- [ ] Active room should be highlighted
- [ ] Message history should load for selected room
- [ ] Input should be enabled/disabled appropriately

---

## 12. Edge Cases

### Test: Special characters in messages
- [ ] Send message with: `Hello <script>alert('xss')</script>`
- [ ] Should be escaped and displayed as text (not executed)
- [ ] Send message with emojis: `Hello 😀 🎉`
- [ ] Should display correctly

### Test: Very long room name
- [ ] Try to create room with 51+ character name
- [ ] Should be rejected with validation error

### Test: Multiple rooms
- [ ] Create 5+ rooms
- [ ] All should appear in room list
- [ ] Should be able to switch between them
- [ ] Each room should have separate message history

---

## 13. Performance

### Test: Many messages
- [ ] Send 50+ messages in a room
- [ ] All should display correctly
- [ ] Scrolling should be smooth
- [ ] No performance degradation

### Test: Multiple users
- [ ] Open 5+ browser windows
- [ ] All join same room
- [ ] All send messages simultaneously
- [ ] All should receive all messages
- [ ] No messages should be lost

---

## Quick Test Summary

**Must Pass:**
1. ✅ Health endpoint returns OK
2. ✅ Can login/register
3. ✅ Can create rooms
4. ✅ Can send/receive messages
5. ✅ Empty messages are rejected
6. ✅ Rate limiting works (10 messages/60s)
7. ✅ WebSocket reconnects on disconnect
8. ✅ Timestamps display correctly
9. ✅ Validation works (username, room name)

**Nice to Have:**
- Typing indicator works
- Online count displays
- Multiple users can chat
- Error messages are clear

---

## Common Issues & Solutions

**Issue:** WebSocket won't connect
- **Check:** Token is in localStorage
- **Check:** Server is running
- **Check:** Browser console for errors

**Issue:** Messages not appearing
- **Check:** WebSocket connection status
- **Check:** Both users in same room
- **Check:** Server console for errors

**Issue:** Rate limit not working
- **Check:** Sending messages quickly enough
- **Check:** Server console for rate limit logs

**Issue:** Validation errors not showing
- **Check:** Browser console
- **Check:** Network tab for API responses

---

## Notes

- All timestamps use server time (UTC)
- Rate limiting is per-user, not per-room
- WebSocket reconnection is automatic (3 second delay)
- Empty messages are rejected on both client and server
- All user inputs are validated and sanitized
