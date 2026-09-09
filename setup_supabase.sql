-- Step 3: Supabase Table Setup
-- Run this in Supabase SQL editor (https://supabase.com/dashboard)

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create code_chunks table with pgvector column
CREATE TABLE IF NOT EXISTS code_chunks (
    id BIGSERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,           -- "project/file.py:function_name:001"
    project_name VARCHAR(100) NOT NULL,              -- "job-alert-agent"
    file_path VARCHAR(500) NOT NULL,                 -- "src/agents/scorer.py"
    file_type VARCHAR(20) NOT NULL,                  -- ".py", ".js", ".md"
    chunk_type VARCHAR(50) NOT NULL,                 -- "function", "class", "section"
    content TEXT NOT NULL,                           -- Raw chunk content
    chunk_name VARCHAR(255),                         -- Function/class/section name
    line_range VARCHAR(50),                          -- "45-78" (for code), "page_1" (for PDF)
    embedding vector(384),                           -- all-MiniLM-L6-v2 embeddings (384 dims)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create IVFFLAT index for fast similarity search
CREATE INDEX ON code_chunks USING IVFFLAT (embedding vector_cosine_ops);

-- 4. Create useful supporting indexes
CREATE INDEX idx_project_name ON code_chunks(project_name);
CREATE INDEX idx_file_path ON code_chunks(file_path);
CREATE INDEX idx_chunk_type ON code_chunks(chunk_type);

-- 5. Enable Row Level Security (optional but recommended)
ALTER TABLE code_chunks ENABLE ROW LEVEL SECURITY;

-- 6. Create a public SELECT policy (allow anyone to query with anon key)
CREATE POLICY "Enable read access for all users" ON code_chunks
    FOR SELECT
    USING (true);

-- 7. Create a policy for INSERT (for your anon key to insert chunks)
CREATE POLICY "Enable insert for your key" ON code_chunks
    FOR INSERT
    WITH CHECK (true);

-- Done! The table is ready for chunk insertion.
-- You can verify by running:
-- SELECT COUNT(*) FROM code_chunks;
