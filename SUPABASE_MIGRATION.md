# Supabase Migration Plan

## 1. Create Supabase Project
- Go to https://supabase.com
- Create new project (FREE tier)
- Get connection details:
  - SUPABASE_URL
  - SUPABASE_KEY (service_role)

## 2. Update Database Code
- Change from sqlite3 to psycopg2/asyncpg
- Update all SQL queries for PostgreSQL syntax
- Keep same table structure

## 3. Tables to Create
- monitored_users
- channels
- sent_tweets
- tweet_ratings

## 4. Environment Variables
Add to Render:
- DATABASE_URL=postgresql://...
- Or SUPABASE_URL + SUPABASE_KEY
