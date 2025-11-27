"""
Google Custom Search API 모듈

[역할]
- Google Custom Search API를 통한 웹 검색
- 모든 검색 도구의 기반 모듈
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Google API 설정
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def is_google_api_available() -> bool:
    """Google API 사용 가능 여부 확인"""
    return bool(GOOGLE_API_KEY and GOOGLE_CSE_ID)


def google_search(
    query: str,
    num_results: int = 5,
    search_type: Optional[str] = None,
    site_search: Optional[str] = None,
    date_restrict: Optional[str] = None,
    language: str = "ko"
) -> List[Dict[str, Any]]:
    """
    Google Custom Search API 호출
    
    Args:
        query: 검색어
        num_results: 결과 수 (최대 10)
        search_type: 검색 타입 ("image" 등, None이면 일반 웹)
        site_search: 특정 사이트 내 검색 (예: "naver.com")
        date_restrict: 날짜 제한 ("d1"=1일, "w1"=1주, "m1"=1개월)
        language: 언어 코드
    
    Returns:
        검색 결과 리스트
    
    Raises:
        ValueError: API 키가 없을 때
        RuntimeError: API 호출 실패 시
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요.\n"
            "발급: https://console.cloud.google.com/ → Custom Search API\n"
            "CSE ID: https://programmablesearchengine.google.com/"
        )
    
    # API 파라미터
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(num_results, 10),  # 최대 10
        "lr": f"lang_{language}",
        "gl": "kr",  # 지역: 한국
    }
    
    if search_type:
        params["searchType"] = search_type
    
    if site_search:
        params["siteSearch"] = site_search
    
    if date_restrict:
        params["dateRestrict"] = date_restrict
    
    try:
        response = requests.get(GOOGLE_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Google Search API 호출 실패: {e}")
    
    # 결과 파싱
    results = []
    items = data.get("items", [])
    
    for item in items:
        result = {
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", ""),
            "displayLink": item.get("displayLink", ""),
        }
        
        # 이미지 검색인 경우 추가 정보
        if search_type == "image":
            image = item.get("image", {})
            result["thumbnail"] = image.get("thumbnailLink", "")
            result["width"] = image.get("width", 0)
            result["height"] = image.get("height", 0)
        
        # 메타데이터
        pagemap = item.get("pagemap", {})
        metatags = pagemap.get("metatags", [{}])[0]
        result["description"] = metatags.get("og:description", result["snippet"])
        
        results.append(result)
    
    return results


def search_shopping(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    쇼핑 검색 (가격 정보)
    
    쿠팡, 네이버 쇼핑 등에서 검색
    """
    # 쇼핑 관련 키워드 추가
    shopping_query = f"{query} 가격 구매"
    
    results = google_search(
        query=shopping_query,
        num_results=num_results,
        site_search=None  # 전체 검색
    )
    
    # 쇼핑 결과 형식으로 변환
    shopping_results = []
    for r in results:
        # 가격 추출 시도 (snippet에서)
        price = extract_price_from_text(r.get("snippet", "") + r.get("title", ""))
        
        shopping_results.append({
            "title": r["title"],
            "price": price,
            "price_text": f"{price:,}원" if price else "가격 정보 없음",
            "link": r["link"],
            "source": r.get("displayLink", ""),
            "snippet": r["snippet"],
            "type": "shopping"
        })
    
    return shopping_results


def search_recipe(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    레시피 검색
    
    만개의레시피, 해먹 등에서 검색
    """
    recipe_query = f"{query} 레시피 만드는법"
    
    results = google_search(
        query=recipe_query,
        num_results=num_results
    )
    
    # 레시피 결과 형식으로 변환
    recipe_results = []
    for r in results:
        recipe_results.append({
            "title": r["title"],
            "content": r["snippet"],
            "link": r["link"],
            "source": r.get("displayLink", ""),
            "type": "recipe"
        })
    
    return recipe_results


def search_nutrition(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    영양/칼로리 정보 검색
    """
    nutrition_query = f"{query} 칼로리 영양정보 100g"
    
    results = google_search(
        query=nutrition_query,
        num_results=num_results
    )
    
    nutrition_results = []
    for r in results:
        # 칼로리 추출 시도
        calorie = extract_calorie_from_text(r.get("snippet", ""))
        
        nutrition_results.append({
            "title": r["title"],
            "calorie": calorie,
            "calorie_text": f"{calorie}kcal" if calorie else "정보 없음",
            "snippet": r["snippet"],
            "link": r["link"],
            "type": "nutrition"
        })
    
    return nutrition_results


def search_health(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    건강/질병 관련 정보 검색
    """
    health_query = f"{query} 식이요법 음식 추천 피해야할 음식"
    
    results = google_search(
        query=health_query,
        num_results=num_results
    )
    
    health_results = []
    for r in results:
        health_results.append({
            "title": r["title"],
            "content": r["snippet"],
            "link": r["link"],
            "source": r.get("displayLink", ""),
            "type": "health"
        })
    
    return health_results


def search_news(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    뉴스 검색 (최근 1주일)
    """
    results = google_search(
        query=query,
        num_results=num_results,
        date_restrict="w1"  # 최근 1주일
    )
    
    news_results = []
    for r in results:
        news_results.append({
            "title": r["title"],
            "snippet": r["snippet"],
            "link": r["link"],
            "source": r.get("displayLink", ""),
            "type": "news"
        })
    
    return news_results


# ============================================================
# 유틸리티 함수
# ============================================================

def extract_price_from_text(text: str) -> int:
    """텍스트에서 가격 추출"""
    import re
    
    # 가격 패턴: 숫자,숫자원 또는 숫자원
    patterns = [
        r'(\d{1,3}(?:,\d{3})+)\s*원',  # 1,000원, 10,000원
        r'(\d+)\s*원',  # 1000원
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                return int(price_str)
            except ValueError:
                continue
    
    return 0


def extract_calorie_from_text(text: str) -> int:
    """텍스트에서 칼로리 추출"""
    import re
    
    # 칼로리 패턴
    patterns = [
        r'(\d+)\s*(?:kcal|Kcal|칼로리|cal)',
        r'칼로리[:\s]*(\d+)',
        r'열량[:\s]*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return 0
