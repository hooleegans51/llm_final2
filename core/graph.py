"""
LangGraph 그래프 구성

[실행 방식]
- invoke: 최종 결과만 반환 (return)
- stream: 각 노드마다 결과 반환 (yield)

[Interrupt 방식]
1. interrupt_before: compile 시 설정 → update_state() → invoke(None, config)
2. interrupt(): 노드 내부에서 호출 → Command(resume=...) 로 재개

[그래프 구조]
START → rag → supervisor ─┬─→ main_agent ↔ tool → memory_writer → reflection → END
                          │
                          └─→ modify_agent → memory_writer → reflection → END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import AgentState

# 노드 함수 import
from nodes.rag_node import rag_node
from nodes.tool_node import tool_node
from nodes.memory_writer_node import memory_writer_node
from nodes.reflection_node import reflection_node
from nodes.rerank_node import rerank_node
from agent.main_agent import main_agent_node
from agent.modify_agent import modify_agent_node
from core.supervisor import supervisor_node, route_after_supervisor


# ============================================================
# 라우팅 함수
# ============================================================

def route_after_main_agent(state: AgentState) -> str:
    """
    main_agent 후 라우팅
    
    - cancelled/complete → memory_writer (저장 후 종료)
    - 도구 필요 → tool
    - 그 외 → memory_writer
    """
    step = state.get("current_step", "")
    
    # 종료 조건
    if step in ["cancelled", "complete", "max_iteration_reached", "2nd_llm_done"]:
        return "memory_writer"
    
    # 도구 사용
    if state.get("need_web_search") and not state.get("search_results"):
        return "tool"
    
    # 도구 결과 받고 다시 main_agent로
    if step == "tool_done":
        return "main_agent"
    
    return "memory_writer"


def route_after_tool(state: AgentState) -> str:
    """tool 실행 후 → main_agent로 돌아가서 2차 LLM"""
    return "main_agent"


def route_after_reflection(state: AgentState) -> str:
    """reflection 후 라우팅"""
    if state.get("need_rerank"):
        return "rerank"
    return END


# ============================================================
# 그래프 빌드
# ============================================================

def build_graph() -> StateGraph:
    """그래프 구조 정의"""
    
    builder = StateGraph(AgentState)
    
    # ========================================
    # 노드 추가
    # ========================================
    builder.add_node("rag", rag_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("main_agent", main_agent_node)
    builder.add_node("modify_agent", modify_agent_node)
    builder.add_node("tool", tool_node)
    builder.add_node("memory_writer", memory_writer_node)
    builder.add_node("reflection", reflection_node)
    builder.add_node("rerank", rerank_node)
    
    # ========================================
    # 엣지 연결
    # ========================================
    
    # START → rag → supervisor
    builder.add_edge(START, "rag")
    builder.add_edge("rag", "supervisor")
    
    # supervisor → main_agent OR modify_agent
    builder.add_conditional_edges("supervisor", route_after_supervisor)
    
    # main_agent 후 분기 (tool / memory_writer)
    builder.add_conditional_edges("main_agent", route_after_main_agent)
    
    # modify_agent → memory_writer (수정 후 저장)
    builder.add_edge("modify_agent", "memory_writer")
    
    # tool 후 → main_agent (2차 LLM 위해)
    builder.add_edge("tool", "main_agent")
    
    # 완료 후 흐름
    builder.add_edge("memory_writer", "reflection")
    builder.add_conditional_edges("reflection", route_after_reflection)
    builder.add_edge("rerank", "main_agent")
    
    return builder


# ============================================================
# 컴파일
# ============================================================

def compile_graph(interrupt_before_nodes: list = None):
    """
    그래프 컴파일
    
    Args:
        interrupt_before_nodes: interrupt_before 설정할 노드 리스트
                               예: ["main_agent"] → main_agent 진입 전 멈춤
    """
    builder = build_graph()
    memory = MemorySaver()
    
    compile_kwargs = {"checkpointer": memory}
    
    if interrupt_before_nodes:
        compile_kwargs["interrupt_before"] = interrupt_before_nodes
    
    return builder.compile(**compile_kwargs)


# ============================================================
# 실행 함수
# ============================================================

def run_with_invoke(app, initial_state: dict, config: dict):
    """
    invoke로 실행 (최종 결과만 반환)
    """
    return app.invoke(initial_state, config)


def run_with_stream(app, initial_state: dict, config: dict):
    """
    stream으로 실행 (각 노드 결과 실시간 확인)
    
    사용 예:
        for node_name, value in run_with_stream(app, state, config):
            print(f"[{node_name}] {value}")
    """
    for event in app.stream(initial_state, config):
        for node_name, value in event.items():
            print(f"[{node_name} 실행됨]")
            print(f"  → 업데이트 내용: {list(value.keys())}")
            print("---")
            yield node_name, value