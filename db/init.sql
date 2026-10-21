CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE article (
    id            BIGSERIAL PRIMARY KEY,
    source_id     TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    url           TEXT,
    published_at  DATE,
    content       TEXT NOT NULL,
    content_hash  CHAR(64) NOT NULL,
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunk (
    id          BIGSERIAL PRIMARY KEY,
    article_id  BIGINT NOT NULL REFERENCES article(id) ON DELETE CASCADE,
    position    INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768) NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (to_tsvector('italian', content)) STORED
);

CREATE INDEX chunk_embedding_idx ON chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunk_tsv_idx ON chunk USING gin (tsv);