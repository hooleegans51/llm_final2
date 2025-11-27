"""
Smart Recipe Chat - 메인 실행 파일

[구조]
1. LangGraph 에이전트 실행 로직
2. Gradio UI 연동
3. Interrupt 처리 (UI에서 버튼으로)

[실행]
python main.py
"""

import uuid
from typing import List, Tuple, Dict, Any, Optional

import gradio as gr
from langgraph.types import Command

# LangGraph 관련 import
from core.state import create_initial_state, AgentState
from core.graph import compile_graph


# ============================================================
# 🤖 LangGraph 에이전트 실행
# ============================================================

# 전역 앱 인스턴스 (한 번만 컴파일)
AGENT_APP = None

def get_agent_app():
    """에이전트 앱 싱글톤"""
    global AGENT_APP
    if AGENT_APP is None:
        AGENT_APP = compile_graph()
    return AGENT_APP


def run_agent(
    user_message: str,
    memory: Dict[str, Any],
    interrupt_response: Optional[str] = None
) -> Dict[str, Any]:
    """
    LangGraph 에이전트 실행
    
    Args:
        user_message: 사용자 입력
        memory: Gradio 상태 (프로필, 냉장고 등)
        interrupt_response: interrupt 응답 (있으면 재개)
    
    Returns:
        {
            "answer": "응답 텍스트",
            "updated_memory": {...},
            "interrupt": None | {"message": "...", "options": [...]},
            "debug": {...}
        }
    """
    app = get_agent_app()
    session_id = memory.get("session_id", "default")
    config = {"configurable": {"thread_id": session_id}}
    
    # =========================================
    # 1. Interrupt 재개 처리
    # =========================================
    if interrupt_response:
        try:
            result = app.invoke(
                Command(resume=interrupt_response),
                config
            )
            return process_agent_result(result, memory)
        except Exception as e:
            return {
                "answer": f"❌ 재개 중 오류: {str(e)}",
                "updated_memory": memory,
                "interrupt": None,
                "debug": {"error": str(e)}
            }
    
    # =========================================
    # 2. 새 요청 처리
    # =========================================
    
    # 제약조건 구성 (Gradio 메모리에서)
    user_constraints = build_constraints_from_memory(memory)
    
    # 초기 State 생성
    initial_state = create_initial_state(
        user_query=user_message,
        user_id=memory.get("user_name", "user"),
        session_id=session_id,
        user_constraints=user_constraints,
        max_iterations=5
    )
    
    # 에이전트 실행
    try:
        result = app.invoke(initial_state, config)
        return process_agent_result(result, memory)
    except Exception as e:
        return {
            "answer": f"❌ 에이전트 오류: {str(e)}",
            "updated_memory": memory,
            "interrupt": None,
            "debug": {"error": str(e)}
        }


def process_agent_result(result: dict, memory: Dict[str, Any]) -> Dict[str, Any]:
    """에이전트 결과 처리"""
    
    # Interrupt 체크
    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        return {
            "answer": f"⚠️ {interrupt_info.get('message', '확인이 필요합니다.')}",
            "updated_memory": memory,
            "interrupt": interrupt_info,
            "debug": {"state": "interrupted"}
        }
    
    # 정상 완료
    answer = result.get("final_response", "응답을 생성하지 못했습니다.")
    
    # 디버그 정보
    debug_info = {
        "llm_call_count": result.get("llm_call_count", 0),
        "react_steps": len(result.get("react_steps", [])),
        "current_step": result.get("current_step", "unknown"),
        "confidence": result.get("confidence_score", 0)
    }
    
    return {
        "answer": answer,
        "updated_memory": memory,
        "interrupt": None,
        "debug": debug_info
    }


