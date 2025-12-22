"""
Streamlit Chatbot Application
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
Supports both Korean and English natural language
"""

import streamlit as st
import utils
import os
import re
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="🤖 My Desktop Assistant",
    page_icon="🤖",
    layout="wide"
)

# Constants
BASE_DIR = "/Users/hyunhocho/Desktop/Stanford_CS/week2"

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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
    
    st.divider()
    
    st.header("📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Helper function to detect language
def detect_language(text: str) -> str:
    """Detect if text is primarily Korean or English"""
    korean_chars = len(re.findall(r'[가-힣]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return "ko" if korean_chars > english_chars else "en"

# Process user input
def process_user_request(user_input: str) -> str:
    """
    사용자 입력을 분석하고 적절한 MCP 도구를 호출하여 응답을 생성합니다.
    Supports both Korean and English input
    """
    user_lower = user_input.lower()
    lang = detect_language(user_input)
    
    try:
        # Math Operations
        if any(keyword in user_lower for keyword in ["더하기", "덧셈", "plus", "add", "sum", "+"]):
            # Extract numbers
            numbers = re.findall(r'-?\d+', user_input)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                result = utils.add_numbers(a, b)
                if lang == "ko":
                    return f"계산 결과: {a} + {b} = {result} ✨"
                else:
                    return f"Calculation result: {a} + {b} = {result} ✨"
            if lang == "ko":
                return "두 개의 숫자를 입력해주세요. 예: '5 더하기 3' 또는 '5 + 3'"
            else:
                return "Please provide two numbers. Example: 'add 5 and 3' or '5 + 3'"
        
        # Greeting
        elif any(keyword in user_lower for keyword in ["안녕", "hello", "hi", "hey", "greet"]):
            # Extract name if provided
            name = None
            
            # Korean pattern: "나는 [이름]" or "내 이름은 [이름]"
            korean_patterns = [
                r'나는\s+([가-힣a-zA-Z]+)',
                r'내\s*이름은\s+([가-힣a-zA-Z]+)',
                r'이름은\s+([가-힣a-zA-Z]+)'
            ]
            
            # English pattern: "I'm [name]" or "I am [name]" or "my name is [name]"
            english_patterns = [
                r"i'?m\s+([a-zA-Z가-힣]+)",
                r"i\s+am\s+([a-zA-Z가-힣]+)",
                r"my\s+name\s+is\s+([a-zA-Z가-힣]+)",
                r"name\s+is\s+([a-zA-Z가-힣]+)"
            ]
            
            # Try to extract name
            for pattern in korean_patterns + english_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    name = match.group(1).strip()
                    break
            
            if name:
                return utils.format_greeting(name)
            else:
                if lang == "ko":
                    return utils.format_greeting("친구")
                else:
                    # Return English version
                    current_time = utils.get_current_time_only()
                    return f"Hello, friend! Current time is {current_time}. 👋"
        
        # Time
        elif any(keyword in user_lower for keyword in ["시간", "time", "몇시", "what time", "clock"]):
            if any(keyword in user_lower for keyword in ["날짜", "date", "오늘", "today"]):
                current_datetime = utils.get_current_datetime()
                if lang == "ko":
                    return f"현재 날짜와 시간: {current_datetime} 🕐"
                else:
                    return f"Current date and time: {current_datetime} 🕐"
            else:
                current_time = utils.get_current_time_only()
                if lang == "ko":
                    return f"현재 시간: {current_time} ⏰"
                else:
                    return f"Current time: {current_time} ⏰"
        
        # File Read
        elif any(keyword in user_lower for keyword in ["파일 읽", "read file", "파일 보", "show file", "open file"]):
            # Extract filename
            words = user_input.split()
            filename = None
            
            for word in words:
                # Check for common file extensions
                if any(ext in word for ext in [".py", ".txt", ".md", ".json", ".yaml", ".yml", ".js", ".html", ".css"]):
                    filename = word
                    break
            
            if filename:
                try:
                    safe_path = utils.validate_safe_path(filename, BASE_DIR)
                    
                    # Check file size
                    file_size = os.path.getsize(safe_path)
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        if lang == "ko":
                            return f"⚠️ 파일이 너무 큽니다 ({file_size} bytes). 최대 10MB까지 읽을 수 있습니다."
                        else:
                            return f"⚠️ File is too large ({file_size} bytes). Maximum size is 10MB."
                    
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Truncate if too long
                    max_display = 1000
                    truncated = content[:max_display]
                    is_truncated = len(content) > max_display
                    
                    if lang == "ko":
                        return f"📄 **{filename}** 내용:\n```\n{truncated}{'... (생략됨)' if is_truncated else ''}\n```"
                    else:
                        return f"📄 **{filename}** contents:\n```\n{truncated}{'... (truncated)' if is_truncated else ''}\n```"
                except Exception as e:
                    if lang == "ko":
                        return f"❌ 파일 읽기 실패: {str(e)}"
                    else:
                        return f"❌ Failed to read file: {str(e)}"
            
            if lang == "ko":
                return "파일명을 포함해주세요. 예: 'server.py 파일 읽어줘'"
            else:
                return "Please include a filename. Example: 'read server.py'"
        
        # File List
        elif any(keyword in user_lower for keyword in ["파일 목록", "list files", "무슨 파일", "what files", "show files", "파일들"]):
            try:
                files = os.listdir(BASE_DIR)
                files = [f for f in files if not f.startswith('.') and not f.startswith('__')]
                
                if lang == "ko":
                    result = f"📁 **파일 목록** ({len(files)}개):\n"
                else:
                    result = f"📁 **File List** ({len(files)} files):\n"
                
                result += "\n".join([f"- {f}" for f in sorted(files)])
                return result
            except Exception as e:
                if lang == "ko":
                    return f"❌ 파일 목록 조회 실패: {str(e)}"
                else:
                    return f"❌ Failed to list files: {str(e)}"
        
        # Help
        elif any(keyword in user_lower for keyword in ["도움말", "help", "뭐 할 수 있어", "what can you do", "commands", "기능"]):
            if lang == "ko":
                return """
🤖 **사용 가능한 명령어:**

📊 **수학 계산**
- "5 더하기 3" 또는 "5 + 3"
- "add 5 and 3"

👋 **인사**
- "안녕하세요" 또는 "Hello"
- "안녕 나는 홍길동" 또는 "Hi, I'm John"

⏰ **시간 확인**
- "지금 몇 시야?" 또는 "What time is it?"
- "오늘 날짜" 또는 "Today's date"

📁 **파일 관리**
- "파일 목록 보여줘" 또는 "Show files"
- "server.py 파일 읽어줘" 또는 "Read server.py"

💡 **한국어와 영어 모두 자연스럽게 사용하세요!**
                """
            else:
                return """
🤖 **Available Commands:**

📊 **Math Operations**
- "5 plus 3" or "5 + 3"
- "add 5 and 3"

👋 **Greetings**
- "Hello" or "안녕하세요"
- "Hi, I'm John" or "안녕 나는 홍길동"

⏰ **Time Check**
- "What time is it?" or "지금 몇 시야?"
- "Today's date" or "오늘 날짜"

📁 **File Management**
- "Show files" or "파일 목록 보여줘"
- "Read server.py" or "server.py 파일 읽어줘"

💡 **Use both Korean and English naturally!**
                """
        
        # Default response
        else:
            if lang == "ko":
                return f"'{user_input}'에 대한 응답을 생각하고 있어요. '도움말'을 입력하면 제가 할 수 있는 일을 볼 수 있어요! 💡"
            else:
                return f"I'm thinking about '{user_input}'. Type 'help' to see what I can do! 💡"
    
    except ValueError as e:
        if lang == "ko":
            return f"⚠️ 입력 오류: {str(e)}"
        else:
            return f"⚠️ Input error: {str(e)}"
    except Exception as e:
        if lang == "ko":
            return f"❌ 처리 중 오류 발생: {str(e)}"
        else:
            return f"❌ Error occurred: {str(e)}"

# Chat input
if prompt := st.chat_input("메시지를 입력하세요... | Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process and generate response
    with st.chat_message("assistant"):
        with st.spinner("생각 중... | Thinking..."):
            response = process_user_request(prompt)
            st.markdown(response)
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.caption("🔒 Security-enhanced | 🚀 Powered by MCP | ⚡ Built with Streamlit | 🌐 Korean & English Support")
