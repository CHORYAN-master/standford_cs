"""
Streamlit Chatbot Application - Production Ready
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
Features: Thought Trace, File Download, Admin Dashboard
Supports Korean & English
"""

import streamlit as st
import utils
import os
import re
from datetime import datetime
import time
import subprocess

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
if "file_cache" not in st.session_state:
    st.session_state.file_cache = {}

# Helper: Add admin log
def add_admin_log(command: str, output: str, status: str = "success"):
    """Add a log entry to admin dashboard"""
    st.session_state.admin_logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "command": command,
        "output": output,
        "status": status
    })
    # Keep only last 50 logs
    if len(st.session_state.admin_logs) > 50:
        st.session_state.admin_logs.pop(0)

# App Header
st.title("🤖 My Desktop Assistant")
st.caption("Powered by MCP Tools - Math, File Operations, Time & More! | 한국어와 English 모두 지원 🌐")

# Sidebar - Tool Status
with st.sidebar:
    st.header("🛠️ Available Tools")
    st.success("✅ Math Operations")
    st.success("✅ File Read/Write")
    st.success("✅ Directory Listing")
    st.success("✅ Time & Greetings")
    st.success("✅ Command Execution")
    st.success("✅ File Download")
    
    st.divider()
    
    st.header("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Admin Logs", len(st.session_state.admin_logs))
    st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    st.header("⚙️ Settings")
    show_reasoning = st.checkbox("Show Reasoning", value=True, help="Display AI's thought process")
    show_admin = st.checkbox("Show Admin Dashboard", value=False, help="Display system logs")
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🧹 Clear Logs"):
        st.session_state.admin_logs = []
        st.rerun()

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "reasoning" in message and show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in message["reasoning"]:
                    st.caption(f"**{step['step']}:** {step['text']}")
        
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

