"""
rag/chunker.py
텍스트 분할 (Chunking) 모듈

PDF/텍스트를 청크 단위로 분할
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ═══════════════════════════════════════════════════════════════════════════
# Chunk 데이터 클래스
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Chunk:
    """청크 단위 데이터"""
    id: str
    text: str
    metadata: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
# Text Splitter
# ═══════════════════════════════════════════════════════════════════════════

def build_text_splitter(
    chunk_size: int = 700, 
    chunk_overlap: int = 120
) -> RecursiveCharacterTextSplitter:
    """
    텍스트 분할기 생성
    
    Args:
        chunk_size: 청크 최대 길이 (기본 700)
        chunk_overlap: 청크 간 중복 (기본 120)
    
    Returns:
        RecursiveCharacterTextSplitter 인스턴스
    """
    return RecursiveCharacterTextSplitter(
        separators=["\n\n", ". ", "! ", "? ", "\n", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )


def chunk_document(
    doc_text: str, 
    source: str, 
    splitter: RecursiveCharacterTextSplitter = None
) -> List[Chunk]:
    """
    문서를 청크 단위로 분할
    
    Args:
        doc_text: 원본 문서 텍스트
        source: 문서 출처 (파일명 등)
        splitter: 텍스트 분할기 (없으면 기본값 사용)
    
    Returns:
        Chunk 리스트
    """
    if splitter is None:
        splitter = build_text_splitter()

    pieces = splitter.split_text(doc_text)
    chunks = []
    
    for i, piece in enumerate(pieces):
        meta = {
            "source": source,
            "chunk_id": i,
        }
        chunks.append(
            Chunk(
                id=f"{os.path.basename(source)}::chunk_{i}",
                text=piece,
                metadata=meta,
            )
        )
    
    return chunks