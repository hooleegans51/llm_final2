"""
메모리 조율 노드 - 단기/장기 메모리 관리

[역할]
- 데이터 분류 (단기/장기)
- short_memory_node, long_memory_node 호출
- 비동기 처리 (실제론 async)
"""

from core.state import AgentState
from nodes.short_memory_node import short_memory_node
from nodes.long_memory_node import long_memory_node


def memory_writer_node(state: AgentState) -> dict:
    print("[memory_writer] 진입")
    """
    메모리 조율 노드
    
    Input: 전체 State
    Output: short_memory, long_memory 업데이트
    """
    
    # 단기 메모리 업데이트
    short_result = short_memory_node(state)
    
    # 장기 메모리 업데이트 (State 병합 후 전달)
    merged_state = {**state, **short_result}
    long_result = long_memory_node(merged_state)
    
    return {
        "short_memory": short_result.get("short_memory", []),
        "entities": short_result.get("entities", {}),
        "long_memory": long_result.get("long_memory", state.get("long_memory", [])),
        "current_step": "memory_writer_done"
    }