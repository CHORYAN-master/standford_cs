# Code Review Guidelines

## 📋 Overview
본 가이드라인은 MCP AI Agent 프로젝트의 코드 품질, 보안, 유지보수성을 보장하기 위한 시니어 아키텍트 수준의 리뷰 기준입니다.

---

## 🎯 Review Severity Levels

### Critical 🔴
- **즉시 수정 필요**: 프로덕션 배포를 차단해야 하는 수준
- 보안 취약점, 데이터 손실 위험, 시스템 장애 가능성
- 예: SQL Injection, Path Traversal, 인증/인가 누락

### Warning ⚠️
- **배포 전 수정 권장**: 기능은 작동하나 문제 발생 가능성
- 성능 저하, 에러 핸들링 부족, 잘못된 아키텍처 패턴
- 예: 적절하지 않은 예외 처리, 리소스 누수, 타입 안정성 부족

### Nit 📝
- **개선 제안**: 코드 품질 향상을 위한 스타일/가독성 개선
- 기능에는 영향 없으나 유지보수성 향상
- 예: 변수명 개선, 주석 추가, 코드 중복 제거

---

## 1. 변수 및 함수 명명 규칙 (Naming Conventions)

### 1.1 Python Naming Standards (PEP 8 기반)

#### Functions & Variables
```python
# ✅ Good
def calculate_user_score(user_id: int) -> float:
    total_score = 0
    average_rating = 4.5
    return total_score

# ❌ Bad
def CalcScore(uid):  # CamelCase는 클래스용
    TotalScore = 0   # 변수는 snake_case
    avgRtg = 4.5     # 약어 지양
```

#### Constants
```python
# ✅ Good
MAX_FILE_SIZE = 10 * 1024 * 1024
API_TIMEOUT_SECONDS = 30
DEFAULT_BASE_DIR = "/home/user"

# ❌ Bad
maxFileSize = 10485760  # 매직 넘버, camelCase
ApiTimeout = 30         # PascalCase
```

#### Classes
```python
# ✅ Good
class UserAuthenticationManager:
    pass

class MCPServerConfig:
    pass

# ❌ Bad
class user_manager:  # snake_case
class mcp_config:    # 약어는 대문자 유지
```

---

## 2. 에러 핸들링 (Error Handling)

### 2.1 Exception Hierarchy

```python
# ✅ Good: 구체적 예외를 먼저 처리
def read_user_file(file_path: str) -> str:
    """
    Read user file with comprehensive error handling.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If no read permission
        ValueError: If file path is invalid
        IOError: For other I/O errors
    """
    try:
        validate_path(file_path)
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError as e:
        logger.error(f"Permission denied: {file_path}")
        raise
    except ValueError as e:
        logger.error(f"Invalid path: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        raise IOError(f"Failed to read file: {file_path}") from e

# ❌ Bad: 광범위한 예외를 먼저 처리
def read_file(path):
    try:
        return open(path).read()
    except Exception:
        return None    # 에러 정보 손실
```

### 2.2 Error Context & Logging

```python
# ✅ Good: 풍부한 컨텍스트와 로깅
import logging

logger = logging.getLogger(__name__)

def process_api_request(user_id: int, action: str) -> dict:
    """Process API request with detailed error tracking."""
    try:
        logger.info(f"Processing request - User: {user_id}, Action: {action}")
        result = perform_action(user_id, action)
        logger.info(f"Request successful - User: {user_id}")
        return result
    except ValueError as e:
        logger.warning(
            f"Invalid input - User: {user_id}, Action: {action}, Error: {e}",
            extra={"user_id": user_id, "action": action}
        )
        return {"error": f"Invalid input: {str(e)}", "code": "INVALID_INPUT"}
    except Exception as e:
        logger.error(
            f"Unexpected error - User: {user_id}, Action: {action}",
            exc_info=True,
            extra={"user_id": user_id, "action": action}
        )
        return {"error": "Internal server error", "code": "INTERNAL_ERROR"}

# ❌ Bad: 컨텍스트 부족, 에러 숨김
def process_request(uid, act):
    try:
        return do_stuff(uid, act)
    except:
        return {}
```

---

## 3. 보안 (Security)

### 3.1 Input Validation

```python
# ✅ Good: 다층 방어 (Defense in Depth)
import re
from typing import Optional

def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username with multiple security checks.
    
    Returns:
        (is_valid, error_message)
    """
    # 1. Type check
    if not isinstance(username, str):
        return False, "Username must be a string"
    
    # 2. Length check
    if not (3 <= len(username) <= 50):
        return False, "Username must be between 3-50 characters"
    
    # 3. Character whitelist
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain alphanumeric, underscore, hyphen"
    
    # 4. Reserved words
    RESERVED = ['admin', 'root', 'system']
    if username.lower() in RESERVED:
        return False, "Username is reserved"
    
    return True, None

# ❌ Bad: 검증 부족
def check_username(name):
    if len(name) > 0:
        return True
```

### 3.2 Path Traversal Prevention

```python
# ✅ Good: 엄격한 경로 검증
import os
from pathlib import Path

def validate_safe_path(user_path: str, base_dir: str) -> str:
    """
    Prevent path traversal attacks (../../../etc/passwd).
    
    Raises:
        ValueError: If path escapes base directory
    """
    # Normalize paths
    base = Path(base_dir).resolve()
    target = (base / user_path).resolve()
    
    # Check if target is within base
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Access denied: Path must be within {base}")
    
    # Additional security checks
    if target.is_symlink():
        raise ValueError("Symbolic links not allowed")
    
    return str(target)

# ❌ Bad: Path traversal 취약
def get_file(filename):
    return open(f"/data/{filename}").read()
```

