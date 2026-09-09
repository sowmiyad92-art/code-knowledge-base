"""
Chunking strategies for different file types.
Returns list of chunks with metadata: {content, chunk_type, line_range}
"""

import ast
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


class ChunkMetadata:
    """Container for chunk info"""
    def __init__(self, content: str, chunk_type: str, line_range: str = None, name: str = None):
        self.content = content
        self.chunk_type = chunk_type
        self.line_range = line_range
        self.name = name  # function/class name


def chunk_python_file(file_path: str) -> List[ChunkMetadata]:
    """
    Parse Python file using AST, chunk by function/class.
    Each function/class = 1 chunk (including docstrings + body).
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno - 1
                end = node.end_lineno or len(lines)
                chunk_content = '\n'.join(lines[start:end])
                chunks.append(ChunkMetadata(
                    content=chunk_content,
                    chunk_type="function",
                    line_range=f"{start+1}-{end}",
                    name=node.name
                ))
            elif isinstance(node, ast.ClassDef):
                start = node.lineno - 1
                end = node.end_lineno or len(lines)
                chunk_content = '\n'.join(lines[start:end])
                chunks.append(ChunkMetadata(
                    content=chunk_content,
                    chunk_type="class",
                    line_range=f"{start+1}-{end}",
                    name=node.name
                ))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_javascript_file(file_path: str) -> List[ChunkMetadata]:
    """
    Chunk JavaScript by function declarations (regex-based).
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Match: function name() or const name = () => or async function name()
        func_pattern = r'(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=|let\s+(\w+)\s*=|var\s+(\w+)\s*=)'
        
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3) or match.group(4)
            start_line = content[:match.start()].count('\n')
            
            # Find closing brace
            start_pos = match.end()
            brace_count = 0
            in_string = False
            end_pos = start_pos
            
            for i, char in enumerate(content[start_pos:], start=start_pos):
                if char in ('"', "'", '`') and (i == 0 or content[i-1] != '\\'):
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
            
            end_line = content[:end_pos].count('\n')
            chunk_content = content[match.start():end_pos]
            
            chunks.append(ChunkMetadata(
                content=chunk_content,
                chunk_type="function",
                line_range=f"{start_line+1}-{end_line+1}",
                name=func_name
            ))
    except (UnicodeDecodeError, Exception) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_markdown_file(file_path: str) -> List[ChunkMetadata]:
    """
    Split Markdown by headers (##, ###, ####).
    Each section = 1 chunk.
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        current_chunk = []
        current_header = None
        start_line = 0
        
        for i, line in enumerate(lines):
            if line.startswith('#'):
                # Save previous chunk
                if current_chunk and current_header:
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append(ChunkMetadata(
                        content=chunk_content,
                        chunk_type="section",
                        line_range=f"{start_line+1}-{i}",
                        name=current_header
                    ))
                
                # Start new chunk
                current_header = line.strip()
                current_chunk = [line]
                start_line = i
            else:
                current_chunk.append(line)
        
        # Save last chunk
        if current_chunk and current_header:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(ChunkMetadata(
                content=chunk_content,
                chunk_type="section",
                line_range=f"{start_line+1}-{len(lines)}",
                name=current_header
            ))
    except (UnicodeDecodeError, Exception) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_json_file(file_path: str) -> List[ChunkMetadata]:
    """
    Split JSON by top-level keys.
    Each key = 1 chunk.
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            for key, value in data.items():
                chunk_content = json.dumps({key: value}, indent=2)
                chunks.append(ChunkMetadata(
                    content=chunk_content,
                    chunk_type="object",
                    name=key
                ))
        else:
            # If top-level is array, return whole thing
            chunk_content = json.dumps(data, indent=2)
            chunks.append(ChunkMetadata(
                content=chunk_content,
                chunk_type="array",
                name="root"
            ))
    except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_ipynb_file(file_path: str) -> List[ChunkMetadata]:
    """
    Extract code and markdown cells from Jupyter notebook.
    Each cell = 1 chunk.
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        cells = notebook.get('cells', [])
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type')
            source = ''.join(cell.get('source', []))
            
            if source.strip():
                chunk_type = "code" if cell_type == "code" else "markdown"
                chunks.append(ChunkMetadata(
                    content=source,
                    chunk_type=chunk_type,
                    name=f"cell_{i}"
                ))
    except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_pdf_file(file_path: str) -> List[ChunkMetadata]:
    """
    Extract text from PDF, chunk by page or 1000-char limit.
    """
    chunks = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    chunks.append(ChunkMetadata(
                        content=text,
                        chunk_type="page",
                        line_range=f"page_{page_num}",
                        name=f"page_{page_num}"
                    ))
    except Exception as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_text_file(file_path: str) -> List[ChunkMetadata]:
    """
    Simple text file: chunk by lines or 500-char chunks.
    """
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by empty lines or max 500 chars
        lines = content.split('\n')
        current_chunk = []
        start_line = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            
            # Chunk when: empty line found OR chunk is 500 chars
            chunk_text = '\n'.join(current_chunk)
            if (line.strip() == '' and len(chunk_text) > 100) or len(chunk_text) > 500:
                chunks.append(ChunkMetadata(
                    content=chunk_text,
                    chunk_type="text",
                    line_range=f"{start_line+1}-{i+1}"
                ))
                current_chunk = []
                start_line = i + 1
        
        # Save remaining
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(ChunkMetadata(
                content=chunk_text,
                chunk_type="text",
                line_range=f"{start_line+1}-{len(lines)}"
            ))
    except (UnicodeDecodeError, Exception) as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return chunks


def chunk_file(file_path: str) -> List[ChunkMetadata]:
    """
    Route to appropriate chunking strategy based on file type.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.py':
        return chunk_python_file(file_path)
    elif suffix == '.js':
        return chunk_javascript_file(file_path)
    elif suffix == '.md':
        return chunk_markdown_file(file_path)
    elif suffix == '.json':
        return chunk_json_file(file_path)
    elif suffix == '.ipynb':
        return chunk_ipynb_file(file_path)
    elif suffix == '.pdf':
        return chunk_pdf_file(file_path)
    elif suffix in ('.txt', '.csv', '.tsv'):
        return chunk_text_file(file_path)
    else:
        return []
