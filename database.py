"""Database operations for Twitter Monitor Bot."""

import asyncio
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from config import settings
from models import Channel, MonitoredUser, SentTweet, UserWithChannel


class DatabaseError(Exception):
    """Custom database error."""
    pass


class Database:
    """SQLite database manager with retry logic."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # 100ms
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper configuration."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # Autocommit mode
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Database locked, retrying in {self.RETRY_DELAY}s... (attempt {attempt + 1})")
                    asyncio.sleep(self.RETRY_DELAY)
                else:
                    raise DatabaseError(f"Database operation failed: {e}")
        return None
    
    def init_database(self) -> None:
        """Initialize database with schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    webhook_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create monitored_users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitored_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    channel_id INTEGER NOT NULL,
                    last_tweet_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
                )
            """)
            
            # Create sent_tweets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_tweets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    text TEXT,
                    created_at TIMESTAMP,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)
            
            # Create tweet_ratings table (AI analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweet_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    score INTEGER NOT NULL, -- 1-10
                    category TEXT, -- bot, alpha, news, community, fluff
                    summary TEXT,
                    action TEXT, -- send, filter, highlight, follow_user, build_bot
                    reason TEXT,
                    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_channel 
                ON monitored_users(channel_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sent_tweets_lookup 
                ON sent_tweets(tweet_id, channel_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ratings_lookup 
                ON tweet_ratings(tweet_id, channel_id)
            """)
            
            logger.info("Database initialized successfully")
    
    # Channel operations
    def create_channel(self, name: str, webhook_url: str) -> int:
        """Create a new channel. Returns the channel ID."""
        def _create():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO channels (name, webhook_url) VALUES (?, ?)",
                    (name, webhook_url)
                )
                return cursor.lastrowid
        
        return self._execute_with_retry(_create)
    
    def get_channel_by_name(self, name: str) -> Optional[Channel]:
        """Get channel by name."""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, webhook_url, created_at FROM channels WHERE name = ?",
                    (name,)
                )
                row = cursor.fetchone()
                if row:
                    return Channel(
                        id=row["id"],
                        name=row["name"],
                        webhook_url=row["webhook_url"],
                        created_at=row["created_at"]
                    )
                return None
        
        return self._execute_with_retry(_get)
    
    def list_channels(self) -> List[dict]:
        """List all channels with user count."""
        def _list():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.name, c.webhook_url, c.created_at,
                           COUNT(u.id) as user_count
                    FROM channels c
                    LEFT JOIN monitored_users u ON c.id = u.channel_id AND u.is_active = 1
                    GROUP BY c.id
                    ORDER BY c.created_at
                """)
                return [
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "webhook_url": row["webhook_url"],
                        "created_at": row["created_at"],
                        "user_count": row["user_count"]
                    }
                    for row in cursor.fetchall()
                ]
        
        return self._execute_with_retry(_list)
    
    def delete_channel(self, name: str) -> bool:
        """Delete a channel and its users. Returns True if deleted."""
        def _delete():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM channels WHERE name = ?", (name,))
                return cursor.rowcount > 0
        
        return self._execute_with_retry(_delete)
    
    # User operations
    def add_user(self, username: str, channel_id: int, last_tweet_id: str = None) -> int:
        """Add a new monitored user. Returns the user ID."""
        def _add():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO monitored_users (username, channel_id, last_tweet_id, is_active)
                       VALUES (?, ?, ?, 1)
                       ON CONFLICT(username) DO UPDATE SET
                       channel_id = excluded.channel_id,
                       is_active = 1,
                       last_tweet_id = COALESCE(excluded.last_tweet_id, monitored_users.last_tweet_id)""",
                    (username, channel_id, last_tweet_id)
                )
                return cursor.lastrowid
        
        return self._execute_with_retry(_add)
    
    def remove_user(self, username: str) -> bool:
        """Remove a user from monitoring. Returns True if removed."""
        def _remove():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM monitored_users WHERE username = ?",
                    (username,)
                )
                return cursor.rowcount > 0
        
        return self._execute_with_retry(_remove)
    
    def get_user(self, username: str) -> Optional[MonitoredUser]:
        """Get user by username."""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT id, username, channel_id, last_tweet_id, is_active, added_at
                       FROM monitored_users WHERE username = ?""",
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    return MonitoredUser(
                        id=row["id"],
                        username=row["username"],
                        channel_id=row["channel_id"],
                        last_tweet_id=row["last_tweet_id"],
                        is_active=bool(row["is_active"]),
                        added_at=row["added_at"]
                    )
                return None
        
        return self._execute_with_retry(_get)
    
    def list_users(self, channel_name: str = None) -> List[dict]:
        """List all users or filter by channel."""
        def _list():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if channel_name:
                    cursor.execute("""
                        SELECT u.id, u.username, u.last_tweet_id, u.is_active, u.added_at,
                               c.name as channel_name, c.webhook_url
                        FROM monitored_users u
                        JOIN channels c ON u.channel_id = c.id
                        WHERE c.name = ?
                        ORDER BY u.added_at
                    """, (channel_name,))
                else:
                    cursor.execute("""
                        SELECT u.id, u.username, u.last_tweet_id, u.is_active, u.added_at,
                               c.name as channel_name, c.webhook_url
                        FROM monitored_users u
                        JOIN channels c ON u.channel_id = c.id
                        ORDER BY c.name, u.added_at
                    """)
                return [
                    {
                        "id": row["id"],
                        "username": row["username"],
                        "channel_name": row["channel_name"],
                        "last_tweet_id": row["last_tweet_id"],
                        "is_active": bool(row["is_active"]),
                        "added_at": row["added_at"],
                        "webhook_url": row["webhook_url"]
                    }
                    for row in cursor.fetchall()
                ]
        
        return self._execute_with_retry(_list)
    
    def get_active_users_with_channels(self) -> List[UserWithChannel]:
        """Get all active users with their channel webhook URLs."""
        def _get():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.id, u.username, u.channel_id, u.last_tweet_id, u.is_active,
                           c.webhook_url
                    FROM monitored_users u
                    JOIN channels c ON u.channel_id = c.id
                    WHERE u.is_active = 1
                """)
                return [
                    UserWithChannel(
                        id=row["id"],
                        username=row["username"],
                        channel_id=row["channel_id"],
                        last_tweet_id=row["last_tweet_id"],
                        is_active=bool(row["is_active"]),
                        webhook_url=row["webhook_url"]
                    )
                    for row in cursor.fetchall()
                ]
        
        return self._execute_with_retry(_get)
    
    def update_user_last_tweet_id(self, username: str, last_tweet_id: str) -> bool:
        """Update the last_tweet_id for a user."""
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE monitored_users SET last_tweet_id = ? WHERE username = ?",
                    (last_tweet_id, username)
                )
                return cursor.rowcount > 0
        
        return self._execute_with_retry(_update)
    
    def set_user_inactive(self, username: str) -> bool:
        """Set user as inactive (e.g., when account is suspended)."""
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE monitored_users SET is_active = 0 WHERE username = ?",
                    (username,)
                )
                return cursor.rowcount > 0
        
        return self._execute_with_retry(_update)
    
    def set_channel_inactive(self, channel_id: int) -> bool:
        """Set all users in a channel as inactive (e.g., when webhook is invalid)."""
        def _update():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE monitored_users SET is_active = 0 WHERE channel_id = ?",
                    (channel_id,)
                )
                return cursor.rowcount > 0
        
        return self._execute_with_retry(_update)
    
    # Sent tweets operations
    def is_tweet_sent(self, tweet_id: str, channel_id: int) -> bool:
        """Check if a tweet has already been sent to a channel."""
        def _check():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM sent_tweets WHERE tweet_id = ? AND channel_id = ?",
                    (tweet_id, channel_id)
                )
                return cursor.fetchone() is not None
        
        return self._execute_with_retry(_check)
    
    def record_sent_tweet(
        self,
        tweet_id: str,
        username: str,
        channel_id: int,
        text: str = None,
        created_at: datetime = None
    ) -> int:
        """Record that a tweet was sent to Discord."""
        def _record():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO sent_tweets (tweet_id, username, channel_id, text, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (tweet_id, username, channel_id, text, created_at)
                )
                return cursor.lastrowid
        
        return self._execute_with_retry(_record)


