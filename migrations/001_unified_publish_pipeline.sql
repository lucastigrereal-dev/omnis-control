-- Pipeline unificado de publicacao (adaptado para local)
-- migrations/001_unified_publish_pipeline.sql

CREATE TABLE IF NOT EXISTS content_items (
    id              TEXT PRIMARY KEY,
    account_handle  TEXT NOT NULL DEFAULT '',
    title           TEXT NOT NULL,
    body            TEXT,
    caption         TEXT,
    hashtags        TEXT,
    media_urls      TEXT,
    format          TEXT NOT NULL DEFAULT 'post',
    status          TEXT NOT NULL DEFAULT 'idea',
    scheduled_at    TEXT,
    published_at    TEXT,
    external_post_id TEXT,
    idempotency_key TEXT,
    retry_count     INT DEFAULT 0,
    error_log       TEXT DEFAULT '[]',
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS publish_queue (
    id              TEXT PRIMARY KEY,
    content_item_id TEXT NOT NULL,
    priority        INT DEFAULT 5,
    locked_by       TEXT,
    locked_at       TEXT,
    attempts        INT DEFAULT 0,
    max_attempts    INT DEFAULT 3,
    next_attempt_at TEXT DEFAULT (datetime('now')),
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS content_transitions (
    id              TEXT PRIMARY KEY,
    content_item_id TEXT NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    actor           TEXT NOT NULL,
    reason          TEXT,
    payload         TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS publish_metrics (
    id              TEXT PRIMARY KEY,
    content_item_id TEXT NOT NULL,
    platform        TEXT NOT NULL DEFAULT 'instagram',
    likes           INT DEFAULT 0,
    comments        INT DEFAULT 0,
    shares          INT DEFAULT 0,
    reach           INT DEFAULT 0,
    impressions     INT DEFAULT 0,
    collected_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_content_status ON content_items(status);
CREATE INDEX IF NOT EXISTS idx_queue_next ON publish_queue(next_attempt_at);
