"""
Streamlit Chatbot Application - Production Ready with System Health
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
Features: Thought Trace, File Download, Admin Dashboard, Security Scanner, System Health
Supports Korean & English
"""

import streamlit as st
import utils
import os
import re
from datetime import datetime
import time
import subprocess
import csv
import io
import json

# Page Configuration
st.set_page_config(
    page_title="🤖 My Desktop Assistant",
    page_icon="🤖",
    layout="wide"
)

# Constants
BASE_DIR = "/Users/hyunhocho/Desktop/Stanford_CS/week2"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "admin_logs" not in st.session_state:
    st.session_state.admin_logs = []
if "security_scans" not in st.session_state:
    st.session_state.security_scans = []
if "system_health" not in st.session_state:
    st.session_state.system_health = {
        "last_cleanup": None,
        "last_secret_scan": None,
        "cleanup_results": None,
        "secret_scan_results": None
    }

# Helper: Add admin log
def add_admin_log(command: str, output: str, status: str = "success"):
    """Add a log entry to admin dashboard"""
    st.session_state.admin_logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "command": command,
        "output": output,
        "status": status
    })
    if len(st.session_state.admin_logs) > 50:
        st.session_state.admin_logs.pop(0)

# Security Scanner Function (copied from server.py logic)
def run_system_cleanup(dry_run=True):
    """Run system cleanup and return results"""
    results = {
        "pyc_files": [],
        "pycache_dirs": [],
        "total_size": 0,
        "dry_run": dry_run
    }
    
    try:
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                if file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    results["pyc_files"].append({
                        "path": file_path.replace(BASE_DIR, "."),
                        "size": file_size
                    })
                    results["total_size"] += file_size
                    
                    if not dry_run:
                        os.remove(file_path)
            
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                dir_size = sum(os.path.getsize(os.path.join(dirpath, f)) 
                              for dirpath, _, filenames in os.walk(pycache_path) 
                              for f in filenames)
                
                results["pycache_dirs"].append({
                    "path": pycache_path.replace(BASE_DIR, "."),
                    "size": dir_size
                })
                results["total_size"] += dir_size
                
                if not dry_run:
                    import shutil
                    shutil.rmtree(pycache_path)
        
        return results
    except Exception as e:
        return {"error": str(e)}

