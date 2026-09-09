#!/usr/bin/env python3
"""
Step 3b: Streamlit Chat App for Code Knowledge Base

Query your indexed code repos with Groq LLM + pgvector similarity search.
Citations link to source files and line ranges.

Usage:
    streamlit run chatbot.py

Requirements:
    pip install -r requirements-step3.txt

Environment (.env):
    SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from supabase import create_client, Client
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np

# ============================================================================
# STREAMLIT PAGE CONFIG (Must be the absolute first Streamlit command)
# ============================================================================
st.set_page_config(
    page_title="Code Knowledge Base",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load env
load_dotenv()

# ============================================================================
# CONFIG & INIT
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not SUPABASE_URL or not SUPABASE_KEY or not GROQ_API_KEY:
    st.error("❌ Missing environment variables. Check .env file.")
    st.stop()

# Initialize Supabase client
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Groq client
@st.cache_resource
def get_groq():
    return Groq(api_key=GROQ_API_KEY)

# Initialize embedding model
@st.cache_resource
def get_embedder():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

supabase: Client = get_supabase()
groq_client = get_groq()
embedder = get_embedder()

# ============================================================================
# MAIN UI HEADER
# ============================================================================

st.title("🧠 Code Knowledge Base")
st.markdown("Query your indexed code repos. Powered by pgvector + Groq.")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("⚙️ Settings")
    
    top_k = st.slider(
        "Retrieve top K chunks",
        min_value=1,
        max_value=10,
        value=5,
        help="How many chunks to retrieve from pgvector"
    )
    
    model = st.selectbox(
        "Groq Model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b", "groq/compound"],
        index=0,
        help="Which Groq model to use for answers"
    )
    
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Lower = more deterministic, higher = more creative"
    )
    
    st.divider()
    st.subheader("📊 Database Stats")
    
    try:
        # Try to get chunk count
        response = supabase.table("code_chunks").select("*").limit(1).execute()
        if response.data:
            st.success("✅ Connected to pgvector")
        else:
            st.warning("⚠️ No chunks in database yet")
    except Exception as e:
        st.error(f"❌ Connection error: {e}")

# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Query input
query = st.chat_input("Ask about your code... (e.g., How do I implement a job scorer with Pydantic?)")

if query:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": query})
    
    with st.chat_message("user"):
        st.markdown(query)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base..."):
            try:
                # 1. Embed query
                query_embedding = embedder.encode(query).tolist()
                
                # 2. Search pgvector
                st.write("📌 Found relevant chunks:")
                response = supabase.rpc(
                    "search_code_chunks",
                    {
                        "query_embedding": query_embedding,
                        "match_count": top_k
                    }
                ).execute()
                
                chunks = []
                if response.data:
                    chunks = response.data
                else:
                    # Fallback: direct similarity search using SQL
                    try:
                        st.warning("⚠️ Vector search RPC not configured. Using direct query fallback.")
                        all_chunks_response = supabase.table("code_chunks").select("*").execute()
                        
                        if all_chunks_response.data:
                            # Calculate similarity manually
                            similarities = []
                            for chunk in all_chunks_response.data:
                                if chunk.get("embedding"):
                                    emb = np.array(chunk["embedding"])
                                    query_emb = np.array(query_embedding)
                                    similarity = np.dot(emb, query_emb) / (np.linalg.norm(emb) * np.linalg.norm(query_emb))
                                    similarities.append((chunk, similarity))
                            
                            # Sort by similarity and get top K
                            similarities.sort(key=lambda x: -x)
                            chunks = [item for item in similarities[:top_k]]
                    except Exception as e:
                        st.error(f"❌ Search error: {e}")
                        chunks = []
                
                # Display retrieved chunks
                if chunks:
                    for i, chunk in enumerate(chunks, 1):
                        with st.expander(f"📄 {i}. {chunk['project_name']} / {chunk['file_path']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.code(chunk["content"], language=chunk.get("file_type", "python").replace(".", ""))
                            with col2:
                                st.markdown(f"**Type:** {chunk.get('chunk_type', 'unknown')}")
                                if chunk.get("line_range"):
                                    st.markdown(f"**Lines:** {chunk['line_range']}")
                                if chunk.get("chunk_name"):
                                    st.markdown(f"**Name:** {chunk['chunk_name']}")
                else:
                    st.info("No code snippets found matching this query context.")
                
                # 3. Call Groq with context
                st.write("\n🧠 Generating answer...")
                
                context = "\n\n".join([
                    f"From {c['project_name']}/{c['file_path']} ({c.get('chunk_type', 'code')}):\n```{c.get('file_type', 'python').replace('.', '')}\n{c['content']}\n```"
                    for c in chunks
                ])
                
                messages_for_groq = [
                    {
                        "role": "system",
                        "content": "You are a helpful code assistant with knowledge of multiple programming projects. Answer questions based on the code context provided. Always cite which project/file each snippet comes from."
                    },
                    {
                        "role": "user",
                        "content": f"Here is relevant code context from my projects:\n\n{context}\n\nBased on this context, please answer the following question:\n{query}\n\nIf the context doesn't contain relevant information, say so and provide general guidance."
                    }
                ]
                
                # Call Groq API
                chat_completion = groq_client.chat.completions.create(
                    messages=messages_for_groq,
                    model=model,
                    temperature=temperature,
                )
                
                # Fixed list index extraction bug here:
                answer = chat_completion.choices[0].message.content
                st.markdown(answer)
                
                # Append assistant reply to session state history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as main_err:
                st.error(f"❌ Application generated an execution error: {main_err}")
