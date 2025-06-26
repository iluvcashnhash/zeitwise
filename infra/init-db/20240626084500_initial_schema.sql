-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE content_type AS ENUM ('text', 'image', 'video', 'link');
CREATE TYPE source_type AS ENUM ('telegram', 'web', 'api', 'manual');

-- Users table to store user information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Add comment on users table
COMMENT ON TABLE users IS 'Stores user account information';

-- Chat sessions to group related messages
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Add comment on chat_sessions table
COMMENT ON TABLE chat_sessions IS 'Stores chat sessions that group related messages';

-- Chat messages within sessions
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    role message_role NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Add comment on chat_messages table
COMMENT ON TABLE chat_messages IS 'Stores individual chat messages within sessions';

-- Raw Telegram posts data
CREATE TABLE tg_posts_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    channel_username VARCHAR(100),
    content TEXT,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    post_date TIMESTAMPTZ,
    processed BOOLEAN DEFAULT false,
    UNIQUE(user_id, channel_id, post_id)
);

-- Add comment on tg_posts_raw table
COMMENT ON TABLE tg_posts_raw IS 'Stores raw Telegram posts data before processing';

-- Detox items for content moderation
CREATE TABLE detox_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type content_type NOT NULL,
    source_type source_type NOT NULL,
    source_id VARCHAR(100),
    is_processed BOOLEAN DEFAULT false,
    is_toxic BOOLEAN,
    toxicity_score FLOAT,
    categories JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Add comment on detox_items table
COMMENT ON TABLE detox_items IS 'Stores content items for toxicity detection and moderation';

-- User achievements
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,
    achieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    progress INT DEFAULT 1,
    metadata JSONB,
    UNIQUE(user_id, achievement_type)
);

-- Add comment on user_achievements table
COMMENT ON TABLE user_achievements IS 'Tracks user achievements and progress';

-- Create indexes for better query performance
CREATE INDEX idx_chat_sessions_user_id_created_at ON chat_sessions(user_id, created_at);
CREATE INDEX idx_chat_messages_session_id_created_at ON chat_messages(session_id, created_at);
CREATE INDEX idx_chat_messages_user_id_created_at ON chat_messages(user_id, created_at);
CREATE INDEX idx_tg_posts_raw_user_id_created_at ON tg_posts_raw(user_id, created_at);
CREATE INDEX idx_tg_posts_raw_channel_id_post_id ON tg_posts_raw(channel_id, post_id);
CREATE INDEX idx_detox_items_user_id_created_at ON detox_items(user_id, created_at);
CREATE INDEX idx_detox_items_is_processed_created_at ON detox_items(is_processed, created_at);
CREATE INDEX idx_user_achievements_user_id_created_at ON user_achievements(user_id, created_at);

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
BEFORE UPDATE ON chat_sessions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_messages_updated_at
BEFORE UPDATE ON chat_messages
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_detox_items_updated_at
BEFORE UPDATE ON detox_items
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
