-- Step 3b: Create RPC function for vector similarity search
-- Run this in Supabase SQL editor after creating the code_chunks table

CREATE OR REPLACE FUNCTION search_code_chunks(
    query_embedding vector(384),
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    chunk_id varchar,
    project_name varchar,
    file_path varchar,
    file_type varchar,
    chunk_type varchar,
    content text,
    chunk_name varchar,
    line_range varchar,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        code_chunks.id,
        code_chunks.chunk_id,
        code_chunks.project_name,
        code_chunks.file_path,
        code_chunks.file_type,
        code_chunks.chunk_type,
        code_chunks.content,
        code_chunks.chunk_name,
        code_chunks.line_range,
        (1 - (code_chunks.embedding <=> query_embedding))::float AS similarity
    FROM code_chunks
    WHERE code_chunks.embedding IS NOT NULL
    ORDER BY code_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Usage in Python:
-- response = supabase.rpc('search_code_chunks', {
--     'query_embedding': query_embedding_list,
--     'match_count': 5
-- }).execute()
