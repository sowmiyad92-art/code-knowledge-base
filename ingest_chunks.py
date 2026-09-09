#!/usr/bin/env python3
"""
Step 2: Chunk & Embed

Walk through all 11 repos, chunk files by type, embed with sentence-transformers,
prepare for pgvector storage (JSON output for Step 3).

Usage:
    python ingest_chunks.py

Output:
    chunks_output.json (ready for pgvector insertion in Step 3)

Requirements:
    pip install -r requirements-step2.txt
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from chunker import chunk_file, ChunkMetadata
from embedder import Embedder, batch_embed_chunks
from datetime import datetime

# Load env
load_dotenv()

# Config
REPOS_DIR = Path("repos")
OUTPUT_FILE = "chunks_output.json"

# File types to process
PROCESSABLE_EXTENSIONS = {'.py', '.js', '.md', '.json', '.ipynb', '.pdf', '.txt', '.csv', '.tsv'}

# Folders to skip
SKIP_FOLDERS = {
    '__pycache__', '.git', 'node_modules', '.venv', 'venv',
    'env', 'build', 'dist', 'egg-info', '.pytest_cache',
    '.vscode', '.idea', 'migrations', '__pycache__'
}

# Files to skip
SKIP_FILES = {'.env', '.gitignore', '.DS_Store', 'package-lock.json', 'yarn.lock'}


def should_skip(path: Path) -> bool:
    """Check if path should be skipped"""
    # Check folders
    for part in path.parts:
        if part in SKIP_FOLDERS:
            return True
    
    # Check files
    if path.name in SKIP_FILES:
        return True
    
    # Check extension
    if path.suffix.lower() not in PROCESSABLE_EXTENSIONS:
        return True
    
    return False


def walk_repos() -> list:
    """Walk all repos and return list of processable files"""
    files = []
    
    for repo_path in sorted(REPOS_DIR.iterdir()):
        if not repo_path.is_dir():
            continue
        
        project_name = repo_path.name
        print(f"\n📁 {project_name}")
        
        for file_path in sorted(repo_path.rglob('*')):
            if file_path.is_file() and not should_skip(file_path):
                rel_path = file_path.relative_to(repo_path)
                files.append((project_name, file_path, rel_path))
        
        print(f"   Found {sum(1 for p, _, _ in files if p == project_name)} processable files")
    
    return files


def generate_chunk_id(project: str, file_rel_path: Path, chunk_index: int, chunk_name: str = None) -> str:
    """
    Generate unique chunk ID: project/file.ext:chunk_type:001
    Example: job-alert-agent/src/scorer.py:score_job:001
    """
    file_str = str(file_rel_path).replace('\\', '/')
    if chunk_name:
        return f"{project}/{file_str}:{chunk_name}:{chunk_index:03d}"
    else:
        return f"{project}/{file_str}:chunk:{chunk_index:03d}"


def main():
    print("=" * 70)
    print("Step 2: Chunking & Embedding")
    print("=" * 70)
    
    # Initialize embedder
    embedder = Embedder()
    
    # Collect files
    print("\n🔍 Scanning repos...")
    files = walk_repos()
    print(f"\n✅ Found {len(files)} processable files\n")
    
    # Process files and collect chunks
    all_chunks = []
    chunk_stats = {
        "total_files": 0,
        "total_chunks": 0,
        "chunks_by_type": {},
        "chunks_by_project": {},
        "errors": []
    }
    
    print("🔪 Chunking files...\n")
    
    for i, (project_name, file_path, rel_path) in enumerate(files, 1):
        # Skip if file is too large (>10MB)
        if file_path.stat().st_size > 10 * 1024 * 1024:
            print(f"{i:3d}. ⏭️  {rel_path} (too large, skipping)")
            continue
        
        print(f"{i:3d}. {rel_path} ...", end=" ")
        
        try:
            chunks = chunk_file(str(file_path))
            
            if chunks:
                print(f"✅ {len(chunks)} chunks")
                
                for chunk_idx, chunk_meta in enumerate(chunks):
                    chunk_record = {
                        "chunk_id": generate_chunk_id(project_name, rel_path, chunk_idx, chunk_meta.name),
                        "project_name": project_name,
                        "file_path": str(rel_path).replace('\\', '/'),
                        "file_type": rel_path.suffix.lower(),
                        "chunk_type": chunk_meta.chunk_type,
                        "content": chunk_meta.content,
                        "line_range": chunk_meta.line_range,
                        "chunk_name": chunk_meta.name,
                        "created_at": datetime.now().isoformat()
                    }
                    all_chunks.append(chunk_record)
                    
                    # Stats
                    chunk_stats["total_chunks"] += 1
                    chunk_stats["chunks_by_type"][chunk_meta.chunk_type] = \
                        chunk_stats["chunks_by_type"].get(chunk_meta.chunk_type, 0) + 1
                    chunk_stats["chunks_by_project"][project_name] = \
                        chunk_stats["chunks_by_project"].get(project_name, 0) + 1
                
                chunk_stats["total_files"] += 1
            else:
                print("(no chunks)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            chunk_stats["errors"].append(f"{rel_path}: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ Created {len(all_chunks)} chunks from {chunk_stats['total_files']} files")
    print("=" * 70)
    
    # Print stats
    print("\n📊 Chunks by type:")
    for chunk_type, count in sorted(chunk_stats["chunks_by_type"].items(), key=lambda x: -x[1]):
        print(f"   {chunk_type:15s}: {count:6d}")
    
    print("\n📊 Chunks by project:")
    for project, count in sorted(chunk_stats["chunks_by_project"].items(), key=lambda x: -x[1]):
        print(f"   {project:45s}: {count:6d}")
    
    if chunk_stats["errors"]:
        print(f"\n⚠️  Errors ({len(chunk_stats['errors'])}):")
        for error in chunk_stats["errors"][:5]:
            print(f"   {error}")
    
    # Embed chunks
    print("\n" + "=" * 70)
    print("🧠 Embedding chunks...")
    print("=" * 70)
    
    chunk_texts = [c["content"] for c in all_chunks]
    embeddings = batch_embed_chunks(embedder, chunk_texts, batch_size=32)
    
    # Add embeddings to records
    for chunk, embedding in zip(all_chunks, embeddings):
        chunk["embedding"] = embedding
    
    # Save to JSON (for Step 3: pgvector insertion)
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    
    output_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_chunks": len(all_chunks),
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dimension": 384,
            "stats": chunk_stats
        },
        "chunks": all_chunks
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(all_chunks)} chunks with embeddings")
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB")
    
    print("\n" + "=" * 70)
    print("✨ Step 2 complete! Output ready for Step 3 (pgvector storage)")
    print("=" * 70)


if __name__ == "__main__":
    main()
