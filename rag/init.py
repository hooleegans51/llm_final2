"""
rag/
RAG (Retrieval-Augmented Generation) 모듈

사용법:
    from rag.retrieval import RAGRetriever
    from rag.vector_db import build_index
"""

from rag.chunker import Chunk, chunk_document, build_text_splitter
from rag.embedder import embed_texts, embed_single, get_embedding
from rag.vector_db import VectorDB, build_index, upsert_vectors, search_similar
from rag.retrieval import RAGRetriever, retrieve_documents

__all__ = [
    # chunker
    "Chunk",
    "chunk_document", 
    "build_text_splitter",
    # embedder
    "embed_texts",
    "embed_single",
    "get_embedding",
    # vector_db
    "VectorDB",
    "build_index",
    "upsert_vectors",
    "search_similar",
    # retrieval
    "RAGRetriever",
    "retrieve_documents",
]