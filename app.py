"""
Streamlit Chatbot Application with Thought Trace UI
연결된 MCP 도구들을 활용하여 사용자와 대화하는 챗봇
Supports both Korean and English with enhanced reasoning visualization
"""

import streamlit as st
import utils
import os
import re
from datetime import datetime
import time

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
    
    st.header("⚙️ Settings")
    show_reasoning = st.checkbox("Show Reasoning", value=True, help="Display AI's thought process")
    
    st.divider()
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "reasoning" in message and show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in message["reasoning"]:
                    st.caption(f"**{step['step']}:** {step['text']}")
        st.markdown(message["content"])

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

# Process user input with reasoning trace
def process_user_request_with_reasoning(user_input: str, status_container):
    """
    사용자 입력을 분석하고 적절한 MCP 도구를 호출하여 응답을 생성합니다.
    생각 과정을 실시간으로 표시합니다.
    """
    user_lower = user_input.lower()
    lang = detect_language(user_input)
    reasoning_steps = []
    
    # Step 1: Language Detection
    reasoning_steps.append({
        "step": "Language Detection" if lang == "en" else "언어 감지",
        "text": f"Detected language: {'English' if lang == 'en' else 'Korean'} | 감지된 언어: {'영어' if lang == 'en' else '한국어'}"
    })
    status_container.update(label="🌐 Detecting language..." if lang == "en" else "🌐 언어 감지 중...", state="running")
    time.sleep(0.3)
    
    try:
        # Step 2: Intent Classification
        status_container.update(label="🎯 Analyzing intent..." if lang == "en" else "🎯 의도 분석 중...", state="running")
        
        # Math Operations
        if any(keyword in user_lower for keyword in ["더하기", "덧셈", "plus", "add", "sum", "+"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Mathematical operation detected | 수학 계산 감지"
            })
            time.sleep(0.2)
            
            # Extract numbers
            numbers = re.findall(r'-?\d+', user_input)
            if len(numbers) >= 2:
                a, b = int(numbers[0]), int(numbers[1])
                
                reasoning_steps.append({
                    "step": "Extraction" if lang == "en" else "추출",
                    "text": f"Numbers extracted: {a}, {b} | 숫자 추출: {a}, {b}"
                })
                status_container.update(label="🔢 Calculating..." if lang == "en" else "🔢 계산 중...", state="running")
                time.sleep(0.2)
                
                reasoning_steps.append({
                    "step": "Tool Call" if lang == "en" else "도구 호출",
                    "text": f"Calling utils.add_numbers({a}, {b}) | utils.add_numbers({a}, {b}) 호출"
                })
                
                result = utils.add_numbers(a, b)
                
                reasoning_steps.append({
                    "step": "Result" if lang == "en" else "결과",
                    "text": f"Computation complete: {result} | 계산 완료: {result}"
                })
                status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
                
                if lang == "ko":
                    return f"계산 결과: {a} + {b} = **{result}** ✨", reasoning_steps
                else:
                    return f"Calculation result: {a} + {b} = **{result}** ✨", reasoning_steps
            
            if lang == "ko":
                return "두 개의 숫자를 입력해주세요. 예: '5 더하기 3' 또는 '5 + 3'", reasoning_steps
            else:
                return "Please provide two numbers. Example: 'add 5 and 3' or '5 + 3'", reasoning_steps
        
        # Greeting
        elif any(keyword in user_lower for keyword in ["안녕", "hello", "hi", "hey", "greet"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Greeting detected | 인사 감지"
            })
            time.sleep(0.2)
            
            # Extract name if provided
            name = None
            korean_patterns = [
                r'나는\s+([가-힣a-zA-Z]+)',
                r'내\s*이름은\s+([가-힣a-zA-Z]+)',
                r'이름은\s+([가-힣a-zA-Z]+)'
            ]
            english_patterns = [
                r"i'?m\s+([a-zA-Z가-힣]+)",
                r"i\s+am\s+([a-zA-Z가-힣]+)",
                r"my\s+name\s+is\s+([a-zA-Z가-힣]+)",
                r"name\s+is\s+([a-zA-Z가-힣]+)"
            ]
            
            status_container.update(label="🔍 Extracting name..." if lang == "en" else "🔍 이름 추출 중...", state="running")
            
            for pattern in korean_patterns + english_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    name = match.group(1).strip()
                    break
            
            if name:
                reasoning_steps.append({
                    "step": "Extraction" if lang == "en" else "추출",
                    "text": f"Name found: {name} | 이름 발견: {name}"
                })
            else:
                name = "친구" if lang == "ko" else "friend"
                reasoning_steps.append({
                    "step": "Extraction" if lang == "en" else "추출",
                    "text": f"No name provided, using default: {name} | 이름 없음, 기본값 사용: {name}"
                })
            
            time.sleep(0.2)
            status_container.update(label="👋 Generating greeting..." if lang == "en" else "👋 인사 생성 중...", state="running")
            
            reasoning_steps.append({
                "step": "Tool Call" if lang == "en" else "도구 호출",
                "text": f"Calling utils.format_greeting('{name}') | utils.format_greeting('{name}') 호출"
            })
            
            if lang == "ko":
                result = utils.format_greeting(name)
            else:
                current_time = utils.get_current_time_only()
                result = f"Hello, {name}! Current time is {current_time}. 👋"
            
            status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
            return result, reasoning_steps
        
        # Time
        elif any(keyword in user_lower for keyword in ["시간", "time", "몇시", "what time", "clock"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Time query detected | 시간 조회 감지"
            })
            time.sleep(0.2)
            
            include_date = any(keyword in user_lower for keyword in ["날짜", "date", "오늘", "today"])
            
            if include_date:
                reasoning_steps.append({
                    "step": "Classification" if lang == "en" else "분류",
                    "text": "Full datetime requested | 전체 날짜/시간 요청"
                })
                status_container.update(label="📅 Getting date & time..." if lang == "en" else "📅 날짜/시간 조회 중...", state="running")
                time.sleep(0.2)
                
                reasoning_steps.append({
                    "step": "Tool Call" if lang == "en" else "도구 호출",
                    "text": "Calling utils.get_current_datetime() | utils.get_current_datetime() 호출"
                })
                
                current_datetime = utils.get_current_datetime()
                status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
                
                if lang == "ko":
                    return f"📅 현재 날짜와 시간: **{current_datetime}** 🕐", reasoning_steps
                else:
                    return f"📅 Current date and time: **{current_datetime}** 🕐", reasoning_steps
            else:
                reasoning_steps.append({
                    "step": "Classification" if lang == "en" else "분류",
                    "text": "Time only requested | 시간만 요청"
                })
                status_container.update(label="⏰ Getting time..." if lang == "en" else "⏰ 시간 조회 중...", state="running")
                time.sleep(0.2)
                
                reasoning_steps.append({
                    "step": "Tool Call" if lang == "en" else "도구 호출",
                    "text": "Calling utils.get_current_time_only() | utils.get_current_time_only() 호출"
                })
                
                current_time = utils.get_current_time_only()
                status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
                
                if lang == "ko":
                    return f"⏰ 현재 시간: **{current_time}** ", reasoning_steps
                else:
                    return f"⏰ Current time: **{current_time}**", reasoning_steps
        
        # File Read
        elif any(keyword in user_lower for keyword in ["파일 읽", "read file", "파일 보", "show file", "open file"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "File read request detected | 파일 읽기 요청 감지"
            })
            time.sleep(0.2)
            
            # Extract filename
            status_container.update(label="🔍 Finding filename..." if lang == "en" else "🔍 파일명 찾는 중...", state="running")
            words = user_input.split()
            filename = None
            
            for word in words:
                if any(ext in word for ext in [".py", ".txt", ".md", ".json", ".yaml", ".yml", ".js", ".html", ".css", ".sh", ".sql"]):
                    filename = word
                    break
            
            if filename:
                reasoning_steps.append({
                    "step": "Extraction" if lang == "en" else "추출",
                    "text": f"Filename found: {filename} | 파일명 발견: {filename}"
                })
                time.sleep(0.2)
                
                try:
                    status_container.update(label="🔒 Validating path..." if lang == "en" else "🔒 경로 검증 중...", state="running")
                    safe_path = utils.validate_safe_path(filename, BASE_DIR)
                    
                    reasoning_steps.append({
                        "step": "Security" if lang == "en" else "보안",
                        "text": f"Path validated successfully | 경로 검증 성공"
                    })
                    time.sleep(0.2)
                    
                    # Check file size
                    file_size = os.path.getsize(safe_path)
                    reasoning_steps.append({
                        "step": "Size Check" if lang == "en" else "크기 확인",
                        "text": f"File size: {file_size:,} bytes | 파일 크기: {file_size:,} bytes"
                    })
                    
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        status_container.update(label="⚠️ File too large" if lang == "en" else "⚠️ 파일이 너무 큼", state="error")
                        if lang == "ko":
                            return f"⚠️ 파일이 너무 큽니다 ({file_size:,} bytes). 최대 10MB까지 읽을 수 있습니다.", reasoning_steps
                        else:
                            return f"⚠️ File is too large ({file_size:,} bytes). Maximum size is 10MB.", reasoning_steps
                    
                    status_container.update(label="📖 Reading file..." if lang == "en" else "📖 파일 읽는 중...", state="running")
                    time.sleep(0.2)
                    
                    with open(safe_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    reasoning_steps.append({
                        "step": "Read Complete" if lang == "en" else "읽기 완료",
                        "text": f"Successfully read {len(content)} characters | {len(content)}자 성공적으로 읽음"
                    })
                    
                    # Detect file language for syntax highlighting
                    file_lang = get_file_language(filename)
                    
                    reasoning_steps.append({
                        "step": "Formatting" if lang == "en" else "포맷팅",
                        "text": f"Applying {file_lang} syntax highlighting | {file_lang} 구문 강조 적용"
                    })
                    
                    status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
                    
                    # Truncate if too long
                    max_display = 2000
                    truncated = content[:max_display]
                    is_truncated = len(content) > max_display
                    
                    if lang == "ko":
                        result = f"📄 **{filename}** ({file_size:,} bytes)\n\n"
                    else:
                        result = f"📄 **{filename}** ({file_size:,} bytes)\n\n"
                    
                    result += f"```{file_lang}\n{truncated}\n```"
                    
                    if is_truncated:
                        if lang == "ko":
                            result += f"\n\n*📝 참고: 처음 {max_display}자만 표시됨 (전체: {len(content)}자)*"
                        else:
                            result += f"\n\n*📝 Note: Showing first {max_display} characters (total: {len(content)})*"
                    
                    return result, reasoning_steps
                    
                except Exception as e:
                    status_container.update(label="❌ Error" if lang == "en" else "❌ 오류", state="error")
                    reasoning_steps.append({
                        "step": "Error" if lang == "en" else "오류",
                        "text": f"Failed: {str(e)} | 실패: {str(e)}"
                    })
                    if lang == "ko":
                        return f"❌ 파일 읽기 실패: {str(e)}", reasoning_steps
                    else:
                        return f"❌ Failed to read file: {str(e)}", reasoning_steps
            
            if lang == "ko":
                return "파일명을 포함해주세요. 예: 'server.py 파일 읽어줘'", reasoning_steps
            else:
                return "Please include a filename. Example: 'read server.py'", reasoning_steps
        
        # File List
        elif any(keyword in user_lower for keyword in ["파일 목록", "list files", "무슨 파일", "what files", "show files", "파일들"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "File list request detected | 파일 목록 요청 감지"
            })
            time.sleep(0.2)
            
            try:
                status_container.update(label="📂 Scanning directory..." if lang == "en" else "📂 디렉토리 스캔 중...", state="running")
                files = os.listdir(BASE_DIR)
                files = [f for f in files if not f.startswith('.') and not f.startswith('__')]
                
                reasoning_steps.append({
                    "step": "Scan Complete" if lang == "en" else "스캔 완료",
                    "text": f"Found {len(files)} files | {len(files)}개 파일 발견"
                })
                
                time.sleep(0.2)
                status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
                
                if lang == "ko":
                    result = f"📁 **파일 목록** ({len(files)}개)\n\n"
                else:
                    result = f"📁 **File List** ({len(files)} files)\n\n"
                
                for f in sorted(files):
                    # Add icons based on file type
                    if f.endswith('.py'):
                        icon = "🐍"
                    elif f.endswith('.md'):
                        icon = "📝"
                    elif f.endswith(('.txt', '.log')):
                        icon = "📄"
                    elif f.endswith(('.json', '.yaml', '.yml')):
                        icon = "⚙️"
                    else:
                        icon = "📦"
                    
                    result += f"{icon} `{f}`\n"
                
                return result, reasoning_steps
                
            except Exception as e:
                status_container.update(label="❌ Error" if lang == "en" else "❌ 오류", state="error")
                if lang == "ko":
                    return f"❌ 파일 목록 조회 실패: {str(e)}", reasoning_steps
                else:
                    return f"❌ Failed to list files: {str(e)}", reasoning_steps
        
        # Help
        elif any(keyword in user_lower for keyword in ["도움말", "help", "뭐 할 수 있어", "what can you do", "commands", "기능"]):
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Help request detected | 도움말 요청 감지"
            })
            status_container.update(label="📚 Preparing help..." if lang == "en" else "📚 도움말 준비 중...", state="running")
            time.sleep(0.2)
            status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
            
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
                """, reasoning_steps
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
                """, reasoning_steps
        
        # Default response
        else:
            reasoning_steps.append({
                "step": "Intent" if lang == "en" else "의도",
                "text": "Unable to classify intent | 의도 분류 불가"
            })
            status_container.update(label="🤔 Thinking..." if lang == "en" else "🤔 생각 중...", state="running")
            time.sleep(0.3)
            status_container.update(label="✅ Complete!" if lang == "en" else "✅ 완료!", state="complete")
            
            if lang == "ko":
                return f"'{user_input}'에 대한 응답을 생각하고 있어요. '도움말'을 입력하면 제가 할 수 있는 일을 볼 수 있어요! 💡", reasoning_steps
            else:
                return f"I'm thinking about '{user_input}'. Type 'help' to see what I can do! 💡", reasoning_steps
    
    except ValueError as e:
        status_container.update(label="⚠️ Input Error" if lang == "en" else "⚠️ 입력 오류", state="error")
        reasoning_steps.append({
            "step": "Error" if lang == "en" else "오류",
            "text": f"ValueError: {str(e)}"
        })
        if lang == "ko":
            return f"⚠️ 입력 오류: {str(e)}", reasoning_steps
        else:
            return f"⚠️ Input error: {str(e)}", reasoning_steps
    except Exception as e:
        status_container.update(label="❌ Error" if lang == "en" else "❌ 오류", state="error")
        reasoning_steps.append({
            "step": "Error" if lang == "en" else "오류",
            "text": f"Exception: {str(e)}"
        })
        if lang == "ko":
            return f"❌ 처리 중 오류 발생: {str(e)}", reasoning_steps
        else:
            return f"❌ Error occurred: {str(e)}", reasoning_steps

# Chat input
if prompt := st.chat_input("메시지를 입력하세요... | Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process and generate response with reasoning
    with st.chat_message("assistant"):
        # Create status container for real-time updates
        status_container = st.status("🤔 Processing..." if detect_language(prompt) == "en" else "🤔 처리 중...", expanded=True)
        
        response, reasoning = process_user_request_with_reasoning(prompt, status_container)
        
        # Display reasoning in expander if enabled
        if show_reasoning:
            with st.expander("🧠 Thought Process", expanded=False):
                for step in reasoning:
                    st.caption(f"**{step['step']}:** {step['text']}")
        
        # Display response
        st.markdown(response)
    
    # Add assistant response with reasoning
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response,
        "reasoning": reasoning
    })

# Footer
st.divider()
st.caption("🔒 Security-enhanced | 🚀 Powered by MCP | ⚡ Built with Streamlit | 🌐 Korean & English Support | 🧠 Thought Trace Enabled")