# Helper function to detect language
def detect_language(text: str) -> str:
    """Detect if text is primarily Korean or English"""
    korean_chars = len(re.findall(r'[가-힣]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return "ko" if korean_chars > english_chars else "en"

# Detect file extension for syntax highlighting
def get_file_language(filename: str) -> str:
    """Return the language for syntax highlighting based on file extension"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.txt': 'text',
        '.sh': 'bash',
        '.sql': 'sql'
    }
    
    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang
    return 'text'

# Execute command and log
def execute_command(command: str) -> str:
    """Execute shell command with logging"""
    try:
        add_admin_log(command, "Executing...", "running")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=30
        )
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

# Process user input with reasoning trace
def process_user_request_with_reasoning(user_input: str, status_container):
    """
    사용자 입력을 분석하고 적절한 MCP 도구를 호출하여 응답을 생성합니다.
    생각 과정을 실시간으로 표시합니다.
    """
    user_lower = user_input.lower()
    lang = detect_language(user_input)
    reasoning_steps = []
    file_data = None
    
    # Step 1: Language Detection
    reasoning_steps.append({
        "step": "Language Detection" if lang == "en" else "언어 감지",
        "text": f"Detected language: {'English' if lang == 'en' else 'Korean'} | 감지된 언어: {'영어' if lang == 'en' else '한국어'}"
    })
    status_container.update(label="🌐 Detecting language..." if lang == "en" else "🌐 언어 감지 중...", state="running")
    time.sleep(0.2)
    
    try:
        # Step 2: Intent Classification
        status_container.update(label="🎯 Analyzing intent..." if lang == "en" else "🎯 의도 분석 중...", state="running")
        
        # Math Operations
        if any(keyword in user_lower for keyword in ["더하기", "덧셈", "plus", "add", "sum", "+"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Mathematical operation detected | 수학 계산 감지"
            })
            
            numbers = re.findall(r'-?\d+', user_input)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                
                reasoning_steps.append({
                    "step": "Extraction" if lang == "en" else "추출",
                    "text": f"Numbers extracted: {a}, {b}"
                })
                
                add_admin_log(f"utils.add_numbers({a}, {b})", "Calculating...", "running")
                result = utils.add_numbers(a, b)
                add_admin_log(f"utils.add_numbers({a}, {b})", f"Result: {result}", "success")
                
                status_container.update(label="✅ Complete!", state="complete")
                
                if lang == "ko":
                    return f"계산 결과: {a} + {b} = **{result}** ✨", reasoning_steps, file_data
                else:
                    return f"Calculation result: {a} + {b} = **{result}** ✨", reasoning_steps, file_data
        
        # Greeting
        elif any(keyword in user_lower for keyword in ["안녕", "hello", "hi", "hey", "greet"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Greeting detected"
            })
            
            name = None
            korean_patterns = [r'나는\s+([가-힣a-zA-Z]+)', r'내\s*이름은\s+([가-힣a-zA-Z]+)']
            english_patterns = [r"i'?m\s+([a-zA-Z가-힣]+)", r"my\s+name\s+is\s+([a-zA-Z가-힣]+)"]
            
            for pattern in korean_patterns + english_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    name = match.group(1).strip()
                    break
            
            name = name or ("친구" if lang == "ko" else "friend")
            
            add_admin_log(f"utils.format_greeting('{name}')", "Generating...", "running")
            
            if lang == "ko":
                result = utils.format_greeting(name)
            else:
                current_time = utils.get_current_time_only()
                result = f"Hello, {name}! Current time is {current_time}. 👋"
            
            add_admin_log(f"utils.format_greeting('{name}')", "Success", "success")
            status_container.update(label="✅ Complete!", state="complete")
            return result, reasoning_steps, file_data
        
        # Time
        elif any(keyword in user_lower for keyword in ["시간", "time", "몇시", "what time", "clock"]):
            include_date = any(keyword in user_lower for keyword in ["날짜", "date", "오늘", "today"])
            
            if include_date:
                add_admin_log("utils.get_current_datetime()", "Fetching...", "running")
                current_datetime = utils.get_current_datetime()
                add_admin_log("utils.get_current_datetime()", current_datetime, "success")
                status_container.update(label="✅ Complete!", state="complete")
                
                if lang == "ko":
                    return f"📅 현재 날짜와 시간: **{current_datetime}** 🕐", reasoning_steps, file_data
                else:
                    return f"📅 Current date and time: **{current_datetime}** 🕐", reasoning_steps, file_data
            else:
                add_admin_log("utils.get_current_time_only()", "Fetching...", "running")
                current_time = utils.get_current_time_only()
                add_admin_log("utils.get_current_time_only()", current_time, "success")
                status_container.update(label="✅ Complete!", state="complete")
                
                if lang == "ko":
                    return f"⏰ 현재 시간: **{current_time}**", reasoning_steps, file_data
                else:
                    return f"⏰ Current time: **{current_time}**", reasoning_steps, file_data
        
        # File Read
        elif any(keyword in user_lower for keyword in ["파일 읽", "read file", "파일 보", "show file", "open file"]):
            words = user_input.split()
            filename = None
            
            for word in words:
                if any(ext in word for ext in [".py", ".txt", ".md", ".json", ".yaml", ".yml", ".js", ".html", ".css"]):
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
                    
                    # Cache file for download
                    file_data = {
                        "filename": filename,
                        "content": content
                    }
                    
                    file_lang = get_file_language(filename)
                    status_container.update(label="✅ Complete!", state="complete")
                    
                    max_display = 2000
                    truncated = content[:max_display]
                    is_truncated = len(content) > max_display
                    
                    result = f"📄 **{filename}** ({file_size:,} bytes)\n\n"
                    result += f"```{file_lang}\n{truncated}\n```"
                    
                    if is_truncated:
                        if lang == "ko":
                            result += f"\n\n*📝 전체 파일을 다운로드 버튼으로 받으세요!*"
                        else:
                            result += f"\n\n*📝 Download the full file using the button below!*"
                    
                    return result, reasoning_steps, file_data
                    
                except Exception as e:
                    add_admin_log(f"read_file({filename})", str(e), "error")
                    status_container.update(label="❌ Error", state="error")
                    return f"❌ Failed to read file: {str(e)}", reasoning_steps, file_data
        
        # File List
        elif any(keyword in user_lower for keyword in ["파일 목록", "list files", "무슨 파일", "what files", "show files"]):
            try:
                add_admin_log("list_files", "Scanning...", "running")
                files = os.listdir(BASE_DIR)
                files = [f for f in files if not f.startswith('.') and not f.startswith('__')]
                add_admin_log("list_files", f"Found {len(files)} files", "success")
                
                status_container.update(label="✅ Complete!", state="complete")
                
                if lang == "ko":
                    result = f"📁 **파일 목록** ({len(files)}개)\n\n"
                else:
                    result = f"📁 **File List** ({len(files)} files)\n\n"
                
                for f in sorted(files):
                    icon = "🐍" if f.endswith('.py') else "📝" if f.endswith('.md') else "📄"
                    result += f"{icon} `{f}`\n"
                
                return result, reasoning_steps, file_data
                
            except Exception as e:
                add_admin_log("list_files", str(e), "error")
                return f"❌ Failed: {str(e)}", reasoning_steps, file_data
        
        # Git/Graphite Commands
        elif any(keyword in user_lower for keyword in ["git ", "gt ", "graphite"]):
            # Extract command
            if "git " in user_lower:
                cmd_start = user_input.lower().find("git ")
                command = user_input[cmd_start:].strip()
            elif "gt " in user_lower:
                cmd_start = user_input.lower().find("gt ")
                command = user_input[cmd_start:].strip()
            else:
                command = "gt log"
            
            add_admin_log(command, "Executing...", "running")
            output = execute_command(command)
            status_container.update(label="✅ Complete!", state="complete")
            
            if lang == "ko":
                result = f"🔧 **명령어 실행 결과:**\n```bash\n$ {command}\n{output}\n```"
            else:
                result = f"🔧 **Command Output:**\n```bash\n$ {command}\n{output}\n```"
            
            return result, reasoning_steps, file_data
        
        # Help
        elif any(keyword in user_lower for keyword in ["도움말", "help", "commands"]):
            status_container.update(label="✅ Complete!", state="complete")
            
            if lang == "ko":
                return """
🤖 **사용 가능한 명령어:**

📊 **수학**: "5 더하기 3"
👋 **인사**: "안녕 나는 현호"
⏰ **시간**: "지금 몇 시?"
📁 **파일**: "파일 목록", "server.py 읽어줘"
🔧 **Git**: "gt log", "git status"
⬇️ **다운로드**: 파일 읽기 후 다운로드 버튼 사용

💡 한국어와 영어 모두 지원!
                """, reasoning_steps, file_data
            else:
                return """
🤖 **Available Commands:**

📊 **Math**: "add 5 and 3"
👋 **Greet**: "Hi, I'm John"
⏰ **Time**: "What time is it?"
📁 **Files**: "Show files", "Read server.py"
🔧 **Git**: "gt log", "git status"
⬇️ **Download**: Use download button after reading files

💡 Korean & English supported!
                """, reasoning_steps, file_data
        
        # Default
        else:
            status_container.update(label="✅ Complete!", state="complete")
            if lang == "ko":
                return f"'{user_input}'에 대한 응답입니다. '도움말'로 명령어를 확인하세요! 💡", reasoning_steps, file_data
            else:
                return f"Response for '{user_input}'. Type 'help' for commands! 💡", reasoning_steps, file_data
    
    except Exception as e:
        add_admin_log("process_request", str(e), "error")
        status_container.update(label="❌ Error", state="error")
        return f"❌ Error: {str(e)}", reasoning_steps, file_data

# Chat input
if prompt := st.chat_input("메시지를 입력하세요... | Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        status_container = st.status("🤔 Processing...", expanded=True)
        
        response, reasoning, file_data = process_user_request_with_reasoning(prompt, status_container)
        
        if show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in reasoning:
                    st.caption(f"**{step['step']}:** {step['text']}")
        
        st.markdown(response)
        
        # Add download button if file was read
        if file_data:
            st.download_button(
                label=f"⬇️ Download {file_data['filename']}",
                data=file_data['content'],
                file_name=file_data['filename'],
                mime='text/plain',
                key=f"download_latest"
            )
    
    # Store message with file data
    msg_data = {
        "role": "assistant", 
        "content": response,
        "reasoning": reasoning
    }
    if file_data:
        msg_data["file_data"] = file_data
    
    st.session_state.messages.append(msg_data)

# Admin Dashboard
if show_admin:
    st.divider()
    st.subheader("🔧 Admin Dashboard")
    
    if st.session_state.admin_logs:
        # Create tabs for different log views
        tab1, tab2 = st.tabs(["📜 Recent Logs", "📊 Statistics"])
        
        with tab1:
            # Display logs in reverse order (most recent first)
            for log in reversed(st.session_state.admin_logs[-10:]):
                status_color = {
                    "success": "🟢",
                    "error": "🔴",
                    "running": "🟡"
                }.get(log["status"], "⚪")
                
                with st.expander(f"{status_color} [{log['timestamp']}] {log['command']}", expanded=False):
                    st.code(log['output'], language='bash')
        
        with tab2:
            col1, col2, col3 = st.columns(3)
            
            success_count = sum(1 for log in st.session_state.admin_logs if log['status'] == 'success')
            error_count = sum(1 for log in st.session_state.admin_logs if log['status'] == 'error')
            total_count = len(st.session_state.admin_logs)
            
            col1.metric("Total Commands", total_count)
            col2.metric("Successful", success_count)
            col3.metric("Errors", error_count)
    else:
        st.info("No logs yet. Start using commands to see activity here!")

# Footer
st.divider()
st.caption("🔒 Security-enhanced | 🚀 Powered by MCP | ⚡ Built with Streamlit | 🌐 Bilingual | 🧠 Thought Trace | ⬇️ File Download | 🔧 Admin Dashboard")
