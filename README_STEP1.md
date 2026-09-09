# Code Knowledge Base — Step 1: Repo Cloning

## Overview
Clone all 11 GitHub repos into a local `/repos/` directory. This is the foundation for Steps 2-3 (chunking, embedding, Streamlit UI).

## Setup

### 1. Create GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `public_repo`
4. Copy the token

### 2. Set Up Environment
```bash
# Copy .env template
cp .env.example .env

# Edit .env and paste your GitHub token
nano .env
# or use your editor (VS Code, etc.)
```

Update these in `.env`:
```
GITHUB_TOKEN=gh_your_token_here
```

### 3. Install Dependencies
```bash
pip install -r requirements-step1.txt
```

### 4. Run Clone Script
```bash
python clone_repos.py
```

**Expected output:**
```
✅ Cloned: 11/11

📂 Repos in repos/:
   MCP-LangGraph-agent             (  1,234 files)
   job-alert-agent                 (    456 files)
   news-brain-                     (    234 files)
   ... (8 more)

✨ Step 1 complete! Next: chunking & embedding.
```

## What Gets Cloned

| Repo | Private? | Purpose |
|------|----------|---------|
| MCP-LangGraph-agent | ❌ | Current active build |
| job-alert-agent | ✅ | Live automation |
| news-brain- | ❌ | Live earnings dashboard |
| multi-agent-rag-chatbot | ❌ | RAG patterns |
| chatbot-assistant | ❌ | Aadsia Streamlit bot |
| ResearchPilot | ✅ | 3-agent Telegram pipeline |
| Cookwithlove | ✅ | Voice-recipe Telegram bot |
| Grounding-Check-In-Tool | ❌ | Check-in logic |
| Media-Entertainment-News-Automation-System | ❌ | Scraper + automation |
| excel-duplicate-checker-pro | ❌ | Flask + data processing |
| n8n-automation-portfolio | ❌ | n8n workflows + ideas |

## Troubleshooting

### "GITHUB_TOKEN not found"
- Make sure `.env` file exists and contains `GITHUB_TOKEN=...`
- Verify you copied the entire token (no extra spaces)

### "Auth failed"
- Check token has `repo` + `public_repo` scopes
- Token may have expired; regenerate it

### Private repos not cloning
- GitHub token needs to have access to your private repos
- Token generated with `repo` scope should work

### Git not found
- Install Git: https://git-scm.com/download/win
- Restart terminal after install

## Next Steps
Once cloning is complete:
1. Verify all 11 repos exist in `repos/` folder
2. Spot-check one repo to see structure
3. Say "Step 1 done, move to Step 2"
4. We'll build the chunking + embedding logic

## Structure After Step 1
```
code-knowledge-base/
├── config.json
├── .env                          (your secrets, NOT in git)
├── .env.example                  (template)
├── .gitignore
├── clone_repos.py                (this script)
├── requirements-step1.txt
├── README_STEP1.md               (this file)
└── repos/                        (git-ignored)
    ├── MCP-LangGraph-agent/
    ├── job-alert-agent/
    ├── news-brain-/
    └── ... (8 more)
```
