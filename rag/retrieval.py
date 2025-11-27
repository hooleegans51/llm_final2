"""
rag/retrieval.py
검색 및 답변 생성 (Retrieval) 모듈

벡터 DB에서 검색 + LLM으로 답변 생성
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from rag.embedder import embed_single
from rag.vector_db import VectorDB, DEFAULT_DB_PATH, DEFAULT_COLLECTION_NAME


# ═══════════════════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════════════════

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# OpenAI 클라이언트
_client = None

def get_client():
    """OpenAI 클라이언트 싱글톤"""
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API 키가 설정되지 않았습니다.\n"
                ".env 파일에 OPENAI_API_KEY=sk-... 를 설정하세요."
            )
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {e}")
    return _client


# ═══════════════════════════════════════════════════════════════════════════
# 프롬프트 빌더
# ═══════════════════════════════════════════════════════════════════════════

def build_prompt(query: str, contexts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    RAG 프롬프트 생성
    
    Args:
        query: 사용자 질문
        contexts: 검색된 컨텍스트 리스트
    
    Returns:
        OpenAI messages 형식
    """
    system_prompt = (
        "당신은 요리 레시피 추천 전문가입니다.\n"
        "- 제공된 컨텍스트를 우선적으로 사용하세요.\n"
        "- 확실한 근거가 없으면 '해당 정보를 찾을 수 없습니다'라고 말하세요.\n"
        "- 사용자의 건강 상태나 제약사항을 고려하세요.\n"
    )
    
    # 컨텍스트 포맷팅
    ctx_lines = []
    for idx, c in enumerate(contexts, start=1):
        src = os.path.basename(str(c.get("source", "unknown")))
        cid = c.get("chunk_id", "?")
        snippet = c.get("text", "").strip()
        ctx_lines.append(f"[{idx}] SOURCE={src} | CHUNK={cid}\n{snippet}")
    
    ctx_block = "\n\n".join(ctx_lines)
    
    user_prompt = (
        f"질문: {query}\n\n"
        f"다음은 검색으로 수집한 컨텍스트입니다. 필요한 부분만 사용하세요.\n\n"
        f"{ctx_block}\n\n"
        f"요구사항:\n"
        f"- 근거가 불충분하면 '해당 정보를 찾을 수 없습니다'라고 답변\n"
        f"- 핵심만 한국어로 간결히\n"
        f"- 마지막에 '출처' 섹션을 반드시 포함하되, 아래 포맷을 그대로 사용:\n"
        f"  출처:\n"
        f"  - SOURCE:CHUNK 형태로 나열 (예: recipe.pdf:12, disease.pdf:3)\n"
    )

    return [
        {"role": "system", "content": system_prompt}, 
        {"role": "user", "content": user_prompt}
    ]


# ═══════════════════════════════════════════════════════════════════════════
# LLM 호출
# ═══════════════════════════════════════════════════════════════════════════

def chat_with_openai(messages: List[Dict[str, str]]) -> str:
    """
    OpenAI Chat API 호출
    
    Args:
        messages: 메시지 리스트
    
    Returns:
        LLM 응답 텍스트
    
    Raises:
        ValueError: API 키가 없을 때
        RuntimeError: API 호출 실패 시
    """
    client = get_client()
    
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL, 
            messages=messages
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"OpenAI API 호출 실패: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# RAG Retriever 클래스
# ═══════════════════════════════════════════════════════════════════════════

