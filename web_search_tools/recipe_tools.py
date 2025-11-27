"""
레시피 검색 도구

[역할]
- Google Custom Search API를 통한 레시피 검색
- 레시피 정보 파싱
"""

from typing import List, Dict, Any

from web_search_tools.google_search import (
    search_recipe as _google_search_recipe,
    google_search,
    is_google_api_available
)


def search_recipe(query: str) -> List[Dict[str, Any]]:
    """
    레시피 검색 실행
    
    Args:
        query: 검색어 (요리명)
    
    Returns:
        레시피 리스트 [{title, content, link, source, type}, ...]
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    return _google_search_recipe(query=query, num_results=5)


def get_recipe_by_ingredients(ingredients: List[str]) -> List[Dict[str, Any]]:
    """
    재료 기반 레시피 검색
    
    Args:
        ingredients: 재료 리스트
    
    Returns:
        레시피 리스트
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    # 재료들을 조합해서 검색
    ingredients_str = " ".join(ingredients[:5])  # 최대 5개 재료
    query = f"{ingredients_str} 요리 레시피"
    
    return _google_search_recipe(query=query, num_results=5)


def get_quick_recipes(max_time: int = 20) -> List[Dict[str, Any]]:
    """
    빠른 요리 레시피 검색
    
    Args:
        max_time: 최대 조리 시간 (분)
    
    Returns:
        레시피 리스트
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    query = f"{max_time}분 이내 간단 요리 레시피"
    return _google_search_recipe(query=query, num_results=5)
