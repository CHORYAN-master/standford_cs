import os
import re
import json

BASE_DIR = "/Users/hyunhocho/Desktop/Stanford_CS/week2"

results = {
    "files_scanned": 0,
    "secrets_found": [],
    "summary": {"high": 0, "medium": 0, "low": 0}
}

secret_patterns = [
    {"name": "OpenAI API Key", "pattern": r'sk-[a-zA-Z0-9]{48}', "severity": "high"},
    {"name": "Password", "pattern": r'password\s*=\s*["\']([^"\']{3,})["\']', "severity": "high"},
    {"name": "API Key", "pattern": r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "severity": "high"},
    {"name": "Secret Key", "pattern": r'secret[_-]?key\s*=\s*["\']([^"\']{10,})["\']', "severity": "high"}
]

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
    
    for file in files:
        if file.endswith(('.py', '.js', '.json', '.yaml', '.env')):
            file_path = os.path.join(root, file)
            results["files_scanned"] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern_info in secret_patterns:
                    matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        results["secrets_found"].append({
                            "file": file_path.replace(BASE_DIR, "."),
                            "line": line_num,
                            "type": pattern_info["name"],
                            "severity": pattern_info["severity"]
                        })
                        results["summary"][pattern_info["severity"]] += 1
            except:
                continue

print(json.dumps(results, indent=2))
