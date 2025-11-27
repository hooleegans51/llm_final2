# 🥘 Smart Recipe Chat

냉장고 재료 + 건강 상태 기반 요리 레시피 추천 챗봇

**LangGraph + ReAct 패턴 기반**

## 📋 기능

- 🔍 RAG 기반 레시피/요리 지식 검색
- 🛒 재료 가격 검색 (Mock)
- 🍳 레시피 검색 (Mock)
- 💰 예산 관리 및 초과 알림
- 🏥 건강 상태 기반 음식 추천
- 📝 사용자 선호도 메모리

## 🚀 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일 편집하여 OPENAI_API_KEY 설정
```

> ⚠️ **API 키 없이도 실행 가능** - Mock 데이터로 동작합니다.

### 3. 실행

**Gradio UI 모드 (기본)**
```bash
python main.py
```
→ http://localhost:7860 접속

**CLI 모드 (디버깅용)**
```bash
python main.py --cli
```

## 📁 프로젝트 구조

```
llm_final-main/
├── main.py                 # 메인 실행 파일 (Gradio UI)
├── requirements.txt        # 의존성
├── .env.example           # 환경변수 예제
│
├── core/                   # 핵심 모듈
│   ├── state.py           # AgentState 정의
│   ├── graph.py           # LangGraph 그래프 구성
│   ├── prompts.py         # LLM 프롬프트 템플릿
│   └── supervisor.py      # 요청 분류 및 라우팅
│
├── agent/                  # 에이전트
│   ├── main_agent.py      # 메인 에이전트 (1차/2차 LLM)
│   └── modify_agent.py    # 수정 에이전트
│
├── nodes/                  # LangGraph 노드들
│   ├── rag_node.py        # RAG 검색
│   ├── tool_node.py       # 도구 실행
│   ├── memory_writer_node.py  # 메모리 관리
│   ├── reflection_node.py # 메모리 반영
│   ├── rerank_node.py     # 결과 재정렬
│   └── ...
│
├── rag/                    # RAG 모듈
│   ├── embedder.py        # 임베딩
│   ├── vector_db.py       # ChromaDB
│   ├── retrieval.py       # 검색
│   └── chunker.py         # 텍스트 분할
│
├── web_search_tools/       # 검색 도구
│   ├── shopping_tool.py   # 쇼핑 검색
│   ├── recipe_tools.py    # 레시피 검색
│   ├── calorie_tool.py    # 칼로리 조회
│   ├── weather_tool.py    # 날씨 조회
│   ├── disease_tool.py    # 건강 가이드
│   └── ...
│
└── config/                 # 설정 파일
    ├── model_config.yaml
    ├── settings.yaml
    └── tool_config.yaml
```

## 🔄 동작 흐름

```
[사용자 질문]
    ↓
[RAG 노드] - 벡터DB 검색
    ↓
[Supervisor] - 새 요청 vs 수정 요청 판단
    ↓
[Main Agent]
├── 1차 LLM: 초안 + 도구 필요 판단
├── (도구 필요시) Tool 노드 → 검색
└── 2차 LLM: 최종 답변 생성
    ↓
[Memory Writer] - 단기/장기 메모리 저장
    ↓
[Reflection] - 메모리 반영 + 확신도 계산
    ↓
[최종 응답]
```

## 💡 사용 예시

**1. 레시피 추천**
```
"오늘 저녁 뭐 먹을까?"
"스테이크 레시피 알려줘"
```

**2. 장보기 도움**
```
"스테이크 재료 장보기 도와줘"
"김치찌개 재료 가격 얼마야?"
```

**3. 건강 고려**
```
"고혈압인데 저녁 추천해줘"
"다이어트 중인데 저칼로리 요리 알려줘"
```

**4. 수정 요청**
```
"2인분으로 바꿔줘"
"소고기 대신 닭고기로"
```

## ⚙️ 설정

### 예산 초과 알림 (System Interrupt)

예산 초과 시 선택지 제공:
- 계속 진행
- 저렴한 대안 찾기
- 취소

### 메모리

- **단기 메모리**: 세션 내 최근 10턴 유지
- **장기 메모리**: 알레르기, 선호도 등 영구 저장

## 📝 라이선스

MIT License
