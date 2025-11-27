"""
계산기 도구

[역할]
- 가격 계산
- 영양소 계산
"""

from typing import Union
import re


def calculate(expression: str) -> Union[float, str]:
    """
    수식 계산
    
    Args:
        expression: 계산식 (예: "15000 + 5000 + 3000")
    
    Returns:
        계산 결과 또는 에러 메시지
    """
    try:
        # 안전한 문자만 허용 (숫자, 연산자, 괄호, 공백)
        safe_chars = set("0123456789+-*/().% ")
        if not all(c in safe_chars for c in expression):
            return "허용되지 않는 문자가 포함되어 있습니다."
        
        # 계산 실행
        result = eval(expression)
        return float(result)
    except Exception as e:
        return f"계산 오류: {str(e)}"


def sum_prices(prices: list) -> int:
    """가격 합계 계산"""
    total = 0
    for p in prices:
        if isinstance(p, (int, float)):
            total += p
        elif isinstance(p, str):
            # 문자열에서 숫자 추출
            numbers = re.findall(r'\d+', p.replace(",", ""))
            if numbers:
                total += int("".join(numbers))
    return int(total)


def calculate_per_serving(total: float, servings: int) -> float:
    """1인분 가격 계산"""
    if servings <= 0:
        return 0
    return round(total / servings, 0)


def calculate_discount(original: float, discount_rate: float) -> dict:
    """할인가 계산"""
    discount_amount = original * (discount_rate / 100)
    final_price = original - discount_amount
    return {
        "original": original,
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "final_price": final_price
    }
