# Code Knowledge Base — Complete Setup Guide

## 🎯 What This Does

Personal code + docs knowledge base. Query all your GitHub repos in one place.

**Example:**
```
User: "How do I implement a job scorer with Pydantic?"
↓
[Searches 10,801 code chunks across 11 repos]
↓
Answer: "Use Pydantic BaseModel to validate... 
[From: job-alert-agent/src/scorer.py lines 45-78]
[Also see: chatbot-assistant/src/models.py]"
```

## 🏗️ Architecture

```
Step 1: Clone 11 GitHub repos locally
    ↓
Step 2: Chunk & embed (10,801 chunks, 384-dim vectors)
    ↓
Step 3: Store in Supabase pgvector + Streamlit UI
    ↓
Result: Query your code → Groq LLM answers with citations
```

## 📋 Quick Start (TL;DR)

### Prerequisites
- Python 3.10+
- GitHub account (personal access token)
- Supabase free account
- Groq API key

### Setup (~30 min)

#### Step 1: Clone Repos (5 min)
```bash
pip install -r requirements-step1.txt
python clone_repos.py
```
→ Creates `repos/` with 11 GitHub repos

#### Step 2: Chunk & Embed (15 min)
```bash
pip install -r requirements-step2.txt
python ingest_chunks.py
```
→ Creates `chunks_output.json` (10,801 chunks, 384-dim embeddings)

#### Step 3: Supabase + Streamlit (10 min)

**3a. Supabase setup (one-time, 3 min):**
1. Create account: https://supabase.com
2. Run SQL in dashboard:
   - `setup_supabase.sql` (create table + indexes)
   - `create_rpc_search.sql` (create search function)
3. Copy credentials to `.env`:
   ```
   SUPABASE_URL=...
   SUPABASE_KEY=...
   GROQ_API_KEY=...
   ```

**3b. Insert chunks (3 min):**
```bash
pip install -r requirements-step3.txt
python insert_chunks_pgvector.py
```
→ Uploads 10,801 chunks to pgvector

**3c. Run chat UI (2 min):**
```bash
streamlit run chatbot.py
```
→ Opens http://localhost:8501

## 📁 File Structure

```
code-knowledge-base/
├── README.md                        (this file)
├── .env.example                     (copy to .env, fill in secrets)
├── .gitignore                       (don't commit repos/, .env)
├── config.json                      (list of 11 repos)
├── chunks_output.json               (10,801 chunks + embeddings)
│
├── repos/                           (git-ignored)
│   ├── MCP-LangGraph-agent/
│   ├── job-alert-agent/
│   ├── news-brain-/
│   └── ... (8 more repos)
│
├── STEP 1: Clone Repos
│   ├── clone_repos.py
│   ├── requirements-step1.txt
│   └── README_STEP1.md
│
├── STEP 2: Chunk & Embed
│   ├── chunker.py
│   ├── embedder.py
│   ├── ingest_chunks.py
│   ├── requirements-step2.txt
│   └── README_STEP2.md
│
└── STEP 3: Supabase + Streamlit
    ├── setup_supabase.sql           (run in Supabase)
    ├── create_rpc_search.sql        (run in Supabase)
    ├── insert_chunks_pgvector.py    (run locally)
    ├── chatbot.py                   (streamlit run this)
    ├── requirements-step3.txt
    └── README_STEP3.md
```

## 🚀 Detailed Walkthrough

### Step 1: Clone Repos
**Time:** 5 min  
**What:** Clone 11 GitHub repos locally using personal access token  
**Files:** `clone_repos.py`, `requirements-step1.txt`, `README_STEP1.md`  
**Output:** `repos/` folder with all 11 repos

**Commands:**
```bash
# 1. Get GitHub token
# Go to https://github.com/settings/tokens
# Create token with 'repo' scope

# 2. Add to .env
GITHUB_TOKEN=gh_your_token_here

# 3. Install & run
pip install -r requirements-step1.txt
python clone_repos.py

# 4. Verify
ls repos/
# Should show 11 folders
```

**See:** `README_STEP1.md` for details

---

### Step 2: Chunk & Embed
**Time:** 15 min (first run with model download)  
**What:** Parse all 11 repos, chunk files by type (AST for Python, regex for JS, headers for Markdown, etc.), embed chunks with sentence-transformers  
**Files:** `chunker.py`, `embedder.py`, `ingest_chunks.py`, `requirements-step2.txt`, `README_STEP2.md`  
**Output:** `chunks_output.json` (134 MB, 10,801 chunks + 384-dim embeddings)

