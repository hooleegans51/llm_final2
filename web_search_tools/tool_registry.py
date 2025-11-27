"""
도구 레지스트리

[역할]
- 모든 도구 등록 및 관리
- 도구 조회 인터페이스
"""

from typing import Dict, Any, Callable, List

from web_search_tools.shopping_tool import search_shopping, get_cheapest, compare_prices
from web_search_tools.recipe_tools import search_recipe, get_recipe_by_ingredients, get_quick_recipes
from web_search_tools.websearch_tool import web_search, search_news
from web_search_tools.calculator_tool import calculate, sum_prices, calculate_per_serving
from web_search_tools.calorie_tool import get_calorie, calculate_meal_calories, check_diet_compatibility
from web_search_tools.weather_tool import get_weather, recommend_food_by_weather
from web_search_tools.time_tool import get_current_time, recommend_by_time, estimate_cooking_time
from web_search_tools.disease_tool import get_health_guidelines, check_food_compatibility


# 도구 정의
TOOLS = {
    # 쇼핑
    "shopping_search": {
        "name": "shopping_search",
        "description": "상품 가격 검색. 재료 가격, 구매처 정보 제공",
        "function": search_shopping,
        "params": ["query"]
    },
    "get_cheapest": {
        "name": "get_cheapest",
        "description": "최저가 상품 찾기",
        "function": get_cheapest,
        "params": ["query"]
    },
    "compare_prices": {
        "name": "compare_prices",
        "description": "가격 비교",
        "function": compare_prices,
        "params": ["query"]
    },
    
    # 레시피
    "recipe_search": {
        "name": "recipe_search",
        "description": "레시피 검색. 요리법, 재료, 조리 순서 제공",
        "function": search_recipe,
        "params": ["query"]
    },
    "recipe_by_ingredients": {
        "name": "recipe_by_ingredients",
        "description": "재료 기반 레시피 검색",
        "function": get_recipe_by_ingredients,
        "params": ["ingredients"]
    },
    "quick_recipes": {
        "name": "quick_recipes",
        "description": "빠른 요리 레시피",
        "function": get_quick_recipes,
        "params": ["max_time"]
    },
    
    # 웹 검색
    "web_search": {
        "name": "web_search",
        "description": "일반 웹 검색",
        "function": web_search,
        "params": ["query"]
    },
    "news_search": {
        "name": "news_search",
        "description": "뉴스 검색",
        "function": search_news,
        "params": ["query"]
    },
    
    # 계산기
    "calculator": {
        "name": "calculator",
        "description": "수식 계산. 가격 합계 등",
        "function": calculate,
        "params": ["expression"]
    },
    "sum_prices": {
        "name": "sum_prices",
        "description": "가격 합계 계산",
        "function": sum_prices,
        "params": ["prices"]
    },
    
    # 칼로리
    "calorie": {
        "name": "calorie",
        "description": "음식 칼로리 조회",
        "function": get_calorie,
        "params": ["food"]
    },
    "meal_calories": {
        "name": "meal_calories",
        "description": "식사 총 칼로리 계산",
        "function": calculate_meal_calories,
        "params": ["ingredients"]
    },
    "diet_check": {
        "name": "diet_check",
        "description": "다이어트 목표 대비 확인",
        "function": check_diet_compatibility,
        "params": ["calories", "goal"]
    },
    
    # 날씨
    "weather": {
        "name": "weather",
        "description": "현재 날씨 조회",
        "function": get_weather,
        "params": ["location"]
    },
    "weather_food": {
        "name": "weather_food",
        "description": "날씨 기반 음식 추천",
        "function": recommend_food_by_weather,
        "params": ["location"]
    },
    
    # 시간
    "current_time": {
        "name": "current_time",
        "description": "현재 시간 조회",
        "function": get_current_time,
        "params": []
    },
    "time_food": {
        "name": "time_food",
        "description": "시간대별 음식 추천",
        "function": recommend_by_time,
        "params": []
    },
    "cooking_time": {
        "name": "cooking_time",
        "description": "조리 시간 예상",
        "function": estimate_cooking_time,
        "params": ["recipe_name"]
    },
    
    # 건강
    "health_guidelines": {
        "name": "health_guidelines",
        "description": "건강 상태별 식이 가이드",
        "function": get_health_guidelines,
        "params": ["condition"]
    },
    "food_compatibility": {
        "name": "food_compatibility",
        "description": "음식과 건강 상태 호환성 확인",
        "function": check_food_compatibility,
        "params": ["food", "health_conditions"]
    },
}


def get_tool(name: str) -> Dict[str, Any]:
    """도구 정보 조회"""
    return TOOLS.get(name)


def execute_tool(name: str, **kwargs) -> Any:
    """도구 실행"""
    tool = get_tool(name)
    if not tool:
        return {"error": f"도구 '{name}'을(를) 찾을 수 없습니다."}
    
    try:
        return tool["function"](**kwargs)
    except Exception as e:
        return {"error": str(e)}


def list_tools() -> List[Dict[str, str]]:
    """사용 가능한 도구 목록"""
    return [
        {"name": t["name"], "description": t["description"]}
        for t in TOOLS.values()
    ]


def get_tool_descriptions() -> str:
    """도구 설명 문자열 (프롬프트용)"""
    lines = []
    for tool in TOOLS.values():
        lines.append(f"- {tool['name']}: {tool['description']}")
    return "\n".join(lines)
