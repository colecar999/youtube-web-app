-- backend/supabase_tables.sql

-- Table: channels
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT,
    link_to_channel TEXT,
    about TEXT,
    number_of_total_videos INTEGER,
    number_of_retrieved_videos INTEGER,
    ids_of_retrieved_videos JSONB,
    subscribers INTEGER,
    channel_retrieval_date TIMESTAMP
);

-- Table: videos
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    duration TEXT,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    retrieval_date TIMESTAMP,
    tags TEXT,
    interviewees TEXT,
    processing_status TEXT,
    error_message TEXT
);

-- Table: comments
CREATE TABLE IF NOT EXISTS comments (
    video_id TEXT,
    comment_id TEXT PRIMARY KEY,
    comment_author TEXT,
    comment_likes INTEGER,
    comment_published_at TIMESTAMP,
    comment_updated_at TIMESTAMP,
    comment_parent_id TEXT,
    comment_text TEXT,
    comment_retrieval_date TIMESTAMP
);

-- Table: transcripts
CREATE TABLE IF NOT EXISTS transcripts (
    video_id TEXT PRIMARY KEY,
    transcript JSONB,
    retrieval_date TIMESTAMP,
    status TEXT
);

-- Table: tags
CREATE TABLE IF NOT EXISTS tags (
    video_id TEXT,
    tag TEXT,
    processed_date TIMESTAMP
);
