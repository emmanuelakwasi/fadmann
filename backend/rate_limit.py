"""
Simple Rate Limiting

This module provides basic rate limiting to prevent spam and abuse.
It uses an in-memory dictionary to track message counts per user.

WHY RATE LIMIT?
- Prevents spam: Stops users from flooding chat
- Protects server: Reduces load from abusive users
- Fair usage: Ensures all users can chat

HOW IT WORKS:
- Tracks messages per user per time window
- Simple sliding window: last N seconds
- If limit exceeded, request is rejected

NOTE: This is a simple in-memory implementation.
For production at scale, use Redis or a proper rate limiting library.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# ============================================================================
# RATE LIMIT CONFIGURATION
# ============================================================================

# Maximum messages per time window
MAX_MESSAGES_PER_WINDOW = 10

# Time window in seconds (e.g., 10 messages per 60 seconds)
TIME_WINDOW_SECONDS = 60

# Store message timestamps per user
# Format: {user_id: [timestamp1, timestamp2, ...]}
user_message_timestamps: Dict[int, List[datetime]] = defaultdict(list)


# ============================================================================
# RATE LIMIT FUNCTIONS
# ============================================================================

def check_rate_limit(user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id: The user's ID
    
    Returns:
        Tuple of (allowed, error_message)
        - If allowed: (True, None)
        - If rate limited: (False, error_message)
    
    How it works:
    1. Get all message timestamps for this user
    2. Filter to only recent messages (within time window)
    3. Count messages in window
    4. If count >= limit, reject; otherwise allow
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=TIME_WINDOW_SECONDS)
    
    # Get user's message timestamps
    timestamps = user_message_timestamps.get(user_id, [])
    
    # Filter to only messages in current time window
    recent_messages = [
        ts for ts in timestamps
        if ts > window_start
    ]
    
    # Update stored timestamps (remove old ones)
    user_message_timestamps[user_id] = recent_messages
    
    # Check if limit exceeded
    if len(recent_messages) >= MAX_MESSAGES_PER_WINDOW:
        return False, f"Rate limit exceeded. Maximum {MAX_MESSAGES_PER_WINDOW} messages per {TIME_WINDOW_SECONDS} seconds."
    
    # Record this message attempt
    recent_messages.append(now)
    user_message_timestamps[user_id] = recent_messages
    
    return True, None


def reset_rate_limit(user_id: int):
    """
    Reset rate limit for a user (useful for testing or admin actions).
    
    Args:
        user_id: The user's ID
    """
    if user_id in user_message_timestamps:
        del user_message_timestamps[user_id]
