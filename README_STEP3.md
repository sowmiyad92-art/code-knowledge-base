# Code Knowledge Base — Step 3: Supabase pgvector + Streamlit Chat

## Overview
- Create Supabase pgvector table
- Insert 10,801 chunks with embeddings
- Build Streamlit chat UI with Groq LLM + vector search

**Result:** Query "How do I implement a job scorer?" → AI searches your code repos → gives answer with citations.

## Files

| File | Purpose |
|------|---------|
| `setup_supabase.sql` | Create table + indexes + RLS policies |
| `create_rpc_search.sql` | Create vector search RPC function |
| `insert_chunks_pgvector.py` | Insert chunks_output.json into pgvector |
| `chatbot.py` | Streamlit chat UI |
| `requirements-step3.txt` | Dependencies |

## Step-by-Step Setup

### 1. Create Supabase Account

1. Go to https://supabase.com
2. Click "Start your project" → "Create a new project"
3. Choose:
   - **Name:** `code-knowledge-base`
   - **Password:** Store securely
   - **Region:** Choose closest to you
4. Wait 1-2 min for project to initialize

### 2. Get Supabase Credentials

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`
3. Paste into `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

### 3. Create pgvector Table

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy all of `setup_supabase.sql` and paste
4. Click **Run**
   - Should see: `CREATE EXTENSION`, `CREATE TABLE`, `CREATE INDEX`, etc.
5. Verify:
   - Go to **Table Editor** → You should see `code_chunks` table

**What was created:**
- `code_chunks` table with 384-dim pgvector column
- IVFFLAT index for fast similarity search
- RLS policies for anon key access

### 4. Create Vector Search RPC Function

1. Go back to **SQL Editor** → **New Query**
2. Copy all of `create_rpc_search.sql` and paste
3. Click **Run**
   - Should see: `CREATE OR REPLACE FUNCTION`

**What was created:**
- `search_code_chunks()` RPC function
- Takes query embedding + K → returns top K similar chunks

### 5. Install Dependencies

```bash
pip install -r requirements-step3.txt
```

Installs:
- `streamlit` — chat UI
- `supabase` — Supabase client
- `groq` — Groq LLM API
- `sentence-transformers` — embeddings

### 6. Insert Chunks into pgvector

```bash
python insert_chunks_pgvector.py
```

**Expected output:**
```
🔗 Connecting to Supabase: your-project
✅ Connected to Supabase

📖 Loading chunks from chunks_output.json...
✅ Loaded 10801 chunks
   Model: sentence-transformers/all-MiniLM-L6-v2
   Dimension: 384

📤 Inserting chunks into pgvector...

Batch 1/108 (100 chunks)... ✅ 100 inserted
Batch 2/108 (100 chunks)... ✅ 100 inserted
...

======================================================================
✅ Inserted: 10801 chunks
======================================================================

✅ Verification successful! Found chunks in database
   Sample chunk:
   ID: job-alert-agent/src/scorer.py:score_job:001
   Project: job-alert-agent
   File: src/agents/scorer.py
   Type: function

✨ Step 3a complete! Chunks are now in pgvector.
```

**Troubleshooting:**
- **Auth error:** Check SUPABASE_URL + SUPABASE_KEY in `.env`
- **Table not found:** Run `setup_supabase.sql` first
- **Timeout:** Large batch might take time; try reducing BATCH_SIZE in script

### 7. Run Streamlit Chat App

```bash
streamlit run chatbot.py
```

