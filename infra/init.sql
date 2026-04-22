-- Postgres schema for Create with Tanmay
-- Metadata mirror of the Qdrant chunk store, plus user + usage tables.

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS sources (
    source_id        TEXT PRIMARY KEY,
    platform         TEXT NOT NULL,
    url              TEXT NOT NULL,
    format           TEXT NOT NULL,
    co_hosts         TEXT[] NOT NULL DEFAULT '{}',
    sponsor          TEXT,
    published_at     TIMESTAMPTZ,
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_uri          TEXT,
    status           TEXT NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS sources_platform_idx ON sources(platform);
CREATE INDEX IF NOT EXISTS sources_published_idx ON sources(published_at DESC);

CREATE TABLE IF NOT EXISTS chunk_metadata (
    chunk_id         TEXT PRIMARY KEY,
    source_id        TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    text             TEXT NOT NULL,
    text_tsv         tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
    start_seconds    DOUBLE PRECISION,
    end_seconds      DOUBLE PRECISION,
    topic_tags       TEXT[] NOT NULL DEFAULT '{}',
    register         TEXT,
    language_mix     JSONB NOT NULL DEFAULT '{}',
    entities         TEXT[] NOT NULL DEFAULT '{}',
    sentiment        REAL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunk_metadata_tsv_idx ON chunk_metadata USING GIN (text_tsv);
CREATE INDEX IF NOT EXISTS chunk_metadata_source_idx ON chunk_metadata(source_id);
CREATE INDEX IF NOT EXISTS chunk_metadata_tags_idx ON chunk_metadata USING GIN (topic_tags);

CREATE TABLE IF NOT EXISTS users (
    user_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_id         TEXT UNIQUE,
    email            TEXT UNIQUE,
    tier             TEXT NOT NULL DEFAULT 'free',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generations (
    id               BIGSERIAL PRIMARY KEY,
    user_id          UUID REFERENCES users(user_id) ON DELETE SET NULL,
    tab              TEXT NOT NULL,
    request          JSONB NOT NULL,
    response         JSONB,
    latency_ms       INTEGER,
    input_tokens     INTEGER,
    output_tokens    INTEGER,
    cost_usd         NUMERIC(10,5),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS generations_user_idx ON generations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS generations_tab_idx ON generations(tab, created_at DESC);
