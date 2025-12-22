"""
Streamlit Chatbot Application - Production Ready with Security Scanner
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
Features: Thought Trace, File Download, Admin Dashboard, Security Scanner
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
if "conversation_data" not in st.session_state:
    st.session_state.conversation_data = []

# Security Scanner Function
def security_scan(content: str, filename: str = "code") -> dict:
    """
    Perform basic security scan on code content
    6주차 예습: 간단한 보안 체크
    """
    issues = []
    warnings = []
    
    # Check 1: Hardcoded API Keys
    api_key_patterns = [
        r'api[_-]?key\s*=\s*["\']([^"\']{10,})["\']',
        r'API[_-]?KEY\s*=\s*["\']([^"\']{10,})["\']',
        r'secret[_-]?key\s*=\s*["\']([^"\']{10,})["\']',
        r'password\s*=\s*["\']([^"\']{3,})["\']',
        r'token\s*=\s*["\']([^"\']{10,})["\']',
    ]
    
    for pattern in api_key_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            issues.append({
                "severity": "HIGH",
                "type": "Hardcoded Secret",
                "description": f"Found hardcoded credential: {match.group(0)[:30]}...",
                "line": content[:match.start()].count('\n') + 1
            })
    
    # Check 2: SQL Injection Risk
    sql_patterns = [
        r'execute\s*\(\s*["\'].*%s.*["\']',
        r'cursor\.execute\s*\(\s*f["\']',
        r'\.format\s*\(.*\)\s*\)',
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, content):
            warnings.append({
                "severity": "MEDIUM",
                "type": "SQL Injection Risk",
                "description": "Potential SQL injection vulnerability detected",
                "line": "Multiple locations"
            })
            break
    
    # Check 3: Command Injection (shell=True)
    if 'shell=True' in content:
        warnings.append({
            "severity": "MEDIUM",
            "type": "Command Injection Risk",
            "description": "Using shell=True can be dangerous with user input",
            "line": content[:content.find('shell=True')].count('\n') + 1
        })
    
    # Check 4: eval() or exec() usage
    dangerous_funcs = ['eval(', 'exec(', '__import__']
    for func in dangerous_funcs:
        if func in content:
            issues.append({
                "severity": "HIGH",
                "type": "Dangerous Function",
                "description": f"Using {func} can execute arbitrary code",
                "line": content[:content.find(func)].count('\n') + 1
            })
    
    # Check 5: Insecure file operations
    if 'open(' in content and 'w' in content:
        if 'validate_safe_path' not in content and 'os.path.join' not in content:
            warnings.append({
                "severity": "LOW",
                "type": "File Operation",
                "description": "File write operation without path validation",
                "line": "Multiple locations"
            })
    
    # Calculate security score
    total_issues = len(issues) + len(warnings)
    if total_issues == 0:
        score = 100
        status = "SAFE"
    elif len([i for i in issues if i['severity'] == 'HIGH']) > 0:
        score = max(30, 100 - (len(issues) * 20 + len(warnings) * 10))
        status = "VULNERABLE"
    elif len(warnings) > 0:
        score = max(60, 100 - (len(warnings) * 10))
        status = "CAUTION"
    else:
        score = 100
        status = "SAFE"
    
    return {
        "filename": filename,
        "score": score,
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# Helper: Save conversation to CSV
def export_conversation_to_csv() -> str:
    """Export conversation history to CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Timestamp", "Role", "Message", "Has File", "Has Reasoning"])
    
    # Data
    for msg in st.session_state.messages:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        role = msg["role"]
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        has_file = "Yes" if "file_data" in msg else "No"
        has_reasoning = "Yes" if "reasoning" in msg else "No"
        
        writer.writerow([timestamp, role, content, has_file, has_reasoning])
    
    return output.getvalue()

# Helper: Save conversation to TXT
def export_conversation_to_txt() -> str:
    """Export conversation history to plain text format"""
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
st.caption("🔒 Production Ready with Security Scanner | 한국어 & English Support 🌐")

