"""
LangGraph 그래프 구성 (수정본)
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import AgentState

from nodes.rag_node import rag_node
from nodes.tool_node import tool_node
from agent.main_agent import main_agent_node
from agent.modify_agent import modify_agent_node
from core.supervisor import supervisor_node, route_after_supervisor


def route_after_main_agent(state: AgentState) -> str:
    print(f"[route] main_agent 후 - final: {bool(state.get('final_response'))}")
    
    if state.get("final_response"):
        return END
    
    if state.get("need_web_search") and not state.get("search_results"):
        return "tool"
    
    return END


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    
    builder.add_node("rag", rag_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("main_agent", main_agent_node)
    builder.add_node("modify_agent", modify_agent_node)
    builder.add_node("tool", tool_node)
    
    builder.add_edge(START, "rag")
    builder.add_edge("rag", "supervisor")
    builder.add_conditional_edges("supervisor", route_after_supervisor)
    builder.add_conditional_edges("main_agent", route_after_main_agent)
    builder.add_edge("modify_agent", END)
    builder.add_edge("tool", "main_agent")
    
    return builder


def compile_graph(interrupt_before_nodes: list = None):
    builder = build_graph()
    memory = MemorySaver()
    
    compile_kwargs = {"checkpointer": memory}
    
    if interrupt_before_nodes:
        compile_kwargs["interrupt_before"] = interrupt_before_nodes
    
    return builder.compile(**compile_kwargs)