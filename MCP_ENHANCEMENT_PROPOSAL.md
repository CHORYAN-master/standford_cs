# Enhanced MCP Tools Proposal
**Date:** 2025-12-22  
**Purpose:** Expand Claude's autonomous capabilities

---

## New Tools to Add

### 1. Git Operations (High Value!)

```python
@mcp.tool()
def git_commit(message: str, files: list = None) -> str:
    """
    Commit changes with a message
    Args:
        message: Commit message
        files: List of files to add (if None, adds all)
    """
    try:
        if files:
            for f in files:
                subprocess.run(['git', '-C', BASE_DIR, 'add', f])
        else:
            subprocess.run(['git', '-C', BASE_DIR, 'add', '.'])
        
        result = subprocess.run(
            ['git', '-C', BASE_DIR, 'commit', '-m', message],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def git_status() -> str:
    """Get git status"""
    result = subprocess.run(
        ['git', '-C', BASE_DIR, 'status'],
        capture_output=True, text=True
    )
    return result.stdout

@mcp.tool()
def graphite_create(message: str) -> str:
    """Create a new Graphite stack"""
    result = subprocess.run(
        ['gt', '-C', BASE_DIR, 'create', '-m', message],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else result.stderr
```

### 2. File Management

```python
@mcp.tool()
def create_directory(dir_path: str) -> str:
    """Create a new directory"""
    try:
        safe_path = utils.validate_safe_path(dir_path, BASE_DIR)
        os.makedirs(safe_path, exist_ok=True)
        return f"Created directory: {dir_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def delete_file(file_path: str) -> str:
    """Delete a file (with confirmation)"""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        if os.path.exists(safe_path):
            os.remove(safe_path)
            return f"Deleted: {file_path}"
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """Move or rename a file"""
    try:
        safe_src = utils.validate_safe_path(src, BASE_DIR)
        safe_dst = utils.validate_safe_path(dst, BASE_DIR)
        os.rename(safe_src, safe_dst)
        return f"Moved {src} to {dst}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 3. Process Management

```python
@mcp.tool()
def run_streamlit_app(file_path: str = "app.py") -> str:
    """Start Streamlit app in background"""
    try:
        safe_path = utils.validate_safe_path(file_path, BASE_DIR)
        # Start in background
        subprocess.Popen(
            ['streamlit', 'run', safe_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return f"Started Streamlit app: {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Advanced Git/Graphite Integration

```python
@mcp.tool()
def auto_commit_and_stack(files_changed: list, commit_message: str) -> str:
    """
    Automatically add, commit, and create Graphite stack
    One-step Git workflow automation
    """
    try:
        # Add files
        for f in files_changed:
            subprocess.run(['git', '-C', BASE_DIR, 'add', f], check=True)
        
        # Commit
        subprocess.run(
            ['git', '-C', BASE_DIR, 'commit', '-m', commit_message],
            check=True, capture_output=True, text=True
        )
        
        # Create Graphite stack
        result = subprocess.run(
            ['gt', '-C', BASE_DIR, 'create', '-m', commit_message],
            capture_output=True, text=True
        )
        
        return f"✅ Committed and stacked: {commit_message}\n{result.stdout}"
    except Exception as e:
        return f"Error: {str(e)}"
```

---

## Implementation Priority

### 🔴 High Priority (Implement Now)
1. `git_commit()` - 자동 커밋
2. `git_status()` - 상태 확인
3. `graphite_create()` - 스택 생성
4. `auto_commit_and_stack()` - 원스텝 워크플로우

### 🟡 Medium Priority
5. `create_directory()` - 폴더 생성
6. `delete_file()` - 파일 삭제
7. `move_file()` - 파일 이동

### 🟢 Low Priority
8. `run_streamlit_app()` - 앱 실행

---

## Benefits

**Before:**
```
1. Claude: "파일 수정 완료!"
2. You: "완료!" 
3. You: (터미널에서 git add, gt create 수동 실행)
```

**After:**
```
1. Claude: "파일 수정하고 자동 커밋했어요!" ✅
   - Files modified
   - Git committed
   - Graphite stack created
```

**Time Saved:** ~30 seconds per commit × 10 commits/day = **5 minutes/day**

---

## Security Considerations

- ✅ All paths validated through `validate_safe_path()`
- ✅ BASE_DIR restriction maintained
- ✅ No dangerous git commands (force push, etc.)
- ✅ Confirmations for destructive operations