# Sidebar
with st.sidebar:
    st.header("🛠️ Available Tools")
    st.success("✅ Math Operations")
    st.success("✅ File Read/Write")
    st.success("✅ Directory Listing")
    st.success("✅ Time & Greetings")
    st.success("✅ Command Execution")
    st.success("✅ File Download")
    st.success("✅ Security Scanner")
    
    st.divider()
    
    st.header("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Admin Logs", len(st.session_state.admin_logs))
    st.metric("Security Scans", len(st.session_state.security_scans))
    st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    st.header("⚙️ Settings")
    show_reasoning = st.checkbox("Show Reasoning", value=True, help="Display AI's thought process")
    show_admin = st.checkbox("Show Admin Dashboard", value=False, help="Display system logs")
    auto_security_scan = st.checkbox("Auto Security Scan", value=True, help="Automatically scan code files")
    
    st.divider()
    
    st.header("📥 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 CSV"):
            csv_data = export_conversation_to_csv()
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📄 TXT"):
            txt_data = export_conversation_to_txt()
            st.download_button(
                label="⬇️ Download TXT",
                data=txt_data,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🧹 Clear Logs"):
        st.session_state.admin_logs = []
        st.session_state.security_scans = []
        st.rerun()

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "reasoning" in message and show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in message["reasoning"]:
                    st.caption(f"**{step['step']}:** {step['text']}")
        
        # Display security scan results
        if "security_scan" in message:
            scan = message["security_scan"]
            
            status_colors = {
                "SAFE": "🟢",
                "CAUTION": "🟡",
                "VULNERABLE": "🔴"
            }
            
            with st.expander(f"🔒 Security Scan: {status_colors.get(scan['status'], '⚪')} {scan['status']} (Score: {scan['score']}/100)", expanded=(scan['status'] != 'SAFE')):
                if scan['status'] == 'SAFE':
                    st.success("✅ No security issues detected!")
                else:
                    if scan['issues']:
                        st.error(f"🚨 Found {len(scan['issues'])} critical issue(s):")
                        for issue in scan['issues']:
                            st.markdown(f"**{issue['severity']}**: {issue['type']} (Line {issue['line']})")
                            st.caption(issue['description'])
                    
                    if scan['warnings']:
                        st.warning(f"⚠️ Found {len(scan['warnings'])} warning(s):")
                        for warning in scan['warnings']:
                            st.markdown(f"**{warning['severity']}**: {warning['type']}")
                            st.caption(warning['description'])
        
        st.markdown(message["content"])
        
        # Add download button if file content is cached
        if message["role"] == "assistant" and "file_data" in message:
            file_data = message["file_data"]
            st.download_button(
                label=f"⬇️ Download {file_data['filename']}",
                data=file_data['content'],
                file_name=file_data['filename'],
                mime='text/plain',
                key=f"download_{idx}"
            )

# Helper functions
def detect_language(text: str) -> str:
    korean_chars = len(re.findall(r'[가-힣]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return "ko" if korean_chars > english_chars else "en"

def get_file_language(filename: str) -> str:
    ext_map = {
        '.py': 'python', '.js': 'javascript', '.html': 'html',
        '.css': 'css', '.json': 'json', '.yaml': 'yaml',
        '.yml': 'yaml', '.md': 'markdown', '.txt': 'text',
        '.sh': 'bash', '.sql': 'sql'
    }
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return 'text'

def execute_command(command: str) -> str:
    try:
        add_admin_log(command, "Executing...", "running")
        result = subprocess.run(command, shell=True, capture_output=True, 
                              text=True, cwd=BASE_DIR, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        status = "success" if result.returncode == 0 else "error"
        add_admin_log(command, output[:200] if output else "Success", status)
        return output if output else "Command executed successfully"
    except subprocess.TimeoutExpired:
        add_admin_log(command, "Timeout after 30s", "error")
        return "Error: Command timed out"
    except Exception as e:
        add_admin_log(command, str(e), "error")
        return f"Error: {str(e)}"

# Process user input
def process_user_request_with_reasoning(user_input: str, status_container):
    user_lower = user_input.lower()
    lang = detect_language(user_input)
    reasoning_steps = []
    file_data = None
    security_scan_result = None
    
    reasoning_steps.append({
        "step": "Language Detection" if lang == "en" else "언어 감지",
        "text": f"Detected: {'English' if lang == 'en' else 'Korean'}"
    })
    status_container.update(label="🌐 Detecting language...", state="running")
    time.sleep(0.2)
    
    try:
        status_container.update(label="🎯 Analyzing intent...", state="running")
        
        # Math Operations
        if any(keyword in user_lower for keyword in ["더하기", "덧셈", "plus", "add", "sum", "+"]):
            numbers = re.findall(r'-?\d+', user_input)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                add_admin_log(f"utils.add_numbers({a}, {b})", "Calculating...", "running")
                result = utils.add_numbers(a, b)
                add_admin_log(f"utils.add_numbers({a}, {b})", f"Result: {result}", "success")
                status_container.update(label="✅ Complete!", state="complete")
                
                return (f"계산 결과: {a} + {b} = **{result}** ✨" if lang == "ko" 
                       else f"Calculation result: {a} + {b} = **{result}** ✨"), reasoning_steps, file_data, security_scan_result
        
        # File Read with Security Scan
        elif any(keyword in user_lower for keyword in ["파일 읽", "read file", "파일 보", "show file", "open file"]):
            words = user_input.split()
            filename = None
            
            for word in words:
                if any(ext in word for ext in [".py", ".txt", ".md", ".json", ".yaml", ".js", ".html", ".css"]):
                    filename = word
                    break
            
            if filename:
                try:
                    add_admin_log(f"read_file({filename})", "Reading...", "running")
                    safe_path = utils.validate_safe_path(filename, BASE_DIR)
                    file_size = os.path.getsize(safe_path)
                    
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    add_admin_log(f"read_file({filename})", f"Read {len(content)} chars", "success")
                    
                    # Security Scan for code files
                    if auto_security_scan and filename.endswith(('.py', '.js', '.sh')):
                        status_container.update(label="🔒 Running security scan...", state="running")
                        security_scan_result = security_scan(content, filename)
                        st.session_state.security_scans.append(security_scan_result)
                        add_admin_log(f"security_scan({filename})", 
                                    f"Score: {security_scan_result['score']}/100", 
                                    "success" if security_scan_result['status'] == 'SAFE' else "error")
                    
                    file_data = {"filename": filename, "content": content}
                    file_lang = get_file_language(filename)
                    status_container.update(label="✅ Complete!", state="complete")
                    
                    max_display = 2000
                    truncated = content[:max_display]
                    is_truncated = len(content) > max_display
                    
                    result = f"📄 **{filename}** ({file_size:,} bytes)\n\n"
                    result += f"```{file_lang}\n{truncated}\n```"
                    
                    if is_truncated:
                        result += f"\n\n*📝 {'전체 파일을 다운로드하세요!' if lang == 'ko' else 'Download the full file!'}*"
                    
                    return result, reasoning_steps, file_data, security_scan_result
                    
                except Exception as e:
                    add_admin_log(f"read_file({filename})", str(e), "error")
                    status_container.update(label="❌ Error", state="error")
                    return f"❌ Failed: {str(e)}", reasoning_steps, file_data, security_scan_result
        
        # File List
        elif any(keyword in user_lower for keyword in ["파일 목록", "list files", "무슨 파일", "show files"]):
            try:
                add_admin_log("list_files", "Scanning...", "running")
                files = os.listdir(BASE_DIR)
                files = [f for f in files if not f.startswith('.') and not f.startswith('__')]
                add_admin_log("list_files", f"Found {len(files)} files", "success")
                status_container.update(label="✅ Complete!", state="complete")
                
                result = f"📁 **{'파일 목록' if lang == 'ko' else 'File List'}** ({len(files)}개)\n\n"
                for f in sorted(files):
                    icon = "🐍" if f.endswith('.py') else "📝" if f.endswith('.md') else "📄"
                    result += f"{icon} `{f}`\n"
                
                return result, reasoning_steps, file_data, security_scan_result
            except Exception as e:
                return f"❌ Failed: {str(e)}", reasoning_steps, file_data, security_scan_result
        
        # Time
        elif any(keyword in user_lower for keyword in ["시간", "time", "몇시", "clock"]):
            add_admin_log("get_time", "Fetching...", "running")
            current_time = utils.get_current_time_only()
            add_admin_log("get_time", current_time, "success")
            status_container.update(label="✅ Complete!", state="complete")
            return f"⏰ **{current_time}**", reasoning_steps, file_data, security_scan_result
        
        # Help
        elif any(keyword in user_lower for keyword in ["도움말", "help", "commands"]):
            status_container.update(label="✅ Complete!", state="complete")
            
            if lang == "ko":
                return """
🤖 **사용 가능한 명령어:**
📊 수학: "5 더하기 3"
📁 파일: "파일 목록", "server.py 읽어줘"
⏰ 시간: "지금 몇 시?"
🔒 보안 스캔: 자동으로 코드 파일 검사
📥 내보내기: 사이드바에서 CSV/TXT 다운로드
                """, reasoning_steps, file_data, security_scan_result
            else:
                return """
🤖 **Available Commands:**
📊 Math: "add 5 and 3"
📁 Files: "Show files", "Read server.py"
⏰ Time: "What time is it?"
🔒 Security Scan: Auto-scan code files
📥 Export: Download CSV/TXT from sidebar
                """, reasoning_steps, file_data, security_scan_result
        
        # Default
        else:
            status_container.update(label="✅ Complete!", state="complete")
            return f"'{user_input}' 💡 '도움말' 입력", reasoning_steps, file_data, security_scan_result
    
    except Exception as e:
        add_admin_log("process_request", str(e), "error")
        status_container.update(label="❌ Error", state="error")
        return f"❌ Error: {str(e)}", reasoning_steps, file_data, security_scan_result

# Chat input
if prompt := st.chat_input("메시지를 입력하세요... | Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        status_container = st.status("🤔 Processing...", expanded=True)
        
        response, reasoning, file_data, security_scan_result = process_user_request_with_reasoning(prompt, status_container)
        
        if show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in reasoning:
                    st.caption(f"**{step['step']}:** {step['text']}")
        
        # Display security scan
        if security_scan_result:
            scan = security_scan_result
            status_colors = {"SAFE": "🟢", "CAUTION": "🟡", "VULNERABLE": "🔴"}
            
            with st.expander(f"🔒 Security Scan: {status_colors.get(scan['status'], '⚪')} {scan['status']} (Score: {scan['score']}/100)", expanded=(scan['status'] != 'SAFE')):
                if scan['status'] == 'SAFE':
                    st.success("✅ No security issues detected!")
                else:
                    if scan['issues']:
                        st.error(f"🚨 {len(scan['issues'])} critical issue(s)")
                        for issue in scan['issues']:
                            st.markdown(f"**{issue['severity']}**: {issue['type']} (Line {issue['line']})")
                            st.caption(issue['description'])
                    if scan['warnings']:
                        st.warning(f"⚠️ {len(scan['warnings'])} warning(s)")
                        for warning in scan['warnings']:
                            st.markdown(f"**{warning['severity']}**: {warning['type']}")
                            st.caption(warning['description'])
        
        st.markdown(response)
        
        if file_data:
            st.download_button(
                label=f"⬇️ Download {file_data['filename']}",
                data=file_data['content'],
                file_name=file_data['filename'],
                mime='text/plain',
                key="download_latest"
            )
    
    # Store message
    msg_data = {"role": "assistant", "content": response, "reasoning": reasoning}
    if file_data:
        msg_data["file_data"] = file_data
    if security_scan_result:
        msg_data["security_scan"] = security_scan_result
    
    st.session_state.messages.append(msg_data)

# Admin Dashboard
if show_admin:
    st.divider()
    st.subheader("🔧 Admin Dashboard")
    
    if st.session_state.admin_logs:
        tab1, tab2, tab3 = st.tabs(["📜 Recent Logs", "📊 Statistics", "🔒 Security Scans"])
        
        with tab1:
            for log in reversed(st.session_state.admin_logs[-10:]):
                status_color = {"success": "🟢", "error": "🔴", "running": "🟡"}.get(log["status"], "⚪")
                with st.expander(f"{status_color} [{log['timestamp']}] {log['command']}", expanded=False):
                    st.code(log['output'], language='bash')
        
        with tab2:
            col1, col2, col3 = st.columns(3)
            success_count = sum(1 for log in st.session_state.admin_logs if log['status'] == 'success')
            error_count = sum(1 for log in st.session_state.admin_logs if log['status'] == 'error')
            col1.metric("Total", len(st.session_state.admin_logs))
            col2.metric("Success", success_count)
            col3.metric("Errors", error_count)
        
        with tab3:
            if st.session_state.security_scans:
                for scan in reversed(st.session_state.security_scans[-5:]):
                    status_emoji = {"SAFE": "🟢", "CAUTION": "🟡", "VULNERABLE": "🔴"}.get(scan['status'], "⚪")
                    st.markdown(f"{status_emoji} **{scan['filename']}** - Score: {scan['score']}/100 ({scan['timestamp']})")
            else:
                st.info("No security scans yet")
    else:
        st.info("No logs yet. Start using commands!")

# Footer
st.divider()
st.caption("🔒 Security Scanner | 🚀 MCP Powered | ⚡ Streamlit | 🌐 Bilingual | 🧠 Thought Trace | 📥 CSV/TXT Export | 🔧 Admin Dashboard")
