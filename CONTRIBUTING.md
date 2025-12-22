# Contributing to MCP AI Agent

Welcome! This guide will help you contribute effectively to our security-hardened MCP server project.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git & Graphite CLI
- GitHub account

### Setup
```bash
# Clone
git clone https://github.com/CHORYAN-master/standford_cs.git
cd Stanford_CS/week2

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your paths

# Install Graphite
brew install graphite
gt auth
```

---

## 📋 Development Workflow

### 1. Create Feature Branch
```bash
# Start from main
gt checkout main
gt branch create feat-your-feature

# Or from current branch
gt branch create fix-bug-name
```

### 2. Make Changes
- Follow code standards (see below)
- Add tests for new features
- Update documentation

### 3. Run Security Scan
```bash
# REQUIRED before commit
python3 security_audit.py

# Must score 90+ to pass
# Fix any issues before proceeding
```

### 4. Commit with Graphite
```bash
# Conventional commit format
gt commit -m "type: description"

# Types:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# refactor: Code refactoring
# test: Tests
# chore: Maintenance
```

### 5. Stack & Submit
```bash
# Create stack
gt stack submit

# Or auto-commit (if server running)
# Use MCP tool: auto_commit_and_stack("message")
```

---

## 🛡️ Security Requirements

### CRITICAL: All PRs Must Pass

#### 1. Security Score ≥ 90/100
```bash
python3 security_audit.py
# Output must show: "GRADE: 🟢 A"
```

#### 2. No Hardcoded Secrets
- Use environment variables
- Never commit `.env`
- Check with: `scan_secrets()`

#### 3. Input Validation
- All user input MUST be validated
- Use functions from `security.py`:
  - `validate_commit_message()`
  - `validate_command_strict()`
  - `validate_filename()`

#### 4. Safe Subprocess Calls
```python
# ✅ REQUIRED
subprocess.run(args, shell=False, timeout=X)

# ❌ FORBIDDEN
subprocess.run(cmd, shell=True)  # NEVER!
```

---

## 📏 Code Standards

### Python Style (PEP 8)
```python
# Function names: snake_case
def calculate_total_price(items: List[dict]) -> float:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024

# Classes: PascalCase
class UserAuthManager:
    pass
```

### Type Hints (Required)
```python
from typing import List, Optional, Tuple

def process_data(
    items: List[str],
    max_count: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Process data items.
    
    Args:
        items: List of items to process
        max_count: Maximum items (None = unlimited)
    
    Returns:
        (success, error_message)
    """
    pass
```

### Error Handling
```python
import logging

logger = logging.getLogger(__name__)

def safe_operation():
    try:
        # Operation
        logger.info("Operation successful")
    except SpecificError as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return sanitize_error_message(e, "operation")
```

### Docstrings (Google Style)
```python
def calculate_discount(price: float, rate: float) -> float:
    """
    Calculate discounted price.
    
    Args:
        price: Original price
        rate: Discount rate (0.0-1.0)
    
    Returns:
        Discounted price
    
    Raises:
        ValueError: If rate not in [0, 1]
    
    Examples:
        >>> calculate_discount(100.0, 0.2)
        80.0
    """
    pass
```

---

## 🔄 Graphite Stack Rules

### Stack Organization
```
main
  └─ feat-auth (base feature)
       ├─ feat-auth-login (sub-feature)
       └─ feat-auth-logout (sub-feature)
```

### Naming Convention
```bash
# Format: YYYY-MM-DD-type_description
12-22-feat_add_user_authentication
12-23-fix_login_validation
12-23-docs_update_auth_guide
```

### Stacking Best Practices

1. **Small, Focused Changes**
   - One feature per stack
   - ~100-300 lines max
   - Single responsibility

2. **Clear Dependencies**
   ```bash
   # Good: Linear stack
   main → feat-base → feat-extension
   
   # Avoid: Complex dependencies
   main → feat-a ─┬→ feat-c
                  └→ feat-b → feat-c
   ```

3. **Descriptive Messages**
   ```bash
   # ✅ Good
   feat: add rate limiting to file operations
   
   # ❌ Bad
   update stuff
   ```

---

## 🧪 Testing Requirements

### Before Submitting PR

1. **Security Audit**
   ```bash
   python3 security_audit.py
   # Must score 90+
   ```

