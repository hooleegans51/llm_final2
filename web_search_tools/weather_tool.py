"""
날씨 도구

[역할]
- Google Custom Search API를 통한 현재 날씨 조회
- 날씨 기반 음식 추천
"""

from typing import Dict, Any, List
from datetime import datetime

from web_search_tools.google_search import (
    google_search,
    is_google_api_available
)


def get_weather(location: str = "서울") -> Dict[str, Any]:
    """
    날씨 정보 조회 (Google 검색)
    
    Args:
        location: 지역명
    
    Returns:
        날씨 정보
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    query = f"{location} 오늘 날씨 기온"
    results = google_search(query=query, num_results=3)
    
    # 결과에서 온도 추출 시도
    temperature = extract_temperature(results)
    
    # 현재 월 기반 계절 판단
    month = datetime.now().month
    if month in [12, 1, 2]:
        season = "겨울"
    elif month in [3, 4, 5]:
        season = "봄"
    elif month in [6, 7, 8]:
        season = "여름"
    else:
        season = "가을"
    
    return {
        "location": location,
        "temperature": temperature,
        "season": season,
        "search_results": results,
        "type": "weather"
    }


def extract_temperature(results: List[Dict[str, Any]]) -> int:
    """검색 결과에서 온도 추출"""
    import re
    
    for r in results:
        text = r.get("snippet", "") + r.get("title", "")
        
        # 온도 패턴 매칭
        patterns = [
            r'(-?\d+)\s*[°도]',
            r'기온[:\s]*(-?\d+)',
            r'현재[:\s]*(-?\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
    
    # 추출 실패 시 계절 기반 기본값
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 0
    elif month in [3, 4, 5]:
        return 15
    elif month in [6, 7, 8]:
        return 28
    else:
        return 18


def recommend_food_by_weather(location: str = "서울") -> Dict[str, Any]:
    """
    날씨 기반 음식 추천 (Google 검색)
    
    Args:
        location: 지역명
    
    Returns:
        음식 추천 결과
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    # 날씨 정보 가져오기
    weather = get_weather(location)
    temp = weather["temperature"]
    season = weather["season"]
    
    # 날씨/계절 기반 음식 추천 검색
    if temp < 5:
        query = "추운 날 따뜻한 음식 추천"
    elif temp < 15:
        query = "선선한 날 음식 추천"
    elif temp < 25:
        query = "봄 가을 날씨 음식 추천"
    else:
        query = "더운 날 시원한 음식 추천"
    
    results = google_search(query=query, num_results=5)
    
    # 계절별 기본 추천 + 검색 결과
    season_foods = {
        "겨울": ["김치찌개", "부대찌개", "순두부찌개", "감자탕", "설렁탕"],
        "봄": ["비빔밥", "제육볶음", "나물무침", "된장찌개"],
        "여름": ["물냉면", "콩국수", "냉모밀", "화채", "삼계탕"],
        "가을": ["갈비찜", "전골", "버섯요리", "불고기"]
    }
    
    return {
        "weather": weather,
        "recommended_foods": season_foods.get(season, []),
        "search_results": results,
        "query": query,
        "type": "weather_food_recommendation"
    }


def search_seasonal_food(season: str = None) -> Dict[str, Any]:
    """
    계절 음식 검색
    
    Args:
        season: 계절 (봄, 여름, 가을, 겨울) - None이면 현재 계절
    
    Returns:
        계절 음식 정보
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    if season is None:
        month = datetime.now().month
        if month in [12, 1, 2]:
            season = "겨울"
        elif month in [3, 4, 5]:
            season = "봄"
        elif month in [6, 7, 8]:
            season = "여름"
        else:
            season = "가을"
    
    query = f"{season} 제철 음식 추천 레시피"
    results = google_search(query=query, num_results=5)
    
    return {
        "season": season,
        "search_results": results,
        "type": "seasonal_food"
    }
