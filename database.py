"""
Database module for Liar's Dice user management and leaderboard.
Handles user registration, authentication, and win tracking with pirate theme.
"""

import os
import sqlite3
import bcrypt
import re
from datetime import datetime, timedelta
from contextlib import contextmanager

# Use /app/data/ in production (Docker) so the volume-mounted directory persists the DB
if os.environ.get('FLASK_ENV') == 'production':
    os.makedirs('/app/data', exist_ok=True)
    DATABASE_PATH = '/app/data/liars_dice.db'
else:
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
                total_coins INTEGER NOT NULL DEFAULT 50,
                ranked_tier INTEGER NOT NULL DEFAULT 1,
                tier_wins INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_wins ON users(total_wins DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username COLLATE NOCASE)')
        # Migration: add total_coins column if missing
        try:
            conn.execute('SELECT total_coins FROM users LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE users ADD COLUMN total_coins INTEGER NOT NULL DEFAULT 50')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_coins ON users(total_coins DESC)')
        # Migration: add ranked_tier and tier_wins columns if missing
        try:
            conn.execute('SELECT ranked_tier FROM users LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE users ADD COLUMN ranked_tier INTEGER NOT NULL DEFAULT 1')
        try:
            conn.execute('SELECT tier_wins FROM users LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute('ALTER TABLE users ADD COLUMN tier_wins INTEGER NOT NULL DEFAULT 0')

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
                'SELECT username, avatar, total_wins, total_coins, created_at FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()

            return True, f"Welcome aboard, {username}! ⚓", {
                'username': user['username'],
                'avatar': user['avatar'],
                'wins': user['total_wins'],
                'coins': user['total_coins']
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
                    'wins': user['total_wins'],
                    'coins': user['total_coins']
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
                'SELECT username, avatar, total_wins, total_games, total_coins, ranked_tier, tier_wins FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()

            if user:
                return {
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins'],
                    'games': user['total_games'],
                    'coins': user['total_coins'],
                    'ranked_tier': user['ranked_tier'],
                    'tier_wins': user['tier_wins']
                }
            return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def get_user_ranked(username):
    """Return {tier, tier_wins} for a user, or None if not found."""
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT ranked_tier, tier_wins FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()
            if row:
                return {'tier': row['ranked_tier'], 'tier_wins': row['tier_wins']}
            return None
    except Exception as e:
        print(f"Error getting ranked progress: {e}")
        return None

def record_ranked_win(username, wins_to_advance):
    """
    Increment a user's tier_wins. If wins_to_advance is hit and not at max tier,
    advance the tier and reset tier_wins to 0.

    Args:
        username: user's name
        wins_to_advance: int or None — None means user is at max tier (no advancement)

    Returns:
        dict: {tier, tier_wins, advanced: bool} after update
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT ranked_tier, tier_wins FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()
            if not row:
                return None
            new_wins = row['tier_wins'] + 1
            new_tier = row['ranked_tier']
            advanced = False
            if wins_to_advance is not None and new_wins >= wins_to_advance:
                new_tier += 1
                new_wins = 0
                advanced = True
            conn.execute(
                'UPDATE users SET ranked_tier = ?, tier_wins = ? WHERE username = ? COLLATE NOCASE',
                (new_tier, new_wins, username)
            )
            return {'tier': new_tier, 'tier_wins': new_wins, 'advanced': advanced}
    except Exception as e:
        print(f"Error recording ranked win: {e}")
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

def increment_user_coins(username, amount):
    """Add coins to a user's account."""
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET total_coins = total_coins + ? WHERE username = ? COLLATE NOCASE',
                (amount, username)
            )
            user = conn.execute(
                'SELECT total_coins FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()
            return user['total_coins'] if user else 0
    except Exception as e:
        print(f"Error incrementing coins: {e}")
        return 0

def get_user_coins(username):
    """Get a user's coin balance."""
    try:
        with get_db() as conn:
            user = conn.execute(
                'SELECT total_coins FROM users WHERE username = ? COLLATE NOCASE',
                (username,)
            ).fetchone()
            return user['total_coins'] if user else 0
    except Exception as e:
        print(f"Error getting coins: {e}")
        return 0

def get_top_by_coins(limit=5):
    """Get top players by coins (Most Treasure)."""
    try:
        with get_db() as conn:
            users = conn.execute(
                'SELECT username, avatar, total_coins FROM users ORDER BY total_coins DESC, created_at ASC LIMIT ?',
                (limit,)
            ).fetchall()
            return [
                {
                    'rank': idx + 1,
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'coins': user['total_coins']
                }
                for idx, user in enumerate(users)
            ]
    except Exception as e:
        print(f"Error fetching coin leaderboard: {e}")
        return []

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

def update_user_avatar(username, avatar):
    """Update a user's avatar."""
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET avatar = ? WHERE username = ? COLLATE NOCASE',
                (avatar, username)
            )
            return True
    except Exception as e:
        print(f"Error updating avatar: {e}")
        return False

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

def get_user_rank(username):
    """Get a user's rank by coins."""
    try:
        with get_db() as conn:
            rows = conn.execute(
                'SELECT username FROM users ORDER BY total_coins DESC, created_at ASC'
            ).fetchall()
            for idx, row in enumerate(rows):
                if row['username'].lower() == username.lower():
                    return idx + 1
            return None
    except Exception as e:
        print(f"Error getting user rank: {e}")
        return None

def set_user_coins(username, amount):
    """Set a user's coin balance to a specific amount."""
    try:
        with get_db() as conn:
            conn.execute(
                'UPDATE users SET total_coins = ? WHERE username = ? COLLATE NOCASE',
                (amount, username)
            )
            return amount
    except Exception as e:
        print(f"Error setting coins: {e}")
        return 0

def get_all_users():
    """Get all users with their win counts and coins."""
    try:
        with get_db() as conn:
            users = conn.execute(
                'SELECT username, avatar, total_wins, total_coins FROM users ORDER BY total_coins DESC, username ASC'
            ).fetchall()
            return [
                {
                    'username': user['username'],
                    'avatar': user['avatar'],
                    'wins': user['total_wins'],
                    'coins': user['total_coins']
                }
                for user in users
            ]
    except Exception as e:
        print(f"Error fetching all users: {e}")
        return []

# Initialize database on module import
init_db()