def build_constraints_from_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Gradio 메모리에서 제약조건 추출"""
    constraints = {}
    
    # 건강 상태 → 제한 재료
    health_issues = memory.get("health_issues", [])
    if "고혈압" in health_issues:
        constraints["avoid_high_sodium"] = True
    if "당뇨" in health_issues:
        constraints["avoid_high_sugar"] = True
    if "고지혈증" in health_issues:
        constraints["avoid_high_fat"] = True
    
    # 목표
    goal = memory.get("goal", "")
    if goal == "다이어트":
        constraints["max_calories"] = 500
    elif goal == "벌크업":
        constraints["min_protein"] = 30
    
    # 냉장고 재료
    fridge_items = memory.get("fridge_items", [])
    if fridge_items:
        constraints["available_ingredients"] = fridge_items
    
    # 메모에서 알레르기 추출 (간단 버전)
    notes = memory.get("notes", "")
    if "알레르기" in notes:
        constraints["allergy_note"] = notes
    
    return constraints


# ============================================================
# 🧠 메모리 / 상태 관리
# ============================================================

def init_memory() -> Dict[str, Any]:
    """초기 메모리 생성"""
    return {
        "session_id": str(uuid.uuid4())[:8],
        "user_name": None,
        "goal": None,
        "health_issues": [],
        "notes": "",
        "fridge_items": [],
        "history": [],
        "pending_interrupt": None,  # 🆕 대기 중인 interrupt
    }


def save_profile(
    user_name: str,
    goal: str,
    health_issues: List[str],
    notes: str,
    fridge_text: str,
    memory: Dict[str, Any] | None,
) -> Tuple[Dict[str, Any], str]:
    """프로필 저장"""
    if memory is None or memory == {}:
        memory = init_memory()

    fridge_items = [
        item.strip()
        for item in fridge_text.replace("\n", ",").split(",")
        if item.strip()
    ]

    memory["user_name"] = user_name or "사용자"
    memory["goal"] = goal or "미설정"
    memory["health_issues"] = health_issues
    memory["notes"] = notes
    memory["fridge_items"] = fridge_items

    msg = f"✅ 프로필 저장 완료! (세션: {memory['session_id']})"
    return memory, msg


# ============================================================
# 💬 채팅 핸들러
# ============================================================

def respond(
    user_message: str,
    chat_history: list,
    memory: Dict[str, Any] | None,
) -> Tuple[list, Dict[str, Any], str, gr.update]:
    """
    채팅 전송 핸들러
    
    Returns:
        chat_history, memory, user_input(비움), interrupt_buttons(업데이트)
    """
    if memory is None or memory == {}:
        memory = init_memory()
    
    if not user_message.strip():
        return chat_history, memory, "", gr.update(visible=False)
    
    # 간단한 인사는 빠르게 응답 (API 호출 없이)
    simple_greetings = ["안녕", "hi", "hello", "하이", "헬로", "ㅎㅇ", "반가워"]
    if user_message.strip().lower() in simple_greetings:
        answer = "안녕하세요! 🍳 레시피 추천, 장보기, 칼로리 계산 등 요리 관련 질문을 해주세요!"
        chat_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer}
        ]
        return chat_history, memory, "", gr.update(visible=False)
    
    # 사용자 메시지 추가
    chat_history = chat_history + [{"role": "user", "content": user_message}]
    
    # 에이전트 실행
    agent_result = run_agent(user_message, memory)
    
    answer = agent_result["answer"]
    updated_memory = agent_result.get("updated_memory", memory)
    interrupt_info = agent_result.get("interrupt")
    
    # 디버그 정보 추가 (선택)
    debug = agent_result.get("debug", {})
    if debug.get("llm_call_count"):
        answer += f"\n\n---\n🔍 *LLM 호출: {debug['llm_call_count']}회 | ReAct 스텝: {debug['react_steps']}*"
    
    # 어시스턴트 응답 추가
    chat_history = chat_history + [{"role": "assistant", "content": answer}]
    
    # Interrupt 처리
    if interrupt_info:
        updated_memory["pending_interrupt"] = interrupt_info
        return chat_history, updated_memory, "", gr.update(visible=True)
    else:
        updated_memory["pending_interrupt"] = None
        return chat_history, updated_memory, "", gr.update(visible=False)


def handle_interrupt_choice(
    choice: str,
    chat_history: list,
    memory: Dict[str, Any],
) -> Tuple[list, Dict[str, Any], gr.update]:
    """
    Interrupt 버튼 클릭 핸들러
    """
    if not memory.get("pending_interrupt"):
        return chat_history, memory, gr.update(visible=False)
    
    # 선택 메시지 추가
    chat_history = chat_history + [{"role": "user", "content": f"[선택: {choice}]"}]
    
    # 에이전트 재개
    agent_result = run_agent("", memory, interrupt_response=choice)
    
    answer = agent_result["answer"]
    updated_memory = agent_result.get("updated_memory", memory)
    updated_memory["pending_interrupt"] = None
    
    # 어시스턴트 응답 추가
    chat_history = chat_history + [{"role": "assistant", "content": answer}]
    
    return chat_history, updated_memory, gr.update(visible=False)


def clear_chat(memory: Dict[str, Any]) -> Tuple[list, Dict[str, Any], str, gr.update]:
    """대화 초기화"""
    # 세션 ID 유지, 나머지 초기화
    new_memory = init_memory()
    if memory:
        new_memory["user_name"] = memory.get("user_name")
        new_memory["goal"] = memory.get("goal")
        new_memory["health_issues"] = memory.get("health_issues", [])
        new_memory["notes"] = memory.get("notes", "")
        new_memory["fridge_items"] = memory.get("fridge_items", [])
    
    return [], new_memory, "", gr.update(visible=False)


# ============================================================
# 🎨 Gradio UI
# ============================================================

CUSTOM_CSS = """
#app-title {
    text-align: left;
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 0;
}
#app-subtitle {
    text-align: left;
    font-size: 14px;
    color: #888;
    margin-top: 4px;
    margin-bottom: 20px;
}
.chatbot .message {
    font-size: 14px;
}
#interrupt-buttons {
    background-color: #fff3cd;
    padding: 10px;
    border-radius: 8px;
    margin-top: 10px;
}
"""

def create_ui():
    """Gradio UI 생성"""
    
    # Gradio 버전 호환성 처리
    try:
        # 구 버전 Gradio (4.x 이전)
        demo = gr.Blocks(css=CUSTOM_CSS, theme="soft")
    except TypeError:
        try:
            # 중간 버전 Gradio
            demo = gr.Blocks(theme="soft")
        except TypeError:
            # 최신 버전 Gradio (5.x+) - 파라미터 없이 생성
            demo = gr.Blocks()
    
    with demo:
        gr.Markdown(
            """