# Global database instance
db = Database()


# AI Rating operations (new)
def record_tweet_rating(
    self,
    tweet_id: str,
    username: str,
    channel_id: int,
    score: int,
    category: str,
    summary: str,
    action: str,
    reason: str
) -> int:
    """Record AI rating for a tweet."""
    def _record():
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO tweet_ratings 
                   (tweet_id, username, channel_id, score, category, summary, action, reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (tweet_id, username, channel_id, score, category, summary, action, reason)
            )
            return cursor.lastrowid
    
    return self._execute_with_retry(_record)


def get_rating_stats(self, days: int = 7) -> dict:
    """Get AI rating statistics for last N days."""
    def _get():
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(score) as avg_score,
                    COUNT(CASE WHEN score >= 7 THEN 1 END) as high_value,
                    COUNT(CASE WHEN score <= 3 THEN 1 END) as filtered,
                    category
                FROM tweet_ratings
                WHERE rated_at >= datetime('now', '-{} days')
                GROUP BY category
            """.format(days))
            
            rows = cursor.fetchall()
            return {
                "total": sum(r["total"] for r in rows),
                "avg_score": round(sum(r["avg_score"] * r["total"] for r in rows) / sum(r["total"] for r in rows), 2) if rows else 0,
                "high_value": sum(r["high_value"] for r in rows),
                "filtered": sum(r["filtered"] for r in rows),
                "by_category": {r["category"]: r["total"] for r in rows}
            }
    
    return self._execute_with_retry(_get)
