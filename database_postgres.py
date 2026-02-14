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


# Global instance
db: Optional[Database] = None

async def init_db():
    """Initialize database."""
    global db
    db = Database()
    await db.init()
    return db
