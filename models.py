"""Pydantic data models for Twitter Monitor Bot."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Tweet(BaseModel):
    """Represents a Twitter tweet."""
    id: str
    text: str
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: str = ""  # Tweet URL
    media_urls: List[str] = Field(default_factory=list)
    
    class Config:
        frozen = True


class Channel(BaseModel):
    """Represents a Discord channel configuration."""
    id: int
    name: str
    webhook_url: str
    created_at: Optional[datetime] = None
    
    class Config:
        frozen = True


class MonitoredUser(BaseModel):
    """Represents a monitored Twitter user."""
    id: int
    username: str
    channel_id: int
    last_tweet_id: Optional[str] = None
    is_active: bool = True
    added_at: Optional[datetime] = None
    
    class Config:
        frozen = True


class SentTweet(BaseModel):
    """Represents a tweet that has been sent to Discord."""
    id: int
    tweet_id: str
    username: str
    channel_id: int
    text: Optional[str] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    class Config:
        frozen = True


class UserWithChannel(BaseModel):
    """Represents a monitored user with their channel details."""
    id: int
    username: str
    channel_id: int
    last_tweet_id: Optional[str] = None
    is_active: bool = True
    webhook_url: str
    
    class Config:
        frozen = True
