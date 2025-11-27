"""
rag/vector_db.py
벡터 DB (ChromaDB) 관리 모듈

PDF 인덱싱 및 ChromaDB 관리
"""

import os
from pathlib import Path
from typing import List, Optional
import chromadb
from pypdf import PdfReader

from rag.chunker import chunk_document, build_text_splitter, Chunk
from rag.embedder import embed_texts


# ═══════════════════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_DB_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "recipes"  # 레시피 추천 AI용
DEFAULT_DATA_DIR = "./rag/data"


# ═══════════════════════════════════════════════════════════════════════════
# PDF 텍스트 추출
# ═══════════════════════════════════════════════════════════════════════════

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    PDF 파일에서 텍스트 추출
    
    Args:
        pdf_path: PDF 파일 경로
    
    Returns:
        추출된 텍스트
    """
    reader = PdfReader(pdf_path)
    text_parts = []
    
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    
    return "\n".join(text_parts)


# ═══════════════════════════════════════════════════════════════════════════
# ChromaDB 관리 클래스
# ═══════════════════════════════════════════════════════════════════════════

class VectorDB:
    """ChromaDB 벡터 데이터베이스 관리"""
    
    def __init__(
        self, 
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME
    ):
        """
        VectorDB 초기화
        
        Args:
            db_path: ChromaDB 저장 경로
            collection_name: 컬렉션 이름
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = None
    
    def get_or_create_collection(self) -> chromadb.Collection:
        """컬렉션 가져오기 또는 생성"""
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )
        return self.collection
    
    def reset_collection(self) -> chromadb.Collection:
        """컬렉션 초기화 (삭제 후 재생성)"""
        try:
            self.client.delete_collection(name=self.collection_name)
        except:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name
        )
        return self.collection
    
    def add_chunks(self, chunks: List[Chunk], batch_size: int = 100):
        """
        청크들을 DB에 추가
        
        Args:
            chunks: 추가할 청크 리스트
            batch_size: 배치 크기
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # 임베딩 생성
            texts = [chunk.text for chunk in batch]
            embeddings = embed_texts(texts)
            
            # ChromaDB에 저장
            ids = [chunk.id for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"  - {i + len(batch)}/{len(chunks)} 완료")
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5
    ) -> dict:
        """
        유사한 청크 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            top_k: 반환할 결과 수
        
        Returns:
            검색 결과 dict
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )


# ═══════════════════════════════════════════════════════════════════════════
# 인덱스 빌드 함수
# ═══════════════════════════════════════════════════════════════════════════

def build_index(
    data_dir: str = DEFAULT_DATA_DIR,
    db_path: str = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    reset: bool = True
):
    """
    data 폴더의 PDF 파일들을 ChromaDB에 인덱싱
    
    Args:
        data_dir: PDF 파일들이 있는 폴더
        db_path: ChromaDB 저장 경로
        collection_name: 컬렉션 이름
        reset: True면 기존 컬렉션 삭제 후 새로 생성
    """
    # 1. PDF 파일 찾기
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: {data_dir} 폴더가 없습니다.")
        return
    
    pdf_files = list(data_path.glob("*.pdf"))
    if not pdf_files:
        print(f"Warning: {data_dir} 폴더에 PDF 파일이 없습니다.")
        return
    
    print(f"발견된 PDF 파일: {len(pdf_files)}개")
    
    # 2. VectorDB 초기화
    db = VectorDB(db_path=db_path, collection_name=collection_name)
    
    if reset:
        db.reset_collection()
    else:
        db.get_or_create_collection()
    
    # 3. 텍스트 분할기 생성
    splitter = build_text_splitter()
    
    # 4. 각 PDF 처리
    all_chunks = []
    for pdf_path in pdf_files:
        print(f"\n처리 중: {pdf_path.name}")
        
        # PDF 텍스트 추출
        try:
            doc_text = extract_text_from_pdf(str(pdf_path))
            print(f"  - 텍스트 추출 완료 ({len(doc_text)} 글자)")
        except Exception as e:
            print(f"  - 텍스트 추출 실패: {e}")
            continue
        
        # 청크로 분할
        chunks = chunk_document(doc_text, str(pdf_path), splitter)
        print(f"  - 청크 생성 완료 ({len(chunks)}개)")
        
        all_chunks.extend(chunks)
    
    if not all_chunks:
        print("\n처리할 청크가 없습니다.")
        return
    
    # 5. DB에 추가
    print(f"\n총 {len(all_chunks)}개 청크 임베딩 중...")
    db.add_chunks(all_chunks)
    
    print(f"\n✓ 인덱싱 완료! {len(all_chunks)}개 청크 저장됨")


# ═══════════════════════════════════════════════════════════════════════════
# 직접 실행 시
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    build_index()


# ═══════════════════════════════════════════════════════════════════════════
# 헬퍼 함수 (노드에서 사용)
# ═══════════════════════════════════════════════════════════════════════════

# 전역 DB 인스턴스 (싱글톤)
_db_instance = None

def get_db_instance() -> VectorDB:
    """VectorDB 싱글톤 인스턴스"""
    global _db_instance
    if _db_instance is None:
        _db_instance = VectorDB()
        _db_instance.get_or_create_collection()
    return _db_instance


def upsert_vectors(
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[dict]
):
    """
    벡터 업서트 (insert or update)
    
    Args:
        ids: 문서 ID 리스트
        embeddings: 임베딩 벡터 리스트
        metadatas: 메타데이터 리스트
    """
    db = get_db_instance()
    try:
        db.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )
    except Exception as e:
        print(f"[vector_db] upsert 오류: {e}")


def search_similar(
    embedding: List[float],
    filter: Optional[dict] = None,
    top_k: int = 5
) -> List[dict]:
    """
    유사한 벡터 검색
    
    Args:
        embedding: 쿼리 임베딩
        filter: 필터 조건 (예: {"user_id": "user1"})
        top_k: 반환할 결과 수
    
    Returns:
        검색 결과 리스트
    """
    db = get_db_instance()
    
    try:
        query_params = {
            "query_embeddings": [embedding],
            "n_results": top_k
        }
        
        if filter:
            query_params["where"] = filter
        
        results = db.collection.query(**query_params)
        
        # 결과 파싱
        parsed = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                item = {
                    "id": results['ids'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "document": results['documents'][0][i] if results['documents'] else "",
                    "score": 1 / (1 + results['distances'][0][i]) if results.get('distances') else 0
                }
                parsed.append(item)
        
        return parsed
    except Exception as e:
        print(f"[vector_db] search 오류: {e}")
        return []


def delete_vectors(ids: List[str]):
    """벡터 삭제"""
    db = get_db_instance()
    try:
        db.collection.delete(ids=ids)
    except Exception as e:
        print(f"[vector_db] delete 오류: {e}")