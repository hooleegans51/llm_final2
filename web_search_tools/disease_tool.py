"""
질병/건강 도구

[역할]
- Google Custom Search API를 통한 건강 상태별 음식 추천
- 금지 식품 안내
"""

from typing import Dict, Any, List

from web_search_tools.google_search import (
    search_health,
    google_search,
    is_google_api_available
)


def get_health_guidelines(condition: str) -> Dict[str, Any]:
    """
    건강 상태별 식이 가이드라인 조회 (Google 검색)
    
    Args:
        condition: 건강 상태 (고혈압, 당뇨 등)
    
    Returns:
        식이 가이드라인
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    results = search_health(query=condition, num_results=5)
    
    # 검색 결과 정리
    avoid_foods = []
    recommend_foods = []
    tips = []
    
    for r in results:
        content = r.get("content", "").lower()
        
        # 피해야 할 음식 키워드 검색
        if "피해야" in content or "금지" in content or "주의" in content:
            avoid_foods.append(r.get("snippet", "")[:100])
        
        # 권장 음식 키워드 검색
        if "권장" in content or "좋은" in content or "추천" in content:
            recommend_foods.append(r.get("snippet", "")[:100])
        
        tips.append(r.get("snippet", "")[:150])
    
    return {
        "condition": condition,
        "search_results": results,
        "tips": tips[:3],
        "type": "health_guidelines"
    }


def search_health_info(condition: str, food: str = None) -> List[Dict[str, Any]]:
    """
    건강 정보 상세 검색
    
    Args:
        condition: 건강 상태
        food: 특정 음식 (선택)
    
    Returns:
        검색 결과 리스트
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    if food:
        query = f"{condition} {food} 먹어도 되나요"
    else:
        query = f"{condition} 식이요법 음식"
    
    return search_health(query=query, num_results=5)


def check_food_compatibility(
    food: str,
    health_conditions: List[str]
) -> Dict[str, Any]:
    """
    음식과 건강 상태 호환성 확인 (Google 검색)
    
    Args:
        food: 음식 이름
        health_conditions: 건강 상태 리스트
    
    Returns:
        호환성 결과
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    all_results = []
    warnings = []
    recommendations = []
    
    for condition in health_conditions:
        # 각 건강 상태에 대해 음식 호환성 검색
        query = f"{condition} {food} 먹어도 되나요 괜찮나요"
        results = google_search(query=query, num_results=3)
        
        for r in results:
            snippet = r.get("snippet", "").lower()
            
            # 부정적 키워드 확인
            negative_keywords = ["피해야", "금지", "안 됩니다", "삼가", "주의", "위험", "나쁜"]
            positive_keywords = ["좋습니다", "권장", "도움", "효과", "추천"]
            
            is_warning = any(kw in snippet for kw in negative_keywords)
            is_positive = any(kw in snippet for kw in positive_keywords)
            
            if is_warning:
                warnings.append({
                    "condition": condition,
                    "food": food,
                    "message": r.get("snippet", "")[:200],
                    "source": r.get("link", "")
                })
            
            if is_positive:
                recommendations.append({
                    "condition": condition,
                    "food": food,
                    "message": r.get("snippet", "")[:200],
                    "source": r.get("link", "")
                })
        
        all_results.extend(results)
    
    return {
        "food": food,
        "health_conditions": health_conditions,
        "is_safe": len(warnings) == 0,
        "warnings": warnings[:3],
        "recommendations": recommendations[:3],
        "search_results": all_results,
        "type": "food_compatibility"
    }


def get_safe_alternatives(
    food: str,
    health_conditions: List[str]
) -> Dict[str, Any]:
    """
    건강 상태를 고려한 대체 음식 제안 (Google 검색)
    
    Args:
        food: 원래 음식
        health_conditions: 건강 상태 리스트
    
    Returns:
        대체 음식 정보
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    conditions_str = " ".join(health_conditions)
    query = f"{conditions_str} {food} 대신 대체 음식 추천"
    
    results = google_search(query=query, num_results=5)
    
    return {
        "original_food": food,
        "health_conditions": health_conditions,
        "alternatives": results,
        "type": "safe_alternatives"
    }
