-- If table already exists, fix the vector dimension
-- ALTER TABLE iconographic_tags ALTER COLUMN tag_embedding TYPE vector(1536);

CREATE TABLE IF NOT EXISTS iconographic_tags (
    id BIGSERIAL PRIMARY KEY,
    label TEXT NOT NULL UNIQUE,
    description TEXT,
    tag_embedding vector(1536),
    source TEXT DEFAULT 'fabritius_iconography',  -- tracking waar het vandaan komt
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS
ALTER TABLE iconographic_tags ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to read tags (for recommendations)
CREATE POLICY "Allow authenticated read access"
ON iconographic_tags
FOR SELECT
TO authenticated
USING (true);-- ============================================
-- VECTOR INDEX (optional but recommended for performance)
-- ============================================

-- Create IVFFlat index for fast similarity search
-- Lists parameter: rule of thumb is sqrt(total_rows) or rows/1000
-- For ~5000 tags: lists = 100 is reasonable
CREATE INDEX IF NOT EXISTS iconographic_tags_embedding_idx 
ON iconographic_tags 
USING ivfflat (tag_embedding vector_cosine_ops) 
WITH (lists = 100);


-- ============================================
-- STORED PROCEDURE for tag recommendations
-- ============================================

-- Simple function to find similar tags based on an artwork's embedding
-- Same pattern as vector_search but searches in iconographic_tags instead

-- this is called when we want to recommend tags for an artwork 
--based on its caption embedding

CREATE OR REPLACE FUNCTION match_iconographic_tags(
    query_embedding vector(1536),
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id bigint,
    label text,
    description text,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        label,
        description,
        1 - (tag_embedding <=> query_embedding) as similarity
    FROM iconographic_tags
    WHERE tag_embedding IS NOT NULL
    ORDER BY tag_embedding <=> query_embedding
    LIMIT match_count;
$$;

