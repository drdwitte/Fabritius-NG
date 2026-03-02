-- Add 'source' column to tags table
-- This tracks where the tag term/definition comes from (FABRITIUS, CUSTOM, ICONCLASS, AAT, etc.)
-- This is different from 'provenance' in artwork-tags which tracks how a tag was assigned to a specific artwork

-- Step 1: Add source column with default value
ALTER TABLE tags 
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'CUSTOM';

-- Step 2: Update all existing tags to have source = 'FABRITIUS'
-- (assuming all existing tags came from the original FABRITIUS dataset)
UPDATE tags 
SET source = 'FABRITIUS' 
WHERE source IS NULL OR source = 'CUSTOM';

-- Step 3: Make source NOT NULL with default 'CUSTOM' for new tags
ALTER TABLE tags 
ALTER COLUMN source SET NOT NULL,
ALTER COLUMN source SET DEFAULT 'CUSTOM';

-- Step 4: Add index for efficient filtering by source
CREATE INDEX IF NOT EXISTS idx_tags_source ON tags(source);

-- Step 5: Add comment to document the column
COMMENT ON COLUMN tags.source IS 'Source thesaurus for this tag: FABRITIUS (original dataset), CUSTOM (user-created), ICONCLASS, AAT, GARNIER, etc.';

-- Verify the migration
SELECT 
    source,
    COUNT(*) as tag_count
FROM tags
GROUP BY source
ORDER BY tag_count DESC;
