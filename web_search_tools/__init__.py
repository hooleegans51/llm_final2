"""
web_search_tools 패키지

Google Custom Search API를 통한 웹 검색 도구 모음
"""

# Google Search 기반 모듈
from web_search_tools.google_search import (
    google_search,
    is_google_api_available,
    search_shopping as google_search_shopping,
    search_recipe as google_search_recipe,
    search_nutrition,
    search_health,
    search_news
)

from web_search_tools.shopping_tool import search_shopping, get_cheapest, compare_prices
from web_search_tools.recipe_tools import search_recipe, get_recipe_by_ingredients
from web_search_tools.websearch_tool import web_search
from web_search_tools.calculator_tool import calculate, sum_prices
from web_search_tools.calorie_tool import get_calorie, calculate_meal_calories
from web_search_tools.weather_tool import get_weather, recommend_food_by_weather
from web_search_tools.time_tool import get_current_time, recommend_by_time
from web_search_tools.disease_tool import get_health_guidelines, check_food_compatibility
from web_search_tools.tool_registry import get_tool, execute_tool, list_tools

__all__ = [
    # Google Search
    "google_search",
    "is_google_api_available",
    # Shopping
    "search_shopping",
    "get_cheapest",
    "compare_prices",
    # Recipe
    "search_recipe",
    "get_recipe_by_ingredients",
    # Web Search
    "web_search",
    # Calculator
    "calculate",
    "sum_prices",
    # Calorie
    "get_calorie",
    "calculate_meal_calories",
    # Weather
    "get_weather",
    "recommend_food_by_weather",
    # Time
    "get_current_time",
    "recommend_by_time",
    # Health
    "get_health_guidelines",
    "check_food_compatibility",
    # Registry
    "get_tool",
    "execute_tool",
    "list_tools",
]