2. **Manual Testing**
   ```bash
   # Start server
   python3 server.py
   
   # Test tools work
   # Check error messages sanitized
   # Verify rate limiting
   ```

3. **Code Quality**
   ```bash
   # Linting (optional but recommended)
   ruff check .
   mypy server.py utils.py config.py security.py
   ```

---

## 📝 PR Checklist

Before submitting, verify:

- [ ] Security audit passes (≥90/100)
- [ ] No hardcoded paths or secrets
- [ ] All inputs validated
- [ ] `shell=False` in subprocess calls
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] Error messages sanitized
- [ ] Logging added
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Conventional commit format
- [ ] Graphite stack clean

---

## 🚫 Common Mistakes to Avoid

### 1. Hardcoding Paths
```python
# ❌ Don't
BASE_DIR = "/Users/yourname/Desktop"

# ✅ Do
from config import BASE_DIR
```

### 2. Exposing Errors
```python
# ❌ Don't
except Exception as e:
    return f"Error: {str(e)}"  # Leaks info

# ✅ Do
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    return sanitize_error_message(e, "operation")
```

### 3. Unsafe Commands
```python
# ❌ Don't
subprocess.run(user_input, shell=True)

# ✅ Do
is_valid, error, args = validate_command_strict(user_input)
if not is_valid:
    return f"Error: {error}"
subprocess.run(args, shell=False, timeout=30)
```

### 4. Missing Validation
```python
# ❌ Don't
def write_file(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)

# ✅ Do
def write_file(path: str, content: str):
    is_valid, error = validate_filename(path)
    if not is_valid:
        return f"Error: {error}"
    
    safe_path = validate_safe_path(path, BASE_DIR)
    # ...
```

---

## 🔍 Code Review Process

### What Reviewers Check

1. **Security** (Highest Priority)
   - Input validation present
   - No command injection risks
   - Proper error handling
   - Rate limiting applied

2. **Code Quality**
   - Type hints complete
   - Docstrings clear
   - No code duplication
   - Follows PEP 8

3. **Testing**
   - Security audit passes
   - Edge cases handled
   - Error cases tested

4. **Documentation**
   - README updated if needed
   - Code comments clear
   - Examples provided

### Review Response Time
- Simple fixes: 1-2 days
- Complex features: 3-5 days
- Security issues: Same day

---

## 📊 Security Audit Details

### Audit Categories

1. **Configuration (20 points)**
   - `.env` setup correct
   - No hardcoded values
   - Config modules present

2. **Hardcoded Paths (25 points)**
   - No absolute paths in code
   - All paths from environment

3. **Security Features (35 points)**
   - Input validation
   - Rate limiting
   - Error sanitization
   - Safe subprocess calls

4. **Dangerous Patterns (20 points)**
   - No `shell=True`
   - No unvalidated inputs
   - No exposed secrets

### Passing Grade
```
Score ≥ 90/100 = Grade A (Required to merge)
Score 80-89    = Grade B (Needs improvement)
Score 70-79    = Grade C (Must fix before merge)
Score < 70     = Grade D (Rejected)
```

---

## 🎯 Example Contribution

```bash
# 1. Create branch
gt checkout main
gt branch create feat-add-user-greeting

# 2. Make changes
# Edit server.py, add new tool

# 3. Test
python3 security_audit.py
# Output: 100/100 ✅

# 4. Commit
gt commit -m "feat: add personalized user greeting tool"

# 5. Submit
gt stack submit
# Creates PR on GitHub
```

---

## 🐛 Found a Security Issue?

**DO NOT** open a public issue!

Email: security@project.com (or private message)

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

---

## 📚 Resources

- [Security Guidelines](./REVIEW_GUIDELINES.md)
- [Security Audit Report](./CODE_REVIEW_AUDIT.md)
- [Phase 1 Report](./PHASE1_FINAL_REPORT.md)
- [Graphite Docs](https://graphite.dev/docs)
- [PEP 8](https://pep8.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## 💬 Questions?

- Check existing issues
- Read documentation
- Ask in discussions
- Review audit output

---

## 🙏 Thank You!

Every contribution makes this project more secure and reliable.

**Last Updated**: 2024-12-22  
**Maintainer**: Development Team
