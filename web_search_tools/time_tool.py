"""
시간 도구

[역할]
- 현재 시간 제공
- 시간 기반 식사 추천
"""

from datetime import datetime
from typing import Dict, Any


def get_current_time() -> Dict[str, Any]:
    """현재 시간 정보"""
    now = datetime.now()
    
    hour = now.hour
    if 5 <= hour < 11:
        meal_time = "아침"
    elif 11 <= hour < 14:
        meal_time = "점심"
    elif 14 <= hour < 17:
        meal_time = "간식"
    elif 17 <= hour < 21:
        meal_time = "저녁"
    else:
        meal_time = "야식"
    
    return {
        "datetime": now.isoformat(),
        "hour": hour,
        "minute": now.minute,
        "weekday": ["월", "화", "수", "목", "금", "토", "일"][now.weekday()],
        "meal_time": meal_time
    }


def recommend_by_time() -> Dict[str, Any]:
    """시간대별 음식 추천"""
    time_info = get_current_time()
    meal_time = time_info["meal_time"]
    
    recommendations = {
        "아침": {
            "foods": ["토스트", "계란프라이", "죽", "샌드위치", "우유"],
            "reason": "가벼우면서 영양가 있는 아침식사"
        },
        "점심": {
            "foods": ["비빔밥", "제육볶음", "김치찌개", "백반", "우동"],
            "reason": "든든한 점심식사"
        },
        "간식": {
            "foods": ["과일", "요거트", "견과류", "떡볶이", "샌드위치"],
            "reason": "가벼운 간식"
        },
        "저녁": {
            "foods": ["삼겹살", "찌개", "파스타", "스테이크", "치킨"],
            "reason": "하루 마무리 저녁식사"
        },
        "야식": {
            "foods": ["라면", "치킨", "족발", "보쌈", "떡볶이"],
            "reason": "야식 (건강을 위해 자제 권장)"
        }
    }
    
    rec = recommendations.get(meal_time, recommendations["점심"])
    
    return {
        "time_info": time_info,
        "recommendation": rec
    }


def estimate_cooking_time(recipe_name: str) -> Dict[str, Any]:
    """조리 시간 예상"""
    cooking_times = {
        "라면": 5,
        "볶음밥": 10,
        "김치찌개": 20,
        "된장찌개": 20,
        "스테이크": 25,
        "파스타": 20,
        "삼겹살": 30,
        "불고기": 25,
        "비빔밥": 15,
    }
    
    recipe_lower = recipe_name.lower()
    for name, time in cooking_times.items():
        if name in recipe_lower:
            return {
                "recipe": name,
                "estimated_minutes": time,
                "message": f"{name}은(는) 약 {time}분 정도 소요됩니다."
            }
    
    return {
        "recipe": recipe_name,
        "estimated_minutes": 30,
        "message": f"{recipe_name}은(는) 약 30분 정도 소요될 것으로 예상됩니다."
    }
