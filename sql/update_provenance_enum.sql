-- Update the provenance enum to include HUMAN and EXPERT values
-- This fixes the error: 'invalid input value for enum prov: "HUMAN"'

-- IMPORTANT: Run these statements ONE AT A TIME in separate queries
-- PostgreSQL requires enum values to be committed before use

-- Step 1: Check current enum values
SELECT 'Current enum values:' as info;
SELECT unnest(enum_range(NULL::prov))::text as current_values;

-- Step 2: Add HUMAN value (run this as a separate query)
ALTER TYPE prov ADD VALUE IF NOT EXISTS 'HUMAN';

-- Step 3: Add EXPERT value (run this as a separate query after step 2)
ALTER TYPE prov ADD VALUE IF NOT EXISTS 'EXPERT';

-- Step 4: Verify all enum values (run this last)
SELECT 'Updated enum values:' as info;
SELECT unnest(enum_range(NULL::prov))::text as all_values;

-- Expected output should include: FABRITIUS, AI, HUMAN, EXPERT