**Expected:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://your-ip:8501
```

Browser automatically opens to http://localhost:8501

## Using the Chatbot

### Query Examples
- "How do I implement a job scorer with Pydantic?"
- "Show me how to use LangGraph with MCP"
- "How does the news-brain earnings tracker work?"
- "What patterns are used in the multi-agent-rag-chatbot?"

### How It Works
1. **User types query** → sent to Streamlit
2. **Embed query** → sentence-transformers (384 dims)
3. **Search pgvector** → top 5 similar chunks (using RPC function)
4. **Call Groq LLM** → "Here's the answer based on your code" + cites sources
5. **Display:** Answer + expandable chunks with line numbers

### UI Features
- **Settings sidebar:** Adjust top_k, model, temperature
- **Chat history:** Messages persist during session
- **Expandable chunks:** Click to see full code + metadata
- **Source citations:** Links to project/file/lines
- **Clear chat:** Button to reset conversation

## Customization

### Change Groq Model
Edit `chatbot.py` line 23:
```python
"llama-3.3-70b-versatile",  # Change this
"llama-3.1-8b",
"mixtral-8x7b-32768"
```

Or select in sidebar at runtime.

### Adjust Retrieval Size
Sidebar slider **"Retrieve top K chunks"** (default: 5)
- Lower = faster, less context
- Higher = slower, more context

### Change Temperature
Sidebar slider (default: 0.7)
- 0.0 = deterministic, factual
- 1.0 = balanced
- 2.0 = creative, exploratory

### Change Embedding Model
Edit `.env`:
```
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```
Or modify `chatbot.py` line 30:
```python
SentenceTransformer("your-model-name")
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements-step3.txt
```

### "SUPABASE_URL or SUPABASE_KEY not found"
- Check `.env` file exists and has credentials
- Don't share `.env` (add to `.gitignore`)

### "No chunks in database yet"
- Run `insert_chunks_pgvector.py` first
- Verify table is populated: Go to Supabase SQL Editor and run:
  ```sql
  SELECT COUNT(*) FROM code_chunks;
  ```

### Vector search returns no results
- Check RPC function was created (`create_rpc_search.sql`)
- Verify embeddings exist in chunks (non-null column)
- Try reducing top_k or rephrasing query

### Groq API error "Rate limit exceeded"
- Free tier has limits; wait a moment and retry
- Or use `llama-3.1-8b` (more generous limits)

### Streamlit slow/freezing
- First load caches models (~1-2 min)
- Subsequent queries are fast
- Reduce batch_size in `insert_chunks_pgvector.py` if issues persist

## Performance Notes

- **First run:** ~2-3 min (model caching + first embedding)
- **Typical query:** 2-5 sec (vector search + Groq response)
- **Groq response time:** Depends on model (8B = faster, 70B = better quality)

## Next Steps

1. ✅ Test a few queries in Streamlit
2. ✅ Verify citations match your code
3. ✅ Deploy (optional): Streamlit Cloud, Heroku, etc.
4. ✅ Refresh chunks (optional): Re-run `ingest_chunks.py` + `insert_chunks_pgvector.py` when you update repos

## Architecture Summary

```
User Query (Streamlit UI)
    ↓
Embed Query (sentence-transformers/all-MiniLM-L6-v2)
    ↓
Search pgvector (Supabase RPC: search_code_chunks)
    ↓
Retrieve Top 5 Chunks
    ↓
Context + Query → Groq LLM (llama-3.3-70b)
    ↓
Answer with Citations
    ↓
Display in Streamlit (expandable chunks, sources)
```

## File Structure After Step 3

```
code-knowledge-base/
├── repos/                           (all 11 cloned repos)
├── config.json                      (repo list)
├── chunks_output.json               (10,801 chunks + embeddings)
├── .env                             (secrets - DON'T COMMIT)
├── .env.example                     (template)
├── .gitignore
│
├── Step 1 files:
│   ├── clone_repos.py
│   ├── README_STEP1.md
│   └── requirements-step1.txt
│
├── Step 2 files:
│   ├── chunker.py
│   ├── embedder.py
│   ├── ingest_chunks.py
│   ├── README_STEP2.md
│   └── requirements-step2.txt
│
└── Step 3 files:
    ├── setup_supabase.sql           ← Run in Supabase SQL Editor
    ├── create_rpc_search.sql        ← Run in Supabase SQL Editor
    ├── insert_chunks_pgvector.py    ← Run locally
    ├── chatbot.py                   ← Run with Streamlit
    ├── README_STEP3.md
    └── requirements-step3.txt
```

## Done! 🎉

Your code knowledge base is now live. Query it anytime:
```bash
streamlit run chatbot.py
```

For help: Review README files or check error messages.
