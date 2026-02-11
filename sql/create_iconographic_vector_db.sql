-- If table already exists, fix the vector dimension
-- ALTER TABLE iconographic_tags ALTER COLUMN tag_embedding TYPE vector(1536);

-- ============================================
-- ICONOGRAPHIC TAGS TABLE
-- ============================================
-- This table is a clone of the 'tags' table with added embedding column
-- Used for tag recommendations based on vector similarity

CREATE TABLE IF NOT EXISTS iconographic_tags (
    id BIGSERIAL PRIMARY KEY,
    label TEXT NOT NULL UNIQUE,
    description TEXT,
    tag_embedding vector(1536),
    source TEXT DEFAULT 'fabritius_iconography',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================
-- INITIAL DATA POPULATION (run once)
-- ============================================
-- Copy existing tags from 'tags' table into 'iconographic_tags'
-- Uncomment and run this once to populate:

-- INSERT INTO iconographic_tags (label, description, created_at)
-- SELECT label, description, created_at 
-- FROM tags
-- ON CONFLICT (label) DO NOTHING;

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
USING (true);




