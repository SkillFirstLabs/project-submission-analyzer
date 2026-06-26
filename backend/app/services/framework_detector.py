import re
from typing import List, Dict, Any

FRAMEWORKS = {
    "FastAPI": {
        "identifiers": [r'\bfastapi\b'],
        "import_patterns": [r'\bimport\s+fastapi\b', r'\bfrom\s+fastapi\b'],
    },
    "Flask": {
        "identifiers": [r'\bflask\b'],
        "import_patterns": [r'\bimport\s+flask\b', r'\bfrom\s+flask\b'],
    },
    "Django": {
        "identifiers": [r'\bdjango\b'],
        "import_patterns": [r'\bimport\s+django\b', r'\bfrom\s+django\b'],
    },
    "React": {
        "identifiers": [r'"react"\s*:', r'"react-dom"\s*:'],
        "import_patterns": [
            r'\bimport\s+React\b',
            r'\bfrom\s+[\'"]react(-dom)?[\'"]',
            r'\brequire\([\'"]react(-dom)?[\'"]\)'
        ],
    },
    "Express.js": {
        "identifiers": [r'"express"\s*:'],
        "import_patterns": [
            r'\bimport\s+express\b',
            r'\bfrom\s+[\'"]express[\'"]',
            r'\brequire\([\'"]express[\'"]\)'
        ],
    },
    "Next.js": {
        "identifiers": [r'"next"\s*:'],
        "import_patterns": [r'\bfrom\s+[\'"]next/'],
    },
    "NestJS": {
        "identifiers": [r'"@nestjs/core"\s*:', r'"@nestjs/common"\s*:'],
        "import_patterns": [r'\bfrom\s+[\'"]@nestjs/'],
    },
    "Spring Boot": {
        "identifiers": [r'\bspring-boot-starter\b'],
        "import_patterns": [r'\bimport\s+org\.springframework\.boot\b'],
    },
    "Flutter": {
        "identifiers": [r'\bflutter\b', r'sdk:\s*flutter'],
        "import_patterns": [r'\bpackage:flutter/'],
    },
    "TensorFlow": {
        "identifiers": [r'\btensorflow\b'],
        "import_patterns": [r'\bimport\s+tensorflow\b', r'\bfrom\s+tensorflow\b'],
    },
    "PyTorch": {
        "identifiers": [r'\btorch\b', r'\bpytorch\b'],
        "import_patterns": [r'\bimport\s+torch\b', r'\bfrom\s+torch\b'],
    },
    "Scikit-Learn": {
        "identifiers": [r'\bscikit-learn\b', r'\bsklearn\b'],
        "import_patterns": [r'\bimport\s+sklearn\b', r'\bfrom\s+sklearn\b'],
    },
    "Pandas": {
        "identifiers": [r'\bpandas\b'],
        "import_patterns": [r'\bimport\s+pandas\b', r'\bfrom\s+pandas\b'],
    },
    "NumPy": {
        "identifiers": [r'\bnumpy\b'],
        "import_patterns": [r'\bimport\s+numpy\b', r'\bfrom\s+numpy\b'],
    }
}

def detect_frameworks(files: List[Dict[str, Any]], parsed_structures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    detections = []
    
    package_json = ""
    requirements_txt = ""
    pubspec_yaml = ""
    pom_xml = ""
    
    all_imports = []
    for structure in parsed_structures:
        all_imports.extend(structure.get("imports", []))
        
    for f in files:
        name = f.get("filename", "").lower()
        if name == "package.json":
            package_json = f.get("content", "")
        elif name == "requirements.txt":
            requirements_txt = f.get("content", "")
        elif name == "pubspec.yaml":
            pubspec_yaml = f.get("content", "")
        elif name == "pom.xml":
            pom_xml = f.get("content", "")
            
    for fw, rule in FRAMEWORKS.items():
        confidence = 0.0
        evidence = []
        
        # Check config/manifest files using regex
        for pattern in rule["identifiers"]:
            # Check package.json
            if package_json and re.search(pattern, package_json, re.IGNORECASE):
                confidence = max(confidence, 0.9)
                evidence.append(f"Found match for '{pattern}' in package.json")
            # Check requirements.txt
            if requirements_txt and re.search(pattern, requirements_txt, re.IGNORECASE):
                confidence = max(confidence, 0.9)
                evidence.append(f"Found match for '{pattern}' in requirements.txt")
            # Check pubspec.yaml
            if pubspec_yaml and re.search(pattern, pubspec_yaml, re.IGNORECASE):
                confidence = max(confidence, 0.9)
                evidence.append(f"Found match for '{pattern}' in pubspec.yaml")
            # Check pom.xml
            if pom_xml and re.search(pattern, pom_xml, re.IGNORECASE):
                confidence = max(confidence, 0.9)
                evidence.append(f"Found match for '{pattern}' in pom.xml")
                

        imports_found = 0
        for imp in all_imports:
            for pattern in rule["import_patterns"]:
                if re.search(pattern, imp):
                    imports_found += 1
                    evidence.append(f"Found matching import pattern '{pattern}' in code")
                    break  
                    
        if imports_found > 0:
            import_conf = min(0.3 + (imports_found * 0.2), 0.95)
            confidence = max(confidence, import_conf)
            
        if confidence > 0.0:
            detections.append({
                "framework": fw,
                "confidence": confidence,
                "evidence": list(set(evidence))
            })
            
    return detections
