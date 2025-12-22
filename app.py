"""
Streamlit Chatbot Application
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
"""

import streamlit as st
import utils
import os
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
st.caption("Powered by MCP Tools - Math, File Operations, Time & More!")

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

# Process user input
def process_user_request(user_input: str) -> str:
    """
    사용자 입력을 분석하고 적절한 MCP 도구를 호출하여 응답을 생성합니다.
    """
    user_lower = user_input.lower()
    
    try:
        # Math Operations
        if "더하기" in user_lower or "+" in user_input or "덧셈" in user_lower:
            # Extract numbers
            import re
            numbers = re.findall(r'-?\d+', user_input)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                result = utils.add_numbers(a, b)
                return f"계산 결과: {a} + {b} = {result} ✨"
            return "두 개의 숫자를 입력해주세요. 예: '5 더하기 3'"
        
        # Greeting
        elif "안녕" in user_lower or "hello" in user_lower or "hi" in user_lower:
            # Extract name if provided
            import re
            # Try to extract name after 안녕 or hello
            if "나는" in user_input or "i'm" in user_lower or "i am" in user_lower:
                words = user_input.replace("나는", "").replace("I'm", "").replace("i'm", "").replace("I am", "").replace("i am", "").strip().split()
                if words:
                    name = words[0]
                    return utils.format_greeting(name)
            return utils.format_greeting("친구")
        
        # Time
        elif "시간" in user_lower or "time" in user_lower or "몇시" in user_lower:
            if "날짜" in user_lower or "date" in user_lower:
                return f"현재 날짜와 시간: {utils.get_current_datetime()} 🕐"
            return f"현재 시간: {utils.get_current_time_only()} ⏰"
        
        # File Read
        elif "파일 읽어" in user_lower or "read file" in user_lower or "파일 보여" in user_lower:
            # Extract filename
            words = user_input.split()
            for word in words:
                if ".py" in word or ".txt" in word or ".md" in word:
                    try:
                        safe_path = utils.validate_safe_path(word, BASE_DIR)
                        with open(safe_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return f"📄 **{word}** 내용:\n```\n{content[:500]}{'...' if len(content) > 500 else ''}\n```"
                    except Exception as e:
                        return f"파일 읽기 실패: {str(e)}"
            return "파일명을 포함해주세요. 예: 'server.py 파일 읽어줘'"
        
        # File List
        elif "파일 목록" in user_lower or "list files" in user_lower or "무슨 파일" in user_lower:
            try:
                files = os.listdir(BASE_DIR)
                files = [f for f in files if not f.startswith('.')]
                return f"📁 **파일 목록** ({len(files)}개):\n" + "\n".join([f"- {f}" for f in sorted(files)])
            except Exception as e:
                return f"파일 목록 조회 실패: {str(e)}"
        
        # Help
        elif "도움말" in user_lower or "help" in user_lower or "뭐 할 수 있어" in user_lower:
            return """
🤖 **사용 가능한 명령어:**

📊 **수학 계산**
- "5 더하기 3" 또는 "5 + 3"

👋 **인사**
- "안녕하세요" 또는 "Hello"
- "안녕 나는 홍길동" (이름 포함)

⏰ **시간 확인**
- "지금 몇 시야?" 또는 "현재 시간"
- "오늘 날짜" (날짜 포함)

📁 **파일 관리**
- "파일 목록 보여줘"
- "server.py 파일 읽어줘"

💡 궁금한 것을 자연스럽게 물어보세요!
            """
        
        # Default response
        else:
            return f"'{user_input}'에 대한 응답을 준비 중입니다. '도움말'을 입력하면 사용 가능한 명령어를 볼 수 있어요! 💡"
    
    except ValueError as e:
        return f"⚠️ 입력 오류: {str(e)}"
    except Exception as e:
        return f"❌ 처리 중 오류 발생: {str(e)}"

# Chat input
if prompt := st.chat_input("메시지를 입력하세요..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process and generate response
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            response = process_user_request(prompt)
            st.markdown(response)
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.caption("🔒 Security-enhanced | 🚀 Powered by MCP | ⚡ Built with Streamlit")