<div id="app-title">🥘 Smart Recipe Chat</div>
<div id="app-subtitle">냉장고 재료 + 건강 상태 기반 요리 레시피 추천 챗봇 (LangGraph + ReAct)</div>
            """,
            elem_id="app-header",
        )

        # 전역 상태
        state_memory = gr.State(init_memory())

        with gr.Row():
            # ========== 왼쪽: 프로필 ==========
            with gr.Column(scale=1, min_width=280):
                gr.Markdown("### 👤 사용자 정보")

                user_name = gr.Textbox(label="이름", placeholder="예: 홍길동")
                goal = gr.Radio(
                    ["벌크업", "다이어트", "1일 1식", "유지", "기타"],
                    label="현재 목표",
                )
                health_issues = gr.CheckboxGroup(
                    ["고혈압", "당뇨", "고지혈증", "신장질환", "위장질환", "기타"],
                    label="건강 상태",
                )
                notes = gr.Textbox(
                    label="추가 메모 (선호, 알레르기 등)",
                    placeholder="예: 매운 음식 좋아함, 돼지고기 X, 견과류 알레르기",
                    lines=3,
                )

                gr.Markdown("### 🧊 냉장고 재료")
                fridge_text = gr.Textbox(
                    label="현재 냉장고에 있는 재료",
                    placeholder="예: 돼지고기, 김치, 양파, 계란",
                    lines=5,
                )

                save_btn = gr.Button("💾 프로필 저장", variant="primary")
                profile_msg = gr.Markdown("")

                save_btn.click(
                    fn=save_profile,
                    inputs=[user_name, goal, health_issues, notes, fridge_text, state_memory],
                    outputs=[state_memory, profile_msg],
                )

            # ========== 오른쪽: 채팅 ==========
            with gr.Column(scale=2):
                gr.Markdown("### 💬 레시피 챗봇")

                # Gradio 버전 호환성 처리
                try:
                    chatbot = gr.Chatbot(label="대화", height=450, type="messages")
                except TypeError:
                    chatbot = gr.Chatbot(label="대화", height=450)

                # 🆕 Interrupt 버튼 그룹 (처음엔 숨김)
                with gr.Group(visible=False, elem_id="interrupt-buttons") as interrupt_group:
                    gr.Markdown("⚠️ **선택이 필요합니다:**")
                    with gr.Row():
                        btn_continue = gr.Button("계속 진행", variant="secondary")
                        btn_alternative = gr.Button("저렴한 대안 찾기", variant="primary")
                        btn_cancel = gr.Button("취소", variant="stop")

                with gr.Row():
                    user_input = gr.Textbox(
                        show_label=False,
                        placeholder="질문을 입력하세요. 예: '냉장고 재료로 저녁 메뉴 추천해줘'",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("전송", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("🗑️ 대화 초기화", variant="secondary")

                # ========== 이벤트 연결 ==========
                
                # 전송
                send_btn.click(
                    fn=respond,
                    inputs=[user_input, chatbot, state_memory],
                    outputs=[chatbot, state_memory, user_input, interrupt_group],
                )
                user_input.submit(
                    fn=respond,
                    inputs=[user_input, chatbot, state_memory],
                    outputs=[chatbot, state_memory, user_input, interrupt_group],
                )

                # Interrupt 버튼들
                btn_continue.click(
                    fn=lambda ch, mem: handle_interrupt_choice("계속 진행", ch, mem),
                    inputs=[chatbot, state_memory],
                    outputs=[chatbot, state_memory, interrupt_group],
                )
                btn_alternative.click(
                    fn=lambda ch, mem: handle_interrupt_choice("저렴한 대안 찾기", ch, mem),
                    inputs=[chatbot, state_memory],
                    outputs=[chatbot, state_memory, interrupt_group],
                )
                btn_cancel.click(
                    fn=lambda ch, mem: handle_interrupt_choice("취소", ch, mem),
                    inputs=[chatbot, state_memory],
                    outputs=[chatbot, state_memory, interrupt_group],
                )

                # 초기화
                clear_btn.click(
                    fn=clear_chat,
                    inputs=[state_memory],
                    outputs=[chatbot, state_memory, user_input, interrupt_group],
                )

    return demo


# ============================================================
# 🚀 CLI 실행 (디버깅용)
# ============================================================

def run_cli():
    """CLI 모드 실행 (디버깅용)"""
    print("=== CLI 모드 (디버깅용) ===\n")
    
    app = get_agent_app()
    config = {"configurable": {"thread_id": "cli_session"}}
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 종료합니다.")
            break
        
        initial_state = create_initial_state(
            user_query=user_input,
            user_constraints={"budget": 20000}
        )
        
        result = app.invoke(initial_state, config)
        
        # Interrupt 처리
        while "__interrupt__" in result:
            interrupt_info = result["__interrupt__"][0].value
            print(f"\n⚠️ {interrupt_info['message']}")
            print(f"   옵션: {interrupt_info['options']}")
            
            choice = input(">> 선택: ").strip()
            result = app.invoke(Command(resume=choice), config)
        
        print(f"\n🤖 Assistant: {result.get('final_response', '응답 없음')}")
        
        # 디버그 정보
        print(f"\n   [Debug] LLM 호출: {result.get('llm_call_count', 0)}회")
        print(f"   [Debug] ReAct 스텝: {len(result.get('react_steps', []))}개")


# ============================================================
# 🏁 메인 실행
# ============================================================

if __name__ == "__main__":
    import sys
    
    if "--cli" in sys.argv:
        # CLI 모드
        run_cli()
    else:
        # Gradio UI 모드 (기본)
        demo = create_ui()
        demo.launch(
            server_name="127.0.0.1",  # Windows 호환성
            server_port=7860,
            share=False  # True로 하면 공유 링크 생성
        )