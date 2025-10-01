"""
포맷팅 관련 유틸리티 함수들 (개선됨)
✅ 중복 제거 및 간소화
"""


def format_amount(amount: float, unit: str = "억원") -> str:
    """
    금액을 읽기 쉬운 형식으로 변환

    Examples:
        >>> format_amount(150000000000)
        '1,500.0억원'
    """
    if unit == "억원":
        value = amount / 100_000_000
        return f"{value:,.1f}억원" if value >= 1 else format_amount(amount, "백만원")
    elif unit == "백만원":
        return f"{amount / 10_000_000:,.0f}백만원"
    elif unit == "원":
        return f"{amount:,.0f}원"
    else:
        raise ValueError(f"Unsupported unit: {unit}")


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """비율을 퍼센트 형식으로 변환"""
    return f"{value:.{decimal_places}f}%"


def format_weight_change(change: float) -> str:
    """비중 변화를 부호와 함께 표시"""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}%"


def format_number_with_unit(value: float, unit: str = "") -> str:
    """숫자를 천 단위 구분자와 함께 표시"""
    formatted = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    return f"{formatted}{unit}" if unit else formatted


def format_ticker(ticker: str) -> str:
    """티커를 표준 형식으로 변환 (6자리, 0 패딩)"""
    return ticker.zfill(6)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자르고 접미사 추가"""
    return (
        text if len(text) <= max_length else text[: max_length - len(suffix)] + suffix
    )


def format_stock_name(name: str, max_length: int = 20) -> str:
    """주식명을 표시용으로 포맷팅"""
    return truncate_text(name, max_length)


def format_etf_name(name: str, max_length: int = 30) -> str:
    """ETF명을 표시용으로 포맷팅"""
    return truncate_text(name, max_length)


def parse_amount(amount_str: str) -> float:
    """
    금액 문자열을 숫자로 파싱

    Examples:
        >>> parse_amount("1,234,567")
        1234567.0
        >>> parse_amount("1.5억원")
        150000000.0
    """
    cleaned = amount_str.replace(",", "")

    if "억" in cleaned:
        number = float(cleaned.replace("억원", "").replace("억", ""))
        return number * 100_000_000
    elif "백만" in cleaned:
        number = float(cleaned.replace("백만원", "").replace("백만", ""))
        return number * 10_000_000
    elif "만" in cleaned:
        number = float(cleaned.replace("만원", "").replace("만", ""))
        return number * 10_000
    else:
        return float(cleaned.replace("원", ""))


def format_count(count: int, singular: str = "", plural: str = "개") -> str:
    """개수를 적절한 단위와 함께 표시"""
    unit = singular if count == 1 and singular else plural
    return f"{count:,d}{unit}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈 (0으로 나누기 방지)"""
    return numerator / denominator if denominator != 0 else default


def format_ratio(numerator: float, denominator: float, decimal_places: int = 2) -> str:
    """비율을 계산하고 포맷팅"""
    ratio = safe_divide(numerator, denominator, 0) * 100
    return format_percentage(ratio, decimal_places)


def format_list_summary(items: list, max_items: int = 3, separator: str = ", ") -> str:
    """
    리스트를 요약 형식으로 표시

    Examples:
        >>> format_list_summary(['A', 'B', 'C', 'D', 'E'], 3)
        'A, B, C 외 2개'
    """
    if len(items) <= max_items:
        return separator.join(str(item) for item in items)

    visible = separator.join(str(item) for item in items[:max_items])
    remaining = len(items) - max_items
    return f"{visible} 외 {remaining}개"
