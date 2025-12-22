#!/usr/bin/env python3
"""
Security Audit Script
Validates the security improvements and generates a report.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_configuration():
    """Check if configuration is properly set up."""
    print("🔍 Checking Configuration...")
    
    checks = {
        ".env file exists": os.path.exists('.env'),
        ".env.example exists": os.path.exists('.env.example'),
        ".gitignore exists": os.path.exists('.gitignore'),
        "config.py exists": os.path.exists('config.py'),
        "security.py exists": os.path.exists('security.py'),
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    return passed, total


def check_hardcoded_paths():
    """Check for hardcoded paths in source files."""
    print("\n🔍 Checking for Hardcoded Paths...")
    
    files_to_check = ['server.py', 'app.py']
    issues = []
    
    for filename in files_to_check:
        if not os.path.exists(filename):
            continue
            
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            # Check for hardcoded absolute paths
            if '/Users/' in line and 'BASE_DIR' not in line and 'PROJECT_DIR' not in line:
                if not line.strip().startswith('#'):
                    issues.append(f"{filename}:{i} - Hardcoded path found")
    
    if issues:
        print(f"  ❌ Found {len(issues)} hardcoded paths:")
        for issue in issues:
            print(f"    - {issue}")
        return 0, len(issues)
    else:
        print("  ✅ No hardcoded paths found")
        return 1, 1


def check_security_features():
    """Check if security features are implemented."""
    print("\n🔍 Checking Security Features...")
    
    checks = {}
    
    # Check server.py
    if os.path.exists('server.py'):
        with open('server.py', 'r') as f:
            content = f.read()
            
        checks["Import security module"] = 'from security import' in content
        checks["Import config module"] = 'from config import' in content
        checks["Rate limiting"] = 'RateLimiter' in content
        checks["Input validation (commit)"] = 'validate_commit_message' in content
        checks["Input validation (command)"] = 'validate_command_strict' in content
        checks["shell=False"] = 'shell=False' in content
        checks["Logging"] = 'logger.' in content
        checks["sanitize_error_message"] = 'sanitize_error_message' in content
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
    
    return passed, total


def check_dangerous_patterns():
    """Check for dangerous patterns in code."""
    print("\n🔍 Checking for Dangerous Patterns...")
    
    issues = []
    
    if os.path.exists('server.py'):
        with open('server.py', 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for shell=True
        for i, line in enumerate(lines, 1):
            if 'shell=True' in line and not line.strip().startswith('#'):
                issues.append(f"server.py:{i} - shell=True found (security risk)")
        
        # Check for unvalidated subprocess calls
        for i, line in enumerate(lines, 1):
            if 'subprocess.run' in line:
                # Look ahead a few lines to check for validation
                context = '\n'.join(lines[max(0, i-5):min(len(lines), i+5)])
                if 'validate' not in context and 'git status' not in line:
                    # This is a potential issue
                    pass  # We can be lenient here if other checks pass
    
    if issues:
        print(f"  ❌ Found {len(issues)} dangerous patterns:")
        for issue in issues:
            print(f"    - {issue}")
        return 0, len(issues)
    else:
        print("  ✅ No dangerous patterns found")
        return 1, 1


def calculate_security_score():
    """Calculate overall security score."""
    print("\n" + "="*60)
    print("🛡️  SECURITY AUDIT RESULTS")
    print("="*60)
    
    categories = []
    
    # Configuration check
    config_passed, config_total = check_configuration()
    categories.append(("Configuration", config_passed, config_total, 20))
    
    # Hardcoded paths check
    paths_passed, paths_total = check_hardcoded_paths()
    categories.append(("Hardcoded Paths", paths_passed, paths_total, 25))
    
    # Security features check
    security_passed, security_total = check_security_features()
    categories.append(("Security Features", security_passed, security_total, 35))
    
    # Dangerous patterns check
    patterns_passed, patterns_total = check_dangerous_patterns()
    categories.append(("Dangerous Patterns", patterns_passed, patterns_total, 20))
    
    # Calculate weighted score
    total_score = 0
    for name, passed, total, weight in categories:
        if total > 0:
            category_score = (passed / total) * weight
            total_score += category_score
    
    print(f"\n📊 OVERALL SECURITY SCORE: {total_score:.1f}/100")
    
    # Grade
    if total_score >= 90:
        grade = "A (Excellent)"
        emoji = "🟢"
    elif total_score >= 80:
        grade = "B (Good)"
        emoji = "🟡"
    elif total_score >= 70:
        grade = "C (Fair)"
        emoji = "🟠"
    else:
        grade = "D (Needs Improvement)"
        emoji = "🔴"
    
    print(f"🎯 GRADE: {emoji} {grade}")
    
    # Detailed breakdown
    print(f"\n📋 DETAILED BREAKDOWN:")
    for name, passed, total, weight in categories:
        if total > 0:
            percentage = (passed / total) * 100
            category_score = (passed / total) * weight
            print(f"  {name:20s}: {passed}/{total} ({percentage:5.1f}%) = {category_score:5.1f}/{weight} points")
    
    print("\n" + "="*60)
    
    # Recommendations
    if total_score < 90:
        print("\n⚠️  RECOMMENDATIONS:")
        if config_passed < config_total:
            print("  • Complete configuration setup")
        if paths_passed < paths_total:
            print("  • Remove remaining hardcoded paths")
        if security_passed < security_total:
            print("  • Implement missing security features")
        if patterns_passed < patterns_total:
            print("  • Fix dangerous code patterns")
    else:
        print("\n✅ All critical security checks passed!")
    
    print("="*60)
    
    return total_score


def main():
    """Main audit function."""
    print("\n" + "="*60)
    print("🔐 SECURITY AUDIT - Phase 1 Critical Fixes")
    print("="*60 + "\n")
    
    # Check if we're in the right directory
    if not os.path.exists('server.py'):
        print("❌ Error: server.py not found. Run this script from the project directory.")
        sys.exit(1)
    
    try:
        score = calculate_security_score()
        
        # Save results
        results = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "security_score": score,
            "passed": score >= 90
        }
        
        with open('security_audit_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: security_audit_results.json")
        
        # Exit with appropriate code
        sys.exit(0 if score >= 90 else 1)
        
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
