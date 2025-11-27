"""
Summary 노드 - 메모리 압축

[역할]
- 메모리 버퍼가 임계치 초과 시 실행
- LLM으로 요약
- 기존 메모리를 압축된 버전으로 교체
"""

from typing import List, Dict
from core.state import AgentState


# 임계치 설정
BUFFER_THRESHOLD = 20  # 20개 넘으면 압축


def summary_node(state: AgentState) -> dict:
    """
    Summary 노드
    
    Input: short_memory
    Output: short_memory (압축됨)
    """
    
    short_memory = state.get("short_memory", [])
    
    # 임계치 미만이면 스킵
    if len(short_memory) < BUFFER_THRESHOLD:
        return {"current_step": "summary_skipped"}
    
    # 압축 대상: 오래된 절반
    old_memories = short_memory[:len(short_memory)//2]
    recent_memories = short_memory[len(short_memory)//2:]
    
    # 요약 생성
    summary = summarize_memories(old_memories)
    
    # 요약을 첫 번째 항목으로
    compressed = [{
        "type": "summary",
        "content": summary,
        "original_count": len(old_memories)
    }] + recent_memories
    
    return {
        "short_memory": compressed,
        "current_step": "summary_done"
    }


def summarize_memories(memories: List[Dict]) -> str:
    """
    메모리 요약
    
    TODO: LLM으로 요약
    """
    
    # 임시: 키워드 추출
    all_queries = [m.get("query", "") for m in memories]
    all_responses = [m.get("response", "")[:50] for m in memories]
    
    summary_parts = [
        f"이전 대화 요약 ({len(memories)}턴):",
        f"- 주요 질문: {', '.join(all_queries[:3])}...",
        f"- 주요 주제: 요리, 장보기 관련"  # TODO: 실제 분석
    ]
    
    return "\n".join(summary_parts)