-- Supabase Setup SQL
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    webhook_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Monitored users table
CREATE TABLE IF NOT EXISTS monitored_users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    last_tweet_id TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sent tweets table
CREATE TABLE IF NOT EXISTS sent_tweets (
    id SERIAL PRIMARY KEY,
    tweet_id TEXT NOT NULL,
    username TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    text TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tweet_id, channel_id)
);

-- Tweet ratings table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default channels
INSERT INTO channels (name, webhook_url) VALUES
('AI', 'https://discord.com/api/webhooks/...'),
('CRYPTO', 'https://discord.com/api/webhooks/...'),
('PROMPT', 'https://discord.com/api/webhooks/...'),
('STATS', 'https://discord.com/api/webhooks/...'),
('alerts', 'https://discord.com/api/webhooks/...')
ON CONFLICT (name) DO NOTHING;

-- Insert monitored users (add your own)
INSERT INTO monitored_users (username, channel_id) VALUES
('godofprompt', 3),
('tech_nurgaliyev', 1),
('jaro3th', 1)
ON CONFLICT (username) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sent_tweets_tweet_id ON sent_tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_sent_tweets_channel ON sent_tweets(channel_id);
CREATE INDEX IF NOT EXISTS idx_ratings_tweet_id ON tweet_ratings(tweet_id);
CREATE INDEX IF NOT EXISTS idx_users_channel ON monitored_users(channel_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON monitored_users(is_active);
