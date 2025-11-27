"""
일반 웹 검색 도구

[역할]
- Google Custom Search API를 통한 일반 웹 검색
- 뉴스, 이미지 검색 지원
"""

from typing import List, Dict, Any

from web_search_tools.google_search import (
    google_search,
    search_news as _search_news,
    is_google_api_available
)


def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    웹 검색 실행
    
    Args:
        query: 검색어
        num_results: 반환할 결과 수
    
    Returns:
        검색 결과 리스트 [{title, snippet, link}, ...]
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    results = google_search(query=query, num_results=num_results)
    
    return [
        {
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "link": r.get("link", ""),
            "type": "web"
        }
        for r in results
    ]


def search_news(query: str, num_results: int = 3) -> List[Dict[str, Any]]:
    """뉴스 검색 (최근 1주일)"""
    return _search_news(query=query, num_results=num_results)


def search_images(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """이미지 검색"""
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    results = google_search(
        query=query,
        num_results=num_results,
        search_type="image"
    )
    
    return [
        {
            "title": r.get("title", ""),
            "thumbnail": r.get("thumbnail", ""),
            "link": r.get("link", ""),
            "type": "image"
        }
        for r in results
    ]