### 3.3 Secrets Management

```python
# ✅ Good: 환경변수 + 검증
import os

def get_api_key(key_name: str) -> str:
    """
    Safely retrieve API key from environment.
    
    Raises:
        ValueError: If key is missing or invalid
    """
    api_key = os.getenv(key_name)
    
    if not api_key:
        raise ValueError(f"Missing required environment variable: {key_name}")
    
    if len(api_key) < 20:
        raise ValueError(f"Invalid API key format for: {key_name}")
    
    return api_key

# ❌ Bad: 하드코딩
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
```

---

## 4. 타입 안정성 (Type Safety)

### 4.1 Type Hints

```python
# ✅ Good: 완전한 타입 힌트
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class UserProfile:
    """User profile data structure."""
    user_id: int
    username: str
    email: str
    created_at: str
    is_active: bool = True

def get_user_by_id(
    user_id: int,
    include_inactive: bool = False
) -> Optional[UserProfile]:
    """
    Retrieve user profile by ID.
    
    Args:
        user_id: Unique user identifier
        include_inactive: Whether to include inactive users
    
    Returns:
        UserProfile if found, None otherwise
    
    Raises:
        ValueError: If user_id is invalid
    """
    if user_id <= 0:
        raise ValueError("user_id must be positive")
    
    return None

# ❌ Bad: 타입 힌트 없음
def get_user(id, active=False):
    return None
```

---

## 5. 성능 및 리소스 관리 (Performance)

### 5.1 Resource Limits

```python
# ✅ Good: 명확한 리소스 제한
import os
from typing import BinaryIO

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_MEMORY_BUFFER = 5 * 1024 * 1024  # 5MB
REQUEST_TIMEOUT = 30  # seconds

def read_large_file(file_path: str) -> str:
    """
    Read file with size limits and chunked processing.
    
    Raises:
        ValueError: If file exceeds size limit
    """
    file_size = os.path.getsize(file_path)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
        )
    
    # Read in chunks
    chunks = []
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(MAX_MEMORY_BUFFER)
            if not chunk:
                break
            chunks.append(chunk)
    
    return ''.join(chunks)

# ❌ Bad: 리소스 제한 없음
def read_file(path):
    return open(path).read()
```

---

## 6. 문서화 (Documentation)

### 6.1 Docstring Standards (Google Style)

```python
# ✅ Good: 완전한 docstring
def calculate_discount(
    original_price: float,
    discount_rate: float,
    min_price: float = 0.0
) -> float:
    """
    Calculate discounted price with validation.
    
    Args:
        original_price: Original price before discount (must be non-negative)
        discount_rate: Discount rate as decimal (0.0 to 1.0)
        min_price: Minimum allowed price (default: 0.0)
    
    Returns:
        Final price after applying discount, guaranteed >= min_price
    
    Raises:
        ValueError: If original_price < 0 or discount_rate not in [0, 1]
    
    Examples:
        >>> calculate_discount(100.0, 0.2)
        80.0
        
        >>> calculate_discount(100.0, 0.5, min_price=60.0)
        60.0
    """
    if original_price < 0:
        raise ValueError("original_price must be non-negative")
    
    if not (0 <= discount_rate <= 1):
        raise ValueError("discount_rate must be between 0 and 1")
    
    discounted = original_price * (1 - discount_rate)
    return max(discounted, min_price)

# ❌ Bad: 문서화 없음
def calc(price, rate):
    return max(price * (1 - rate), 0)
```

---

## 7. 로깅 (Logging)

### 7.1 Structured Logging

```python
# ✅ Good: 구조화된 로깅
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_api_request(
    method: str,
    path: str,
    user_id: Optional[int],
    response_time_ms: float,
    status_code: int
):
    """Log API request with structured data."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "api_request",
        "method": method,
        "path": path,
        "user_id": user_id,
        "response_time_ms": response_time_ms,
        "status_code": status_code,
        "success": 200 <= status_code < 300
    }
    
    if 200 <= status_code < 300:
        logger.info(json.dumps(log_data))
    elif 400 <= status_code < 500:
        logger.warning(json.dumps(log_data))
    else:
        logger.error(json.dumps(log_data))

# ❌ Bad: 비구조화된 로깅
def log_request(method, path, time):
    logger.info(f"Request: {method} {path} took {time}ms")
```

---

## 8. 체크리스트

### 8.1 Security Checklist
- [ ] 모든 사용자 입력 검증
- [ ] SQL Injection 방지
- [ ] Path Traversal 방지
- [ ] XSS 방지
- [ ] 민감 정보 로깅 금지
- [ ] 환경 변수로 secrets 관리
- [ ] Rate limiting 구현
- [ ] 적절한 인증/인가
- [ ] HTTPS 사용

### 8.2 Performance Checklist
- [ ] 적절한 캐싱 전략
- [ ] 리소스 제한 설정
- [ ] Connection pooling
- [ ] 메모리 누수 체크

### 8.3 Code Quality Checklist
- [ ] Type hints 사용
- [ ] Docstring 작성
- [ ] 단위 테스트 작성
- [ ] 에러 핸들링 구현
- [ ] 로깅 추가
- [ ] 코드 중복 제거 (DRY)
- [ ] 매직 넘버 제거
- [ ] 명확한 변수명 사용
- [ ] 함수 길이 적절 (<50 lines)

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-22  
**Maintainer**: Senior Architect Team
