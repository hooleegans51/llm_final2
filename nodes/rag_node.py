"""
RAG 노드 - 벡터DB 검색

[역할]
- 사용자 쿼리로 벡터DB 검색
- 관련 문서 반환
"""

from core.state import AgentState


def rag_node(state: AgentState) -> dict:
    """
    RAG 검색 노드
    
    Input: user_query
    Output: retrieved_docs
    """
    
    query = state["user_query"]
    
    try:
        # 기존 rag 모듈 import
        from rag.retrieval import retrieve_documents
        from rag.embedder import get_embedding
        
        # 쿼리 임베딩 생성
        query_embedding = get_embedding(query)
        
        # 벡터DB 검색
        results = retrieve_documents(
            query_embedding=query_embedding,
            top_k=5
        )
        
        # 결과 포맷팅
        retrieved_docs = []
        for doc in results:
            retrieved_docs.append({
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
                "score": doc.get("score", 0.0)
            })
        
        # 결과가 없으면 빈 리스트
        if not retrieved_docs:
            print(f"[rag_node] 검색 결과 없음: {query}")
        
    except ValueError as e:
        # API 키 오류
        print(f"[rag_node] API 키 오류: {e}")
        raise e
    except Exception as e:
        # 기타 오류 (DB 없음 등) - 빈 결과로 계속 진행
        print(f"[rag_node] RAG 검색 오류: {e}")
        retrieved_docs = []
    
    return {
        "retrieved_docs": retrieved_docs,
        "current_step": "rag_done"
    }