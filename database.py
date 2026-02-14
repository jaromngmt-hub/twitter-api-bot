"""PostgreSQL/SQLite database wrapper with Supabase support."""

import os
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime
import logging

from loguru import logger

# Try to import PostgreSQL driver
try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("asyncpg not available, falling back to SQLite")

# Try to import SQLite
try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class Database:
    """Database wrapper supporting both SQLite and PostgreSQL (Supabase)."""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
        self.is_postgres = self.db_url and self.db_url.startswith("postgresql://")
        self.pool = None
        
        if self.is_postgres and not POSTGRES_AVAILABLE:
            logger.error("PostgreSQL URL set but asyncpg not installed!")
            raise RuntimeError("asyncpg required for PostgreSQL")
        
        if self.is_postgres:
            logger.info("Using PostgreSQL (Supabase)")
        else:
            self.db_path = os.getenv("DATABASE_PATH", "./data/monitor.db")
            logger.info(f"Using SQLite: {self.db_path}")
    
    async def init(self):
        """Initialize database connection pool."""
        if self.is_postgres:
            self.pool = await asyncpg.create_pool(self.db_url, min_size=1, max_size=10)
            await self._create_postgres_tables()
        else:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            await self._create_sqlite_tables()
    
    async def _create_postgres_tables(self):
        """Create PostgreSQL tables."""
        async with self.pool.acquire() as conn:
            # channels table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    webhook_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # monitored_users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monitored_users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
                    last_tweet_id TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # sent_tweets table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_tweets (
                    id SERIAL PRIMARY KEY,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    text TEXT,
                    created_at TIMESTAMP,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tweet_id, channel_id)
                )
            """)
            
            # tweet_ratings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tweet_ratings (
                    id SERIAL PRIMARY KEY,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    category TEXT,
                    summary TEXT,
                    action TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("PostgreSQL tables created")
    
    async def _create_sqlite_tables(self):
        """Create SQLite tables (legacy)."""
        import aiosqlite
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    webhook_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS monitored_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    channel_id INTEGER NOT NULL,
                    last_tweet_id TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS sent_tweets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    text TEXT,
                    created_at TIMESTAMP,
                    UNIQUE(tweet_id, channel_id)
                );
                
                CREATE TABLE IF NOT EXISTS tweet_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    category TEXT,
                    summary TEXT,
                    action TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.commit()
            logger.info("SQLite tables created")
    
    async def execute(self, query: str, *args):
        """Execute a query."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        else:
            import aiosqlite
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(query, args)
                await conn.commit()
    
    async def fetchone(self, query: str, *args) -> Optional[Dict]:
        """Fetch one row."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        else:
            import aiosqlite
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(query, args) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
    
    async def fetchall(self, query: str, *args) -> List[Dict]:
        """Fetch all rows."""
        if self.is_postgres:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        else:
            import aiosqlite
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(query, args) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    # Convenience methods for the app
    async def get_all_users(self) -> List[Dict]:
        return await self.fetchall(
            "SELECT * FROM monitored_users WHERE is_active = TRUE"
        )
    
    async def get_all_channels(self) -> List[Dict]:
        return await self.fetchall("SELECT * FROM channels")
    
    async def is_tweet_sent(self, tweet_id: str, channel_id: int) -> bool:
        result = await self.fetchone(
            "SELECT 1 FROM sent_tweets WHERE tweet_id = $1 AND channel_id = $2"
            if self.is_postgres else
            "SELECT 1 FROM sent_tweets WHERE tweet_id = ? AND channel_id = ?",
            tweet_id, channel_id
        )
        return result is not None
    
    async def record_sent_tweet(self, tweet_id: str, username: str, 
                                channel_id: int, text: str, created_at: datetime):
        await self.execute(
            """INSERT INTO sent_tweets (tweet_id, username, channel_id, text, created_at)
               VALUES ($1, $2, $3, $4, $5)"""
            if self.is_postgres else
            """INSERT INTO sent_tweets (tweet_id, username, channel_id, text, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            tweet_id, username, channel_id, text, created_at
        )
    
    async def record_tweet_rating(self, tweet_id: str, username: str,
                                   channel_id: int, score: int, category: str,
                                   summary: str, action: str, reason: str):
        await self.execute(
            """INSERT INTO tweet_ratings 
               (tweet_id, username, channel_id, score, category, summary, action, reason)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"""
            if self.is_postgres else
            """INSERT INTO tweet_ratings 
               (tweet_id, username, channel_id, score, category, summary, action, reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            tweet_id, username, channel_id, score, category, summary, action, reason
        )
    
    async def update_user_last_tweet(self, username: str, tweet_id: str):
        await self.execute(
            "UPDATE monitored_users SET last_tweet_id = $1 WHERE username = $2"
            if self.is_postgres else
            "UPDATE monitored_users SET last_tweet_id = ? WHERE username = ?",
            tweet_id, username
        )
    
    async def update_user_last_tweet_id(self, username: str, tweet_id: str):
        """Alias for update_user_last_tweet."""
        await self.update_user_last_tweet(username, tweet_id)
    
    async def set_user_inactive(self, username: str):
        """Set user as inactive."""
        await self.execute(
            "UPDATE monitored_users SET is_active = FALSE WHERE username = $1"
            if self.is_postgres else
            "UPDATE monitored_users SET is_active = 0 WHERE username = ?",
            username
        )
    
    # ============== SYNC COMPATIBILITY METHODS ==============
    # These methods provide sync interface for legacy code (api.py, scheduler.py)
    
    def _run_sync(self, coro):
        """Run async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # Already in async context, create task
            return asyncio.create_task(coro)
        except RuntimeError:
            # No loop running, use run_until_complete
            return asyncio.run(coro)
    
    def get_active_users_with_channels(self) -> List[Dict]:
        """Get all active users with their channel webhook URLs (sync)."""
        async def _get():
            query = """
                SELECT u.id, u.username, u.channel_id, u.last_tweet_id, u.is_active,
                       c.name as channel_name, c.webhook_url
                FROM monitored_users u
                JOIN channels c ON u.channel_id = c.id
                WHERE u.is_active = TRUE
            """ if self.is_postgres else """
                SELECT u.id, u.username, u.channel_id, u.last_tweet_id, u.is_active,
                       c.name as channel_name, c.webhook_url
                FROM monitored_users u
                JOIN channels c ON u.channel_id = c.id
                WHERE u.is_active = 1
            """
            return await self.fetchall(query)
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in async context, this shouldn't happen with sync methods
                # Return empty list as fallback
                logger.warning("get_active_users_with_channels called from async context without await!")
                return []
            return loop.run_until_complete(_get())
        except RuntimeError:
            return asyncio.run(_get())
    
    def list_channels(self) -> List[Dict]:
        """Get all channels with user count (sync)."""
        async def _get():
            channels = await self.fetchall("SELECT * FROM channels")
            result = []
            for ch in channels:
                count_result = await self.fetchone(
                    "SELECT COUNT(*) as count FROM monitored_users WHERE channel_id = $1"
                    if self.is_postgres else
                    "SELECT COUNT(*) as count FROM monitored_users WHERE channel_id = ?",
                    ch['id']
                )
                result.append({
                    'id': ch['id'],
                    'name': ch['name'],
                    'webhook_url': ch['webhook_url'],
                    'user_count': count_result['count'] if count_result else 0,
                    'created_at': ch.get('created_at', '')
                })
            return result
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return loop.run_until_complete(_get())
        except RuntimeError:
            return asyncio.run(_get())
    
    def list_users(self, channel: Optional[str] = None) -> List[Dict]:
        """Get all users, optionally filtered by channel (sync)."""
        async def _get():
            if channel:
                ch = await self.fetchone(
                    "SELECT id FROM channels WHERE name = $1" if self.is_postgres else "SELECT id FROM channels WHERE name = ?",
                    channel
                )
                if not ch:
                    return []
                users = await self.fetchall(
                    "SELECT u.*, c.name as channel_name FROM monitored_users u JOIN channels c ON u.channel_id = c.id WHERE u.channel_id = $1"
                    if self.is_postgres else
                    "SELECT u.*, c.name as channel_name FROM monitored_users u JOIN channels c ON u.channel_id = c.id WHERE u.channel_id = ?",
                    ch['id']
                )
            else:
                users = await self.fetchall("""
                    SELECT u.*, c.name as channel_name 
                    FROM monitored_users u 
                    JOIN channels c ON u.channel_id = c.id
                """)
            
            result = []
            for u in users:
                result.append({
                    'id': u['id'],
                    'username': u['username'],
                    'channel_name': u.get('channel_name', ''),
                    'last_tweet_id': u.get('last_tweet_id'),
                    'is_active': u.get('is_active', True),
                    'added_at': u.get('added_at', '')
                })
            return result
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return loop.run_until_complete(_get())
        except RuntimeError:
            return asyncio.run(_get())
    
    def create_channel(self, name: str, webhook_url: str) -> int:
        """Create a new channel (sync)."""
        async def _create():
            result = await self.fetchone(
                "INSERT INTO channels (name, webhook_url) VALUES ($1, $2) RETURNING id"
                if self.is_postgres else
                "INSERT INTO channels (name, webhook_url) VALUES (?, ?) RETURNING id",
                name, webhook_url
            )
            return result['id'] if result else 0
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return 0
            return loop.run_until_complete(_create())
        except RuntimeError:
            return asyncio.run(_create())
    
    def delete_channel(self, name: str) -> bool:
        """Delete a channel (sync)."""
        async def _delete():
            result = await self.execute(
                "DELETE FROM channels WHERE name = $1"
                if self.is_postgres else
                "DELETE FROM channels WHERE name = ?",
                name
            )
            return True
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            return loop.run_until_complete(_delete())
        except RuntimeError:
            return asyncio.run(_delete())
    
    def get_channel_by_name(self, name: str) -> Optional[Dict]:
        """Get channel by name (sync)."""
        async def _get():
            return await self.fetchone(
                "SELECT * FROM channels WHERE name = $1"
                if self.is_postgres else
                "SELECT * FROM channels WHERE name = ?",
                name
            )
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return None
            return loop.run_until_complete(_get())
        except RuntimeError:
            return asyncio.run(_get())
    
    def add_user(self, username: str, channel_id: int, last_tweet_id: Optional[str] = None) -> int:
        """Add a new user (sync)."""
        async def _add():
            result = await self.fetchone(
                "INSERT INTO monitored_users (username, channel_id, last_tweet_id) VALUES ($1, $2, $3) RETURNING id"
                if self.is_postgres else
                "INSERT INTO monitored_users (username, channel_id, last_tweet_id) VALUES (?, ?, ?) RETURNING id",
                username, channel_id, last_tweet_id
            )
            return result['id'] if result else 0
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return 0
            return loop.run_until_complete(_add())
        except RuntimeError:
            return asyncio.run(_add())
    
    def remove_user(self, username: str) -> bool:
        """Remove a user (sync)."""
        async def _remove():
            await self.execute(
                "DELETE FROM monitored_users WHERE username = $1"
                if self.is_postgres else
                "DELETE FROM monitored_users WHERE username = ?",
                username
            )
            return True
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            return loop.run_until_complete(_remove())
        except RuntimeError:
            return asyncio.run(_remove())
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (sync)."""
        return self.list_users()
    
    def query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute raw query (sync)."""
        async def _query():
            return await self.fetchall(query, *params)
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            return loop.run_until_complete(_query())
        except RuntimeError:
            return asyncio.run(_query())


# Global instance - initialized on first use
db = Database()