**Chunking Strategy:**
- `.py` files → AST parsing, chunk by function/class
- `.js` files → Regex parsing, chunk by function
- `.md` files → Split by headers (## Section)
- `.json` files → Chunk by top-level keys
- `.ipynb` files → Extract code cells
- `.pdf` files → Extract pages
- `.csv`/`.txt` files → Split by paragraphs

**Commands:**
```bash
# 1. Install
pip install -r requirements-step2.txt
# (Downloads ~130 MB embedding model first run)

# 2. Run
python ingest_chunks.py

# 3. Wait for completion
# Output: chunks_output.json (134.39 MB, 10,801 chunks)
```

**See:** `README_STEP2.md` for details

---

### Step 3: Supabase pgvector + Streamlit Chat
**Time:** 10 min  
**What:** Create Supabase pgvector table, insert chunks, run Streamlit UI  
**Files:** `setup_supabase.sql`, `create_rpc_search.sql`, `insert_chunks_pgvector.py`, `chatbot.py`, `requirements-step3.txt`, `README_STEP3.md`

#### 3a. Supabase Setup (3 min)
1. Create account at https://supabase.com
2. Create new project
3. In SQL Editor, run:
   - Copy all of `setup_supabase.sql` → Execute
   - Copy all of `create_rpc_search.sql` → Execute
4. Copy credentials to `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   GROQ_API_KEY=gsk_...
   ```

#### 3b. Insert Chunks (3 min)
```bash
pip install -r requirements-step3.txt
python insert_chunks_pgvector.py

# Output:
# ✅ Inserted: 10801 chunks
# ✨ Step 3a complete!
```

#### 3c. Run Chat UI (2 min)
```bash
streamlit run chatbot.py
# Opens http://localhost:8501
```

**Try these queries:**
- "How do I implement a job scorer with Pydantic?"
- "Show me how to use LangGraph with MCP"
- "How does the news-brain earnings tracker work?"

**See:** `README_STEP3.md` for details

---

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# Step 1
GITHUB_TOKEN=gh_your_token_here

# Step 3
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
GROQ_API_KEY=gsk_your_key_here

# Optional
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**⚠️ Never commit `.env` to Git!** It's in `.gitignore`.

---

## 🎯 Use Cases

1. **"How do I do X in my code?"** → Search knowledge base, get answer with code examples
2. **"What patterns do I use for Y?"** → Find similar patterns across projects
3. **"Debug error from project Z"** → Ask chatbot, get context from that project
4. **"Onboard to my codebase"** → New teammate queries knowledge base instead of reading docs

---

## 📊 What Gets Indexed

**11 GitHub Repos:**
1. MCP-LangGraph-agent (current active build)
2. job-alert-agent (live automation)
3. news-brain- (live dashboard)
4. multi-agent-rag-chatbot (RAG patterns)
5. chatbot-assistant (Aadsia Streamlit bot)
6. ResearchPilot (3-agent Telegram pipeline)
7. Cookwithlove (voice-recipe Telegram bot)
8. Grounding-Check-In-Tool (check-in logic)
9. Media-Entertainment-News-Automation-System (scraper)
10. excel-duplicate-checker-pro (Flask + data)
11. n8n-automation-portfolio (n8n workflows)

**Total:**
- 247 files processed
- 10,801 chunks created
- 384-dim embeddings for each chunk

---

## ⚡ Performance

| Step | Time | Notes |
|------|------|-------|
| **Step 1** | 5 min | Clone repos (depends on internet) |
| **Step 2** | 15 min (first run) | Embedding model download included |
| **Step 2** | 3-5 min (subsequent) | Model cached locally |
| **Step 3a** | 3 min | Supabase setup (one-time) |
| **Step 3b** | 3 min | Insert 10,801 chunks into pgvector |
| **Step 3c** | ~2-5 sec per query | Vector search + Groq LLM response |

---

## 🐛 Troubleshooting

### General
- **Missing dependency:** `pip install -r requirements-stepX.txt`
- **.env not found:** Copy `.env.example` to `.env`, fill in secrets
- **Windows path issues:** Use forward slashes or raw strings

### Step 1
- **Auth failed:** Check GitHub token has `repo` scope
- **Git not found:** Install from https://git-scm.com/download/win

### Step 2
- **Slow embedding:** First run downloads model (~130 MB). Subsequent runs cached.
- **CUDA memory:** Reduce batch_size to 8 in `ingest_chunks.py`

### Step 3
- **No chunks in DB:** Run `insert_chunks_pgvector.py`
- **Search returns nothing:** Verify RPC function created (`create_rpc_search.sql`)
- **Groq rate limit:** Free tier has limits, use `llama-3.1-8b` instead

**See individual README files for detailed troubleshooting.**

---

## 🚀 Next Steps / Extensions

- **Auto-refresh:** Schedule weekly runs of Steps 2-3b when repos update
- **Web deployment:** Deploy Streamlit to Streamlit Cloud / Heroku
- **Multi-user:** Add Streamlit secrets + auth for shared access
- **Analytics:** Track which code patterns are queried most
- **Integrations:** Slack bot, Discord bot, VS Code extension

---

## 📝 License & Credits

- **sentence-transformers:** https://www.sbert.net/
- **Supabase pgvector:** https://supabase.com/
- **Groq LLM:** https://groq.com/
- **Streamlit:** https://streamlit.io/

---

## ✨ You're Done!

Your personal code knowledge base is live. Query it anytime:

```bash
streamlit run chatbot.py
```

Enjoy! 🎉
