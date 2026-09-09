#!/usr/bin/env python3
"""
Step 1: Clone all 11 GitHub repos locally into /repos/ folder.

Usage:
    python clone_repos.py

Output:
    repos/
    ├── MCP-LangGraph-agent/
    ├── job-alert-agent/
    ├── news-brain-/
    └── ... (9 more repos)

Requirements:
    pip install -r requirements-step1.txt
"""

import json
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from github import Github, GithubException

# Load env vars
load_dotenv()

# Config
CONFIG_FILE = "config.json"
REPOS_DIR = Path("repos")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("❌ GITHUB_TOKEN not found in .env file. See .env.example")

# Load repo list
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

GITHUB_USER = config["github_user"]
REPOS_LIST = config["repos"]

# Initialize GitHub client
print(f"🔐 Authenticating with GitHub as {GITHUB_USER}...")
try:
    github = Github(GITHUB_TOKEN)
    user = github.get_user(GITHUB_USER)
    print(f"✅ Authenticated. Found user: {user.login}\n")
except GithubException as e:
    print(f"❌ Auth failed: {e}")
    exit(1)

# Create repos directory
REPOS_DIR.mkdir(exist_ok=True)
print(f"📁 Repo directory: {REPOS_DIR.absolute()}\n")

# Clone each repo
success_count = 0
failed_repos = []

for i, repo_info in enumerate(REPOS_LIST, 1):
    repo_name = repo_info["name"]
    is_private = repo_info["private"]
    repo_path = REPOS_DIR / repo_name
    
    status = "[PRIVATE]" if is_private else "[PUBLIC]"
    print(f"{i:2d}. {repo_name:45s} {status}")
    
    try:
        # Fetch repo from GitHub
        repo = user.get_repo(repo_name)
        clone_url = repo.clone_url
        
        # Remove if exists
        if repo_path.exists():
            print(f"    ⚠️  Existing folder found, removing...")
            shutil.rmtree(repo_path)
        
        # Clone
        print(f"    📥 Cloning from {clone_url}...")
        os.system(f'git clone {clone_url} "{repo_path}"')
        
        # Verify
        if (repo_path / ".git").exists():
            file_count = sum(1 for _ in repo_path.rglob("*") if _.is_file())
            print(f"    ✅ Success ({file_count} files)\n")
            success_count += 1
        else:
            print(f"    ❌ Clone failed (no .git folder)\n")
            failed_repos.append(repo_name)
            
    except GithubException as e:
        print(f"    ❌ GitHub API error: {e}\n")
        failed_repos.append(repo_name)
    except Exception as e:
        print(f"    ❌ Error: {e}\n")
        failed_repos.append(repo_name)

# Summary
print("=" * 70)
print(f"✅ Cloned: {success_count}/{len(REPOS_LIST)}")
if failed_repos:
    print(f"❌ Failed:  {', '.join(failed_repos)}")
print("=" * 70)

# List cloned repos
print(f"\n📂 Repos in {REPOS_DIR}:")
for folder in sorted(REPOS_DIR.iterdir()):
    if folder.is_dir():
        file_count = sum(1 for _ in folder.rglob("*") if _.is_file())
        print(f"   {folder.name:45s} ({file_count:6d} files)")

print("\n✨ Step 1 complete! Next: chunking & embedding.")
