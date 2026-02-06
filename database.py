"""
Database module for Liar's Dice user management and leaderboard.
Handles user registration, authentication, and win tracking with pirate theme.
"""

import sqlite3
import bcrypt
import re
from datetime import datetime, timedelta
from contextlib import contextmanager

DATABASE_PATH = 'liars_dice.db'

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database with users table."""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                avatar TEXT NOT NULL DEFAULT '🏴‍☠️',
                total_wins INTEGER NOT NULL DEFAULT 0,
                total_games INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_wins ON users(total_wins DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username COLLATE NOCASE)')

def validate_username(username):
    """Validate username format (3-20 alphanumeric characters)."""
    if not username or len(username) < 3 or len(username) > 20:
        return False, "Yer name be too short or too long! Need 3-20 characters, savvy?"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Only letters, numbers, and underscores allowed in yer name, matey!"
    return True, None

def validate_password(password):
    """Validate password format (4-10 digits only)."""
    if not password or len(password) < 4 or len(password) > 10:
        return False, "Shiver me timbers! Password must be 4-10 digits!"
    if not re.match(r'^[0-9]+$', password):
        return False, "Password must be digits only, landlubber! (e.g., 1234)"
    return True, None

def create_user(username, password, avatar='🏴‍☠️'):
    """
    Create a new user account with bcrypt password hashing.

    Args:
        username: User's chosen name (3-20 alphanumeric)
        password: User's password (4-10 digits)
        avatar: User's avatar emoji

    Returns:
        tuple: (success: bool, message: str, user_data: dict or None)
    """
    # Validate inputs
    valid, error = validate_username(username)
    if not valid:
        return False, error, None

    valid, error = validate_password(password)
    if not valid:
        return False, error, None

    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

    try:
        with get_db() as conn:
            conn.execute(
                'INSERT INTO users (username, password_hash, avatar) VALUES (?, ?, ?)',
                (username, password_hash, avatar)
            )
            user = conn.execute(
                'SELECT username, avatar, total_wins, created_at FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()

            return True, f"Welcome aboard, {username}! ⚓", {
                'username': user['username'],
                'avatar': user['avatar'],
                'wins': user['total_wins']
            }
    except sqlite3.IntegrityError:
        return False, "Arrr! That name's already taken by another scallywag!", None
    except Exception as e:
        return False, f"Database error: {str(e)}", None

def authenticate_user(username, password):
    """
    Authenticate user credentials.

    Args:
        username: User's username
        password: User's password (plaintext)

    Returns:
        tuple: (success: bool, message: str, user_data: dict or None)
    """
    if not username or not password:
        return False, "Username and password required, matey!", None

    try:
        with get_db() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()

            if not user:
                return False, "No pirate by that name found! Check yer spelling!", None

            # Verify password with bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
                return True, f"Welcome back, {user['username']}! Ready to plunder?", {
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins']
                }
            else:
                return False, "Wrong password, landlubber! Try again!", None
    except Exception as e:
        return False, f"Database error: {str(e)}", None

def get_user_by_username(username):
    """
    Fetch user data by username.

    Args:
        username: User's username

    Returns:
        dict or None: User data or None if not found
    """
    try:
        with get_db() as conn:
            user = conn.execute(
                'SELECT username, avatar, total_wins, total_games FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()

            if user:
                return {
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins'],
                    'games': user['total_games']
                }
            return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def increment_user_wins(username):
    """
    Increment win count for a user.

    Args:
        username: User's username

    Returns:
        bool: Success status
    """
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET total_wins = total_wins + 1 WHERE username = ? COLLATE NOCASE',
                (username,)
            )
            return True
    except Exception as e:
        print(f"Error incrementing wins: {e}")
        return False

def increment_user_games(username):
    """
    Increment total games played for a user.

    Args:
        username: User's username

    Returns:
        bool: Success status
    """
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET total_games = total_games + 1 WHERE username = ? COLLATE NOCASE',
                (username,)
            )
            return True
    except Exception as e:
        print(f"Error incrementing games: {e}")
        return False

def update_last_login(username):
    """
    Update user's last login timestamp.

    Args:
        username: User's username

    Returns:
        bool: Success status
    """
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ? COLLATE NOCASE',
                (username,)
            )
            return True
    except Exception as e:
        print(f"Error updating last login: {e}")
        return False

def get_top_pirates(limit=5):
    """
    Get top players by wins for the leaderboard.

    Args:
        limit: Number of top players to return (default 5)

    Returns:
        list: List of dicts with rank, username, avatar, wins
    """
    try:
        with get_db() as conn:
            users = conn.execute(
                'SELECT username, avatar, total_wins FROM users ORDER BY total_wins DESC, created_at ASC LIMIT ?',
                (limit,)
            ).fetchall()

            return [
                {
                    'rank': idx + 1,
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins']
                }
                for idx, user in enumerate(users)
            ]
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        return []

def reset_user_wins(username):
    """Reset wins to 0 for a specific user."""
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET total_wins = 0 WHERE username = ? COLLATE NOCASE',
                (username,)
            )
            return True
    except Exception as e:
        print(f"Error resetting user wins: {e}")
        return False

def reset_all_wins():
    """Reset wins to 0 for all users."""
    try:
        with get_db() as conn:
            conn.execute('UPDATE users SET total_wins = 0')
            return True
    except Exception as e:
        print(f"Error resetting all wins: {e}")
        return False

def get_all_users():
    """Get all users with their win counts."""
    try:
        with get_db() as conn:
            users = conn.execute(
                'SELECT username, avatar, total_wins FROM users ORDER BY total_wins DESC, username ASC'
            ).fetchall()
            return [
                {
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins']
                }
                for user in users
            ]
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []

# Initialize database on module import
init_db()
