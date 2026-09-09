#!/usr/bin/env python3
"""
Step 3a: Insert chunks into Supabase pgvector table.

Usage:
    python insert_chunks_pgvector.py

Reads chunks_output.json and inserts all chunks into Supabase.
Requires: SUPABASE_URL and SUPABASE_KEY in .env

Requirements:
    pip install -r requirements-step3.txt
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load env
load_dotenv()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
INPUT_FILE = "chunks_output.json"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_URL or SUPABASE_KEY not found in .env. See .env.example")

print(f"🔗 Connecting to Supabase: {SUPABASE_URL.split('/')[-1]}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Connected to Supabase\n")

# Load chunks from JSON
print(f"📖 Loading chunks from {INPUT_FILE}...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data["chunks"]
metadata = data["metadata"]

print(f"✅ Loaded {len(chunks)} chunks")
print(f"   Model: {metadata['embedding_model']}")
print(f"   Dimension: {metadata['embedding_dimension']}")
print()

# Insert chunks in batches (Supabase has limits)
BATCH_SIZE = 100
inserted_count = 0
failed_count = 0

print("📤 Inserting chunks into pgvector...\n")

for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ")
    
    try:
        # Prepare records for insertion
        records = []
        for chunk in batch:
            record = {
                "chunk_id": chunk["chunk_id"],
                "project_name": chunk["project_name"],
                "file_path": chunk["file_path"],
                "file_type": chunk["file_type"],
                "chunk_type": chunk["chunk_type"],
                "content": chunk["content"],
                "chunk_name": chunk.get("chunk_name"),
                "line_range": chunk.get("line_range"),
                "embedding": chunk["embedding"],
                "created_at": chunk.get("created_at", datetime.now().isoformat())
            }
            records.append(record)
        
        # Insert batch
        response = supabase.table("code_chunks").insert(records).execute()
        inserted_count += len(batch)
        print(f"✅ {len(batch)} inserted")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        failed_count += len(batch)

print("\n" + "=" * 70)
print(f"✅ Inserted: {inserted_count} chunks")
if failed_count > 0:
    print(f"❌ Failed:  {failed_count} chunks")
print("=" * 70)

# Verify insertion
print("\n🔍 Verifying insertion in Supabase...")
try:
    response = supabase.table("code_chunks").select("COUNT(id)").execute()
    # Note: COUNT might not work with select(), try alternative
    
    # Better: fetch one chunk to verify
    response = supabase.table("code_chunks").select("*").limit(1).execute()
    if response.data:
        print(f"✅ Verification successful! Found chunks in database")
        sample = response.data[0]
        print(f"\n   Sample chunk:")
        print(f"   ID: {sample['chunk_id']}")
        print(f"   Project: {sample['project_name']}")
        print(f"   File: {sample['file_path']}")
        print(f"   Type: {sample['chunk_type']}")
        print(f"   Content preview: {sample['content'][:100]}...")
    else:
        print("⚠️  No chunks found in database")
except Exception as e:
    print(f"⚠️  Verification error: {e}")

print("\n✨ Step 3a complete! Chunks are now in pgvector.")
print("   Next: Run Streamlit app (streamlit run chatbot.py)")
