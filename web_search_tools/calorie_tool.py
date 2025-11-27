"""
칼로리 계산 도구

[역할]
- Google Custom Search API를 통한 음식 칼로리 조회
- 영양소 정보 제공
"""

from typing import Dict, Any, List, Optional

from web_search_tools.google_search import (
    search_nutrition,
    is_google_api_available,
    extract_calorie_from_text
)


def get_calorie(food: str) -> Optional[Dict[str, Any]]:
    """
    음식 칼로리 조회 (Google 검색)
    
    Args:
        food: 음식 이름
    
    Returns:
        칼로리 및 영양 정보 또는 None
    """
    if not is_google_api_available():
        raise ValueError(
            "Google API 키가 설정되지 않았습니다.\n"
            ".env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID를 설정하세요."
        )
    
    results = search_nutrition(query=food, num_results=3)
    
    if not results:
        return None
    
    # 첫 번째 결과에서 칼로리 추출
    best_result = results[0]
    calorie = best_result.get("calorie", 0)
    
    # 칼로리를 못 찾은 경우 다른 결과에서 시도
    if calorie == 0:
        for r in results[1:]:
            if r.get("calorie", 0) > 0:
                calorie = r["calorie"]
                break
    
    return {
        "name": food,
        "calories": calorie,
        "calorie_text": f"{calorie}kcal (100g 기준)" if calorie else "정보 없음",
        "source": best_result.get("link", ""),
        "snippet": best_result.get("snippet", ""),
        "type": "nutrition"
    }


def search_calorie_info(food: str) -> List[Dict[str, Any]]:
    """
    음식 칼로리 정보 검색 (여러 결과)
    
    Args:
        food: 음식 이름
    
    Returns:
        칼로리 정보 리스트
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    return search_nutrition(query=food, num_results=5)


def calculate_meal_calories(ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    식사 총 칼로리 계산
    
    Args:
        ingredients: [{"name": "소고기", "amount": 200}, ...]
    
    Returns:
        총 영양 정보
    """
    if not is_google_api_available():
        raise ValueError("Google API 키가 설정되지 않았습니다.")
    
    total_calories = 0
    details = []
    
    for item in ingredients:
        name = item.get("name", "")
        amount = item.get("amount", 100)  # 그램
        
        info = get_calorie(name)
        if info and info.get("calories", 0) > 0:
            # 100g 기준 칼로리를 실제 양으로 환산
            ratio = amount / 100
            item_calories = round(info["calories"] * ratio, 1)
            
            details.append({
                "name": name,
                "amount": amount,
                "calories": item_calories,
                "source": info.get("source", "")
            })
            
            total_calories += item_calories
        else:
            details.append({
                "name": name,
                "amount": amount,
                "calories": 0,
                "note": "칼로리 정보를 찾을 수 없음"
            })
    
    return {
        "total_calories": round(total_calories, 1),
        "details": details,
        "type": "meal_calories"
    }


def check_diet_compatibility(
    calories: float,
    goal: str = "유지"
) -> Dict[str, Any]:
    """
    다이어트 목표 대비 확인
    
    Args:
        calories: 칼로리
        goal: "다이어트", "벌크업", "유지"
    
    Returns:
        평가 결과
    """
    # 목표별 1끼 권장 칼로리
    goals = {
        "다이어트": {"min": 300, "max": 500, "message": "다이어트에 적합"},
        "벌크업": {"min": 600, "max": 1000, "message": "벌크업에 적합"},
        "유지": {"min": 500, "max": 700, "message": "유지에 적합"},
    }
    
    target = goals.get(goal, goals["유지"])
    
    if calories < target["min"]:
        status = "부족"
        message = f"{goal} 목표 대비 칼로리가 부족합니다. ({target['min']}kcal 이상 권장)"
    elif calories > target["max"]:
        status = "초과"
        message = f"{goal} 목표 대비 칼로리가 높습니다. ({target['max']}kcal 이하 권장)"
    else:
        status = "적합"
        message = target["message"]
    
    return {
        "calories": calories,
        "goal": goal,
        "status": status,
        "message": message,
        "recommended_range": f"{target['min']}-{target['max']}kcal",
        "type": "diet_check"
    }