class RAGRetriever:
    """RAG 검색 및 답변 생성"""
    
    def __init__(
        self, 
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME
    ):
        """
        RAGRetriever 초기화
        
        Args:
            db_path: ChromaDB 경로
            collection_name: 컬렉션 이름
        """
        self.db = VectorDB(db_path=db_path, collection_name=collection_name)
        self.db.get_or_create_collection()
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리로 관련 컨텍스트 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
        
        Returns:
            컨텍스트 리스트
        """
        # 쿼리 임베딩
        query_embedding = embed_single(query)
        
        # 벡터 DB 검색
        results = self.db.search(query_embedding, top_k=top_k)
        
        # 결과 파싱
        contexts = []
        if results['metadatas'] and results['metadatas'][0]:
            for i in range(len(results['ids'][0])):
                context = {
                    "source": results['metadatas'][0][i].get('source', 'unknown'),
                    "chunk_id": results['metadatas'][0][i].get('chunk_id', '?'),
                    "text": results['documents'][0][i]
                }
                contexts.append(context)
        
        return contexts
    
    def query(self, question: str, top_k: int = 5) -> str:
        """
        질문에 대해 RAG 기반 답변 생성
        
        Args:
            question: 사용자 질문
            top_k: 검색할 컨텍스트 수
        
        Returns:
            LLM 생성 답변
        """
        # 1. 관련 컨텍스트 검색
        contexts = self.retrieve(question, top_k=top_k)
        
        if not contexts:
            return "관련 정보를 찾을 수 없습니다."
        
        # 2. 프롬프트 생성
        messages = build_prompt(question, contexts)
        
        # 3. LLM 답변 생성
        answer = chat_with_openai(messages)
        
        return answer
    
    def retrieve_with_score(
        self, 
        query: str, 
        top_k: int = 5
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        컨텍스트 검색 + 유사도 점수 반환
        (LangGraph 노드에서 사용)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
        
        Returns:
            (컨텍스트 리스트, 평균 유사도 점수)
        """
        query_embedding = embed_single(query)
        results = self.db.search(query_embedding, top_k=top_k)
        
        contexts = []
        distances = []
        
        if results['metadatas'] and results['metadatas'][0]:
            for i in range(len(results['ids'][0])):
                context = {
                    "source": results['metadatas'][0][i].get('source', 'unknown'),
                    "chunk_id": results['metadatas'][0][i].get('chunk_id', '?'),
                    "text": results['documents'][0][i]
                }
                contexts.append(context)
            
            # 거리 정보가 있으면 유사도로 변환
            if results.get('distances') and results['distances'][0]:
                distances = results['distances'][0]
        
        # 평균 유사도 계산 (거리가 작을수록 유사)
        avg_score = 0.0
        if distances:
            # ChromaDB L2 거리 → 유사도 변환 (간단 버전)
            avg_score = 1 / (1 + sum(distances) / len(distances))
        
        return contexts, avg_score


# ═══════════════════════════════════════════════════════════════════════════
# 직접 실행 시 (테스트용)
# ═══════════════════════════════════════════════════════════════════════════

# 전역 Retriever 인스턴스 (싱글톤)
_retriever_instance = None

def get_retriever() -> RAGRetriever:
    """RAGRetriever 싱글톤"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance


def retrieve_documents(
    query_embedding: List[float] = None,
    query: str = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    문서 검색 (LangGraph 노드용 래퍼)
    
    Args:
        query_embedding: 쿼리 임베딩 벡터 (둘 중 하나 필수)
        query: 쿼리 텍스트 (둘 중 하나 필수)
        top_k: 반환할 결과 수
    
    Returns:
        검색 결과 리스트 [{content, metadata, score}, ...]
    """
    retriever = get_retriever()
    
    # 쿼리 텍스트로 검색
    if query:
        contexts, avg_score = retriever.retrieve_with_score(query, top_k)
        results = []
        for ctx in contexts:
            results.append({
                "content": ctx.get("text", ""),
                "metadata": {
                    "source": ctx.get("source", ""),
                    "chunk_id": ctx.get("chunk_id", "")
                },
                "score": avg_score
            })
        return results
    
    # 임베딩으로 직접 검색
    if query_embedding:
        raw_results = retriever.db.search(query_embedding, top_k)
        
        results = []
        if raw_results['documents'] and raw_results['documents'][0]:
            for i in range(len(raw_results['ids'][0])):
                # 거리 → 유사도 변환
                distance = raw_results['distances'][0][i] if raw_results.get('distances') else 0
                score = 1 / (1 + distance)
                
                results.append({
                    "content": raw_results['documents'][0][i],
                    "metadata": raw_results['metadatas'][0][i] if raw_results.get('metadatas') else {},
                    "score": score
                })
        return results
    
    # 쿼리 없으면 빈 결과
    return []


if __name__ == "__main__":
    print("=" * 60)
    print("RAG 시스템 - 질의응답 테스트")
    print("=" * 60)
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
    
    retriever = RAGRetriever()
    
    while True:
        question = input("\n질문: ").strip()
        
        if question.lower() in ["quit", "exit", "종료"]:
            print("프로그램을 종료합니다.")
            break
        
        if not question:
            continue
        
        print("\n답변을 생성 중입니다...\n")
        try:
            answer = retriever.query(question)
            print("-" * 60)
            print(answer)
            print("-" * 60)
        except Exception as e:
            print(f"Error: {e}")