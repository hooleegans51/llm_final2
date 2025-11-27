"""
도구 스펙 정의

OpenAI Function Calling 형식의 도구 스펙
"""

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "shopping_search",
            "description": "상품 가격 검색. 재료 가격, 구매처 정보를 제공합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 상품명"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recipe_search",
            "description": "레시피 검색. 요리법, 재료, 조리 순서를 제공합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 요리명"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "일반 웹 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "수식 계산. 가격 합계 등에 사용",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "계산식 (예: 15000 + 5000 + 3000)"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calorie",
            "description": "음식 칼로리 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "food": {
                        "type": "string",
                        "description": "음식 이름"
                    }
                },
                "required": ["food"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "현재 날씨 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "지역명 (기본: 서울)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "health_guidelines",
            "description": "건강 상태별 식이 가이드라인 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "건강 상태 (예: 고혈압, 당뇨)"
                    }
                },
                "required": ["condition"]
            }
        }
    },
]


def get_tool_specs():
    """OpenAI 호환 도구 스펙 반환"""
    return TOOL_SPECS
