"""
쇼핑 검색 도구

[역할]
- Google Custom Search API를 통한 상품 가격 검색
- 쇼핑몰 비교
"""

from typing import List, Dict, Any

from web_search_tools.google_search import (
    search_shopping as _google_search_shopping,
    is_google_api_available
)


def search_shopping(query: str) -> List[Dict[str, Any]]:
    """
    쇼핑 검색 실행
    
    Args:
        query: 검색어
    
    Returns:
        상품 리스트 [{title, price, link, source, type}, ...]
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    return _google_search_shopping(query=query, num_results=5)


def get_cheapest(query: str) -> Dict[str, Any]:
    """최저가 상품 반환"""
    results = search_shopping(query)
    if not results:
        return {}
    
    # 가격 정보가 있는 결과만 필터링
    priced_results = [r for r in results if r.get("price", 0) > 0]
    
    if not priced_results:
        return results[0] if results else {}
    
    return min(priced_results, key=lambda x: x.get("price", float("inf")))


def compare_prices(query: str) -> List[Dict[str, Any]]:
    """가격 비교 결과 반환 (가격순 정렬)"""
    results = search_shopping(query)
    return sorted(results, key=lambda x: x.get("price", 0))
