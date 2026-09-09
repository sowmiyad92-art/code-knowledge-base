# Code Knowledge Base — Step 2: Chunking & Embedding

## Overview
Walk all 11 repos, chunk files by type (Python AST, Markdown headers, JSON keys, etc.), and embed each chunk using `sentence-transformers/all-MiniLM-L6-v2` (384 dims).

Output: `chunks_output.json` with ~1000-5000 chunks + embeddings, ready for pgvector storage in Step 3.

## Files

| File | Purpose |
|------|---------|
| `chunker.py` | File-type specific chunking logic |
| `embedder.py` | Embedding wrapper (sentence-transformers) |
| `ingest_chunks.py` | Main script: walk repos → chunk → embed → output JSON |
| `requirements-step2.txt` | Dependencies |

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements-step2.txt
```

This installs:
- `sentence-transformers` — embedding model
- `pdfplumber` — PDF text extraction
- `python-dotenv` — env var management

Model download (~130 MB): automatically cached on first run.

### 2. Run Ingestion
```bash
python ingest_chunks.py
```

**Expected output:**
```
======================================================================
Step 2: Chunking & Embedding
======================================================================

🔍 Scanning repos...
📁 MCP-LangGraph-agent
   Found 8 processable files
📁 job-alert-agent
   Found 12 processable files
...
✅ Found 247 processable files

🔪 Chunking files...
  1. src/main.py ...                    ✅ 3 chunks
  2. src/utils.js ...                   ✅ 5 chunks
  3. docs/README.md ...                 ✅ 2 chunks
...

======================================================================
✅ Created 2847 chunks from 247 files
======================================================================

📊 Chunks by type:
   function        :  1203
   class           :   456
   section         :   789
   object          :    99
   page            :   300

📊 Chunks by project:
   MCP-LangGraph-agent             :   267
   job-alert-agent                 :   312
   news-brain-                     :   334
   ... (8 more)

🧠 Embedding chunks...
📦 Loading embedding model: sentence-transformers/all-MiniLM-L6-v2...
✅ Model loaded. Dimension: 384

💾 Saving to chunks_output.json...
✅ Saved 2847 chunks with embeddings
   File: chunks_output.json
   Size: 145.2 MB

✨ Step 2 complete! Output ready for Step 3 (pgvector storage)
```

## Chunking Strategy

### Python (`.py`)
- **Method:** AST parsing
- **Unit:** Each function/class = 1 chunk
- **Example:** `def score_job(profile):` + body = 1 chunk
- **Metadata:** line_range, function/class name

### JavaScript (`.js`)
- **Method:** Regex function declarations
- **Unit:** Each function = 1 chunk
- **Example:** `const formatter = () => {...}` = 1 chunk
- **Metadata:** line_range, function name

### Markdown (`.md`)
- **Method:** Split by headers (## Heading)
- **Unit:** Each section = 1 chunk
- **Example:** `## Installation` + content = 1 chunk
- **Metadata:** section name

### JSON (`.json`)
- **Method:** Top-level key split
- **Unit:** Each key = 1 chunk
- **Example:** `{"config": {...}}` → 1 chunk

### Jupyter Notebooks (`.ipynb`)
- **Method:** Extract code + markdown cells
- **Unit:** Each cell = 1 chunk
- **Type:** "code" or "markdown"

### PDF (`.pdf`)
- **Method:** Page extraction + OCR fallback
- **Unit:** Each page = 1 chunk
- **Metadata:** page number

### Text/CSV (`.txt`, `.csv`)
- **Method:** Split by empty lines or 500-char limit
- **Unit:** Paragraph or chunk = 1 chunk

## Filtering

**Files processed:**
- `.py`, `.js`, `.md`, `.json`, `.ipynb`, `.pdf`, `.txt`, `.csv`, `.tsv`

**Folders skipped:**
- `__pycache__`, `.git`, `node_modules`, `.venv`, `build`, `dist`

**Files skipped:**
- `.env`, `.gitignore`, `.DS_Store`, `package-lock.json`

**Size limit:** Skip files > 10 MB

## Output Structure (`chunks_output.json`)

```json
{
  "metadata": {
    "created_at": "2024-12-15T10:30:45.123456",
    "total_chunks": 2847,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "stats": {
      "total_files": 247,
      "total_chunks": 2847,
      "chunks_by_type": {...},
      "chunks_by_project": {...},
      "errors": []
    }
  },
  "chunks": [
    {
      "chunk_id": "job-alert-agent/src/scorer.py:score_job:001",
      "project_name": "job-alert-agent",
      "file_path": "src/scorer.py",
      "file_type": ".py",
      "chunk_type": "function",
      "content": "def score_job(profile):\n    \"\"\"Score a job posting...\"\"\"",
      "line_range": "45-78",
      "chunk_name": "score_job",
      "embedding": [0.234, -0.156, 0.890, ..., 0.234],  # 384 floats
      "created_at": "2024-12-15T10:30:45.123456"
    },
    ... (2846 more chunks)
  ]
}
```

## Verification

After running, verify:
```bash
# Check file size (should be 100-200 MB)
ls -lh chunks_output.json

# Peek at structure (first 10 chunks)
python -c "import json; d=json.load(open('chunks_output.json')); print(json.dumps(d['chunks'][:2], indent=2)[:500])"

# Count chunks
python -c "import json; print('Total chunks:', len(json.load(open('chunks_output.json'))['chunks']))"
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'sentence_transformers'"
```bash
pip install sentence-transformers
```

### "CUDA out of memory" (if using GPU)
- Reduce batch_size in `ingest_chunks.py`: change `batch_size=32` to `batch_size=8`

### Chunks look wrong/incomplete
- Check `chunker.py` logic for that file type
- Open a sample chunk in `chunks_output.json` and verify content

### Very slow embedding
- First run downloads the model (~130 MB) — takes 2-5 min
- Subsequent runs are cached locally (fast)
- To verify: check `.cache/huggingface/` folder

## Next Steps

1. Verify `chunks_output.json` is created
2. Check file size (100-200 MB is normal)
3. Spot-check a few chunks for quality
4. Say "Step 2 done, move to Step 3"
5. We'll create Supabase pgvector table + insert chunks

## Time Estimate

- First run: 10-15 min (includes model download)
- Subsequent runs: 3-5 min
