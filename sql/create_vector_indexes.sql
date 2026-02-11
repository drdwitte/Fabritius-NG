-- Create vector indexes for performance optimization
-- Run this after embeddings are populated in the tables

-- Enable pgvector extension (should already be enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- FABRITIUS TABLE: Vector index for artwork caption embeddings
-- ============================================

-- Fix dimension if unrestricted (optional, uncomment if needed)
-- ALTER TABLE fabritius ALTER COLUMN caption_embedding TYPE vector(1536);

-- Create IVFFlat index for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS fabritius_caption_embedding_idx 
ON fabritius 
USING ivfflat (caption_embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: lists = 100 is a good default for ~100k records
-- Formula: lists ≈ rows / 1000
-- Adjust if you have more/fewer records

-- ============================================
-- PERFORMANCE NOTES
-- ============================================
-- IVFFlat index trade-offs:
-- - Build time: Fast
-- - Query time: 10-100x faster than full scan
-- - Recall: ~95% (approximate, not exact)
-- - Good for: < 1M records
--
-- Alternative: HNSW (better recall, slower build)
-- CREATE INDEX ... USING hnsw (caption_embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);
