"""
rag/embedder.py
임베딩 (Embedding) 모듈

OpenAI API를 사용한 텍스트 임베딩
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════════════════

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSION = 1536  # text-embedding-3-small 차원

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
# 임베딩 함수
# ═══════════════════════════════════════════════════════════════════════════

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    텍스트 리스트를 임베딩 벡터로 변환
    
    Args:
        texts: 임베딩할 텍스트 리스트
    
    Returns:
        임베딩 벡터 리스트 (각 벡터는 float 리스트)
    
    Raises:
        ValueError: API 키가 없을 때
        RuntimeError: API 호출 실패 시
    """
    client = get_client()
    
    try:
        resp = client.embeddings.create(
            model=EMBED_MODEL, 
            input=texts
        )
        return [d.embedding for d in resp.data]
    except Exception as e:
        raise RuntimeError(f"임베딩 생성 실패: {e}")


def embed_single(text: str) -> List[float]:
    """
    단일 텍스트 임베딩
    
    Args:
        text: 임베딩할 텍스트
    
    Returns:
        임베딩 벡터
    """
    return embed_texts([text])[0]


# Alias for compatibility
def get_embedding(text: str) -> List[float]:
    """get_embedding은 embed_single의 별칭"""
    return embed_single(text)