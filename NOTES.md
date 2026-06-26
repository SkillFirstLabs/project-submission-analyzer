# Architectural & Design Notes

### 1. Safety and Security First (Safe ZIP Extraction)
- **Zip Slip Prevention**: Standard ZIP extraction in Python (`ZipFile.extractall`) can be vulnerable to directory traversal attacks where relative path parts (`../`) escape the destination directory. ProjectIQ prevents this by resolving each file's absolute path and verifying it starts with the target extraction directory.
- **Zip Bomb Mitigation**: Malicious ZIP files (such as 42.zip) contain highly compressed data which can exceed disk space or exhaust server memory. We verify:
  1. Absolute decompressed size limit (Default: 100 MB).
  2. Ratio of uncompressed to compressed size (Default: 100x max).

### 2. Multi-Stage Token Optimization
Rather than calling the LLM for every single outcome statement or skill, we batch the operations:
1. **Programmatic Pre-Filtering**: The `SkillDetector` checks imports, code signatures, filenames, and config dependencies locally before sending anything to the LLM. Only detected skills are forwarded.
2. **Batch Requesting**:
   - Question generation compiles all skills into a single structured prompt.
   - Stated outcome evaluation analyzes all outcomes in a single Groq LPU completion.
3. This reduces API round-trips from `O(N)` to `O(1)`, minimizing processing latency (`processing_time_ms`) and token consumption.

### 3. Structured Outputs with Groq
- Groq is forced to return JSON by specifying `response_format={"type": "json_object"}` in the chat completions payload.
- System prompts are augmented with structured JSON specifications.
- Returned JSON is explicitly validated and parsed back into Pydantic v2 schemas in Python, providing strict type-safety and fallback configurations (default templates) if validation fails.

### 4. Codebase-Specific Questioning
We select a relevant subset of key logic files (entrypoints like `main.py` or framework files like `Dockerfile`, `package.json`, etc.) using a heuristic scoring algorithm. We extract the first 120 lines of these files to supply the LLM with enough local context to reference actual variables, imports, or file structures in its codebase questions.
