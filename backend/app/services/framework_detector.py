from typing import List, Dict, Any

FRAMEWORKS = {
    "FastAPI": {
        "identifiers": ["fastapi"],
        "imports": ["fastapi", "APIRouter"],
    },
    "Flask": {
        "identifiers": ["flask", "flask-cors"],
        "imports": ["flask", "Flask", "Blueprint"],
    },
    "Django": {
        "identifiers": ["django"],
        "imports": ["django", "django.db", "django.urls"],
    },
    "React": {
        "identifiers": ["react", "react-dom"],
        "imports": ["react", "useState", "useEffect"],
    },
    "Express": {
        "identifiers": ["express"],
        "imports": ["express", "require('express')"],
    },
    "Next.js": {
        "identifiers": ["next"],
        "imports": ["next/router", "next/link", "next/image"],
    },
    "NestJS": {
        "identifiers": ["@nestjs/core", "@nestjs/common"],
        "imports": ["@nestjs/common", "@nestjs/core"],
    },
    "Spring Boot": {
        "identifiers": ["spring-boot-starter"],
        "imports": ["org.springframework.boot", "SpringBootApplication"],
    }
}

def detect_frameworks(files: List[Dict[str, Any]], parsed_structures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    detections = []
    
    package_json = ""
    requirements_txt = ""
    pom_xml = ""
    
    all_imports = []
    for structure in parsed_structures:
        all_imports.extend(structure.get("imports", []))
        
    for f in files:
        name = f.get("filename", "").lower()
        if name == "package.json":
            package_json = f.get("content", "").lower()
        elif name == "requirements.txt":
            requirements_txt = f.get("content", "").lower()
        elif name == "pom.xml":
            pom_xml = f.get("content", "").lower()
            
    for fw, rule in FRAMEWORKS.items():
        confidence = 0.0
        evidence = []
        
        for identifier in rule["identifiers"]:
            if identifier in package_json:
                confidence = max(confidence, 0.9)
                evidence.append(f"Found '{identifier}' in package.json")
            if identifier in requirements_txt:
                confidence = max(confidence, 0.9)
                evidence.append(f"Found '{identifier}' in requirements.txt")
            if identifier in pom_xml:
                confidence = max(confidence, 0.9)
                evidence.append(f"Found '{identifier}' in pom.xml")
                
        imports_found = 0
        for imp in all_imports:
            for rule_imp in rule["imports"]:
                if rule_imp.lower() in imp.lower():
                    imports_found += 1
                    evidence.append(f"Found import '{rule_imp}' in code")
                    
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
