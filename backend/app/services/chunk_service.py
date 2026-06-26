from typing import List, Dict

MAX_CHUNK_SIZE = 4000

def chunk_files(files: List[Dict]) -> List[Dict]:
    """
    Splits files into semantic chunks by class, function, or size boundaries.
    Each chunk: {"text": str, "relative_path": str, "filename": str, "chunk_index": int}
    """
    chunks = []
    for f in files:
        content = f["content"]
        relative_path = f["relative_path"]
        filename = f["filename"]
        
        lines = content.split('\n')
        current_chunk_lines = []
        current_size = 0
        chunk_index = 0
        
        for line in lines:
            line_size = len(line) + 1
            is_boundary = line.strip().startswith("class ") or line.strip().startswith("def ") or line.strip().startswith("function ")
            
            if (current_size + line_size > MAX_CHUNK_SIZE and current_chunk_lines) or (is_boundary and current_size > 2000):
                chunk_text = "\n".join(current_chunk_lines)
                chunks.append({
                    "text": f"File: {relative_path}\n\n{chunk_text}",
                    "relative_path": relative_path,
                    "filename": filename,
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                
                current_chunk_lines = current_chunk_lines[-2:]
                current_size = sum(len(l) + 1 for l in current_chunk_lines)
                
            current_chunk_lines.append(line)
            current_size += line_size
            
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines)
            chunks.append({
                "text": f"File: {relative_path}\n\n{chunk_text}",
                "relative_path": relative_path,
                "filename": filename,
                "chunk_index": chunk_index
            })
            
    return chunks
