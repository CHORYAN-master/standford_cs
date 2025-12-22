#!/usr/bin/env python3
"""
Health Check Script for MCP AI Agent
Validates system health and reports status
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def check_environment():
    """환경 변수 확인"""
    required_vars = ['BASE_DIR', 'PROJECT_DIR']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    return {
        "status": "healthy" if not missing else "unhealthy",
        "missing_vars": missing
    }

def check_files():
    """필수 파일 존재 확인"""
    required_files = [
        'config.py',
        'security.py',
        'utils.py',
        'server.py',
        'app.py'
    ]
    
    missing = [f for f in required_files if not Path(f).exists()]
    
    return {
        "status": "healthy" if not missing else "unhealthy",
        "missing_files": missing
    }

def check_imports():
    """필수 모듈 임포트 확인"""
    try:
        import streamlit
        import mcp
        from dotenv import load_dotenv
        
        return {
            "status": "healthy",
            "modules": ["streamlit", "mcp", "dotenv"]
        }
    except ImportError as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def check_disk_space():
    """디스크 공간 확인"""
    import shutil
    
    total, used, free = shutil.disk_usage("/")
    free_percent = (free / total) * 100
    
    return {
        "status": "healthy" if free_percent > 10 else "warning",
        "free_space_gb": round(free / (1024**3), 2),
        "free_percent": round(free_percent, 2)
    }

def check_log_file():
    """로그 파일 쓰기 가능 여부 확인"""
    log_file = Path("logs/mcp_server.log")
    
    try:
        log_file.parent.mkdir(exist_ok=True)
        log_file.touch()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def main():
    """전체 헬스 체크 실행"""
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "checks": {
            "environment": check_environment(),
            "files": check_files(),
            "imports": check_imports(),
            "disk_space": check_disk_space(),
            "log_file": check_log_file()
        }
    }
    
    # 전체 상태 판단
    unhealthy_checks = [
        name for name, result in health["checks"].items()
        if result.get("status") != "healthy"
    ]
    
    if unhealthy_checks:
        health["overall_status"] = "unhealthy"
        health["failed_checks"] = unhealthy_checks
    
    # JSON 출력
    print(json.dumps(health, indent=2))
    
    # Exit code
    return 0 if health["overall_status"] == "healthy" else 1

if __name__ == "__main__":
    sys.exit(main())
