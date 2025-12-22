# 🤖 My Desktop Assistant

MCP (Model Context Protocol) 도구를 활용한 대화형 데스크톱 어시스턴트입니다.

## ✨ 주요 기능

- 📊 **수학 계산**: 덧셈 연산
- 👋 **스마트 인사**: 이름과 시간을 포함한 개인화된 인사
- ⏰ **시간 조회**: 현재 시간 및 날짜 확인
- 📁 **파일 관리**: 파일 읽기, 쓰기, 목록 조회
- 🔐 **보안 강화**: Path Traversal, Command Injection 방어

## 🚀 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Streamlit 앱 실행
```bash
streamlit run app.py
```

### 3. MCP 서버 실행 (별도 터미널)
```bash
python server.py
```

## 💬 사용 예시

- "5 더하기 3" - 수학 계산
- "안녕 나는 현호" - 개인화된 인사
- "지금 몇 시야?" - 시간 확인
- "파일 목록 보여줘" - 파일 목록
- "server.py 파일 읽어줘" - 파일 내용 읽기
- "도움말" - 전체 명령어 보기

## 📁 프로젝트 구조

```
week2/
├── app.py              # Streamlit 챗봇 UI
├── server.py           # MCP 서버 (도구 정의)
├── utils.py            # 유틸리티 함수
├── requirements.txt    # 의존성 목록
└── README.md          # 문서
```

## 🔒 보안 기능

- ✅ 파일 경로 검증 (Path Traversal 방지)
- ✅ 명령어 화이트리스트 (Command Injection 방지)
- ✅ 입력 값 검증 및 제한
- ✅ 리소스 사용량 제한 (파일 크기, 타임아웃 등)

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: FastMCP
- **Language**: Python 3.8+
- **Version Control**: Git + Graphite