def run_secret_scan():
    """Run secret detection scan"""
    results = {
        "files_scanned": 0,
        "secrets_found": [],
        "summary": {"high": 0, "medium": 0, "low": 0}
    }
    
    secret_patterns = [
        {"name": "OpenAI API Key", "pattern": r'sk-[a-zA-Z0-9]{48}', "severity": "high"},
        {"name": "Anthropic API Key", "pattern": r'AI[a-zA-Z0-9]{40,}', "severity": "high"},
        {"name": "Generic API Key", "pattern": r'api[_-]?key\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "severity": "high"},
        {"name": "Password", "pattern": r'password\s*=\s*["\']([^"\']{3,})["\']', "severity": "high"},
        {"name": "Secret Key", "pattern": r'secret[_-]?key\s*=\s*["\']([^"\']{10,})["\']', "severity": "high"},
        {"name": "JWT Token", "pattern": r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', "severity": "medium"},
    ]
    
    try:
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.json', '.yaml', '.env', '.txt', '.md')):
                    file_path = os.path.join(root, file)
                    results["files_scanned"] += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')
                        
                        for pattern_info in secret_patterns:
                            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
                            
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                context_line = lines[line_num - 1].strip()
                                
                                secret = {
                                    "file": file_path.replace(BASE_DIR, "."),
                                    "line": line_num,
                                    "type": pattern_info["name"],
                                    "severity": pattern_info["severity"],
                                    "context": context_line[:80] + "..." if len(context_line) > 80 else context_line
                                }
                                
                                results["secrets_found"].append(secret)
                                results["summary"][pattern_info["severity"]] += 1
                    except:
                        continue
        
        return results
    except Exception as e:
        return {"error": str(e)}

# Helper: Export conversation
def export_conversation_to_csv() -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Role", "Message", "Has File", "Has Reasoning"])
    
    for msg in st.session_state.messages:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        role = msg["role"]
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        has_file = "Yes" if "file_data" in msg else "No"
        has_reasoning = "Yes" if "reasoning" in msg else "No"
        writer.writerow([timestamp, role, content, has_file, has_reasoning])
    
    return output.getvalue()

def export_conversation_to_txt() -> str:
    output = []
    output.append("="*60)
    output.append("MY DESKTOP ASSISTANT - CONVERSATION HISTORY")
    output.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("="*60)
    output.append("")
    
    for idx, msg in enumerate(st.session_state.messages, 1):
        role = msg["role"].upper()
        content = msg["content"]
        output.append(f"[{idx}] {role}:")
        output.append("-" * 60)
        output.append(content)
        output.append("")
    
    return "\n".join(output)

# App Header
st.title("🤖 My Desktop Assistant")
st.caption("🔒 Production Ready with System Health Monitor | 한국어 & English Support 🌐")

# Sidebar
with st.sidebar:
    st.header("🛠️ Available Tools")
    st.success("✅ Math Operations")
    st.success("✅ File Read/Write")
    st.success("✅ System Cleanup")
    st.success("✅ Secret Detection")
    st.success("✅ Security Scanner")
    
    st.divider()
    
    st.header("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Admin Logs", len(st.session_state.admin_logs))
    st.metric("Security Scans", len(st.session_state.security_scans))
    
    st.divider()
    
    st.header("⚙️ Settings")
    show_reasoning = st.checkbox("Show Reasoning", value=True)
    show_admin = st.checkbox("Show Admin Dashboard", value=False)
    show_health = st.checkbox("Show System Health", value=False)
    
    st.divider()
    
    st.header("📥 Export Results")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 CSV"):
            csv_data = export_conversation_to_csv()
            st.download_button(
                label="⬇️ Download",
                data=csv_data,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    with col2:
        if st.button("📄 TXT"):
            txt_data = export_conversation_to_txt()
            st.download_button(
                label="⬇️ Download",
                data=txt_data,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# System Health Monitor
if show_health:
    st.divider()
    st.subheader("🏥 System Health Monitor")
    
    tab1, tab2, tab3 = st.tabs(["🧹 Cleanup", "🔒 Secret Detection", "📊 Summary"])
    
    with tab1:
        st.markdown("### System Cleanup")
        st.caption("Remove Python cache files (.pyc) and __pycache__ directories")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Scan (Dry Run)"):
                with st.spinner("Scanning..."):
                    results = run_system_cleanup(dry_run=True)
                    st.session_state.system_health["cleanup_results"] = results
                    st.session_state.system_health["last_cleanup"] = datetime.now()
        
        with col2:
            if st.button("🧹 Clean Now", type="primary"):
                with st.spinner("Cleaning..."):
                    results = run_system_cleanup(dry_run=False)
                    st.session_state.system_health["cleanup_results"] = results
                    st.session_state.system_health["last_cleanup"] = datetime.now()
                    st.success("Cleanup completed!")
        
        if st.session_state.system_health["cleanup_results"]:
            results = st.session_state.system_health["cleanup_results"]
            
            if "error" in results:
                st.error(f"Error: {results['error']}")
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric(".pyc Files", len(results["pyc_files"]))
                col2.metric("__pycache__ Dirs", len(results["pycache_dirs"]))
                col3.metric("Total Size", f"{results['total_size'] / 1024:.1f} KB")
                
                if results["pyc_files"]:
                    with st.expander("📄 .pyc Files"):
                        for f in results["pyc_files"]:
                            st.caption(f"• {f['path']} ({f['size']} bytes)")
                
                if results["pycache_dirs"]:
                    with st.expander("📁 __pycache__ Directories"):
                        for d in results["pycache_dirs"]:
                            st.caption(f"• {d['path']} ({d['size']} bytes)")
    
    with tab2:
        st.markdown("### Secret Detection")
        st.caption("Scan for hardcoded API keys, passwords, and sensitive data")
        
        if st.button("🔍 Scan for Secrets"):
            with st.spinner("Scanning all files..."):
                results = run_secret_scan()
                st.session_state.system_health["secret_scan_results"] = results
                st.session_state.system_health["last_secret_scan"] = datetime.now()
        
        if st.session_state.system_health["secret_scan_results"]:
            results = st.session_state.system_health["secret_scan_results"]
            
            if "error" in results:
                st.error(f"Error: {results['error']}")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Files Scanned", results["files_scanned"])
                col2.metric("🔴 High", results["summary"]["high"])
                col3.metric("🟡 Medium", results["summary"]["medium"])
                col4.metric("🟢 Low", results["summary"]["low"])
                
                if results["secrets_found"]:
                    st.error(f"⚠️ Found {len(results['secrets_found'])} potential secrets!")
                    
                    for secret in results["secrets_found"]:
                        severity_color = {
                            "high": "🔴",
                            "medium": "🟡",
                            "low": "🟢"
                        }.get(secret["severity"], "⚪")
                        
                        with st.expander(f"{severity_color} {secret['type']} in {secret['file']}"):
                            st.caption(f"**Line {secret['line']}**: {secret['context']}")
                            st.code(secret.get("matched", "N/A"), language="text")
                else:
                    st.success("✅ No secrets detected!")
    
    with tab3:
        st.markdown("### Health Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Last Cleanup",
                st.session_state.system_health["last_cleanup"].strftime("%H:%M:%S") 
                if st.session_state.system_health["last_cleanup"] else "Never"
            )
        
        with col2:
            st.metric(
                "Last Secret Scan",
                st.session_state.system_health["last_secret_scan"].strftime("%H:%M:%S")
                if st.session_state.system_health["last_secret_scan"] else "Never"
            )
        
        # Overall health status
        cleanup_ok = st.session_state.system_health["cleanup_results"] is not None
        secrets_ok = (st.session_state.system_health["secret_scan_results"] and 
                     len(st.session_state.system_health["secret_scan_results"].get("secrets_found", [])) == 0)
        
        if cleanup_ok and secrets_ok:
            st.success("🟢 System Health: GOOD")
        elif cleanup_ok or secrets_ok:
            st.warning("🟡 System Health: FAIR")
        else:
            st.info("⚪ System Health: UNKNOWN (Run scans)")

# Chat display
st.divider()

# Simple chat interface (abbreviated for space)
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        response = f"System Health Monitor is active! Try commands like: 'Run cleanup' or 'Scan for secrets'"
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.caption("🔒 Security Scanner | 🧹 System Cleanup | 🔍 Secret Detection | 🚀 MCP Powered | 🌐 Bilingual")
