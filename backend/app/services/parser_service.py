import re
from typing import Dict, List, Any

def parse_file(file_content: str, filename: str) -> Dict[str, Any]:
    """
    Parses a file to extract structural components: classes, methods, functions, imports, APIs, and variables.
    Provides a robust regex-based syntax analyzer.
    """
    structure = {
        "classes": [],
        "methods": [],
        "functions": [],
        "imports": [],
        "apis": [],
        "variables": []
    }
    
    lines = file_content.split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        
        # Imports detection
        if line_stripped.startswith("import ") or line_stripped.startswith("from ") or "require(" in line_stripped or line_stripped.startswith("import {"):
            structure["imports"].append(line_stripped)
            
        # Class detection
        class_match = re.search(r'\bclass\s+(\w+)', line_stripped)
        if class_match:
            structure["classes"].append(class_match.group(1))
            
        # Function/Method detection
        func_match = re.search(r'\bdef\s+(\w+)\s*\(', line_stripped) or re.search(r'\bfunction\s+(\w+)\s*\(', line_stripped)
        if func_match:
            structure["functions"].append(func_match.group(1))
            
        # C++/Java/JS class method
        method_match = re.search(r'\b(public|private|protected|static|async)?\s*(\w+)\s*\([^)]*\)\s*\{', line_stripped)
        if method_match and method_match.group(2) not in ['if', 'for', 'while', 'switch', 'catch', 'function']:
            structure["methods"].append(method_match.group(2))
            
        # API route / endpoint detection
        api_match = re.search(r'@(app|router|Blueprint|route)\.(get|post|put|delete|patch|route)\(["\']([^"\']+)["\']', line_stripped) or \
                    re.search(r'\b(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', line_stripped)
        if api_match:
            route = api_match.group(3) if len(api_match.groups()) >= 3 else api_match.group(2)
            structure["apis"].append(route)
            
        # Variables
        var_match = re.search(r'\b(const|let|var)\s+(\w+)\s*=', line_stripped) or re.search(r'^\s*(\w+)\s*=\s*[^=]', line_stripped)
        if var_match:
            var_name = var_match.group(2) if len(var_match.groups()) >= 2 and var_match.group(1) in ['const', 'let', 'var'] else var_match.group(1)
            if var_name not in ['self', 'if', 'for', 'while', 'return']:
                structure["variables"].append(var_name)
                
    # Deduplicate lists
    for key in structure:
        structure[key] = list(set(structure[key]))
        
    return structure
