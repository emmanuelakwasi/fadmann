"""
Input Validation Utilities

This module provides validation functions for user inputs like
usernames, room names, and messages. This prevents invalid data
from entering the database and improves security.

WHY VALIDATE?
- Security: Prevents injection attacks and malicious input
- Data quality: Ensures consistent, clean data
- User experience: Clear error messages for invalid input
"""
import re
from typing import Optional, Tuple

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

# Username: 3-20 characters, alphanumeric + underscore/hyphen
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')

# Room name: 2-50 characters, alphanumeric + spaces/hyphens/underscores
ROOM_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s_-]{2,50}$')

# Message: Non-empty, max 2000 characters
MAX_MESSAGE_LENGTH = 2000


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Rules:
    - 3-20 characters
    - Only letters, numbers, underscore, hyphen
    - No spaces
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 20:
        return False, "Username must be no more than 20 characters"
    
    if not USERNAME_PATTERN.match(username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_room_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate room name format.
    
    Rules:
    - 2-50 characters
    - Letters, numbers, spaces, hyphens, underscores
    - Cannot be only spaces
    
    Args:
        name: Room name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Room name cannot be empty"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Room name must be at least 2 characters"
    
    if len(name) > 50:
        return False, "Room name must be no more than 50 characters"
    
    if not ROOM_NAME_PATTERN.match(name):
        return False, "Room name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    # Check it's not just spaces
    if not name.replace(" ", ""):
        return False, "Room name cannot be only spaces"
    
    return True, None


def validate_message(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate message content.
    
    Rules:
    - Cannot be empty (after trimming whitespace)
    - Maximum 2000 characters
    
    Args:
        content: Message content to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content:
        return False, "Message cannot be empty"
    
    content = content.strip()
    
    if not content:
        return False, "Message cannot be only whitespace"
    
    if len(content) > MAX_MESSAGE_LENGTH:
        return False, f"Message must be no more than {MAX_MESSAGE_LENGTH} characters"
    
    return True, None


def validate_display_name(display_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate display name format.
    
    Rules:
    - 1-50 characters
    - Can contain letters, numbers, spaces, and common punctuation
    
    Args:
        display_name: Display name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not display_name:
        return False, "Display name cannot be empty"
    
    display_name = display_name.strip()
    
    if len(display_name) < 1:
        return False, "Display name must be at least 1 character"
    
    if len(display_name) > 50:
        return False, "Display name must be no more than 50 characters"
    
    # Allow letters, numbers, spaces, and common punctuation
    if not re.match(r'^[a-zA-Z0-9\s.,!?\-_]+$', display_name):
        return False, "Display name contains invalid characters"
    
    return True, None
