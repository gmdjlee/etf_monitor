"""
포맷팅 관련 유틸리티 함수들
금액, 비율, 숫자 등의 표시 형식을 처리합니다.
"""


def format_amount(amount: float, unit: str = "억원") -> str:
    """
    금액을 읽기 쉬운 형식으로 변환

    Args:
        amount: 원화 금액 (원 단위)
        unit: 표시 단위 ('억원', '백만원', '원')

    Returns:
        포맷된 금액 문자열

    Examples:
        >>> format_amount(150000000000)
        '1,500.0억원'
        >>> format_amount(150000000000, '백만원')
        '150,000백만원'
    """
    if unit == "억원":
        value = amount / 100_000_000
        if value >= 1:
            return f"{value:,.1f}억원"
        else:
            # 1억 미만은 백만원 단위로
            return format_amount(amount, "백만원")

    elif unit == "백만원":
        value = amount / 10_000_000
        return f"{value:,.0f}백만원"

    elif unit == "원":
        return f"{amount:,.0f}원"

    else:
        raise ValueError(f"Unsupported unit: {unit}")


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    비율을 퍼센트 형식으로 변환

    Examples:
        >>> format_percentage(12.3456)
        '12.35%'
        >>> format_percentage(12.3456, 1)
        '12.3%'
    """
    return f"{value:.{decimal_places}f}%"


def format_weight_change(change: float) -> str:
    """
    비중 변화를 부호와 함께 표시

    Examples:
        >>> format_weight_change(1.23)
        '+1.23%'
        >>> format_weight_change(-0.45)
        '-0.45%'
    """
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}%"


def format_number_with_unit(value: float, unit: str = "") -> str:
    """
    숫자를 천 단위 구분자와 함께 표시

    Examples:
        >>> format_number_with_unit(1234567)
        '1,234,567'
        >>> format_number_with_unit(123, '개')
        '123개'
    """
    formatted = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    return f"{formatted}{unit}" if unit else formatted


def format_ticker(ticker: str) -> str:
    """
    티커를 표준 형식으로 변환 (6자리, 0 패딩)

    Examples:
        >>> format_ticker('005930')
        '005930'
        >>> format_ticker('5930')
        '005930'
    """
    return ticker.zfill(6)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    텍스트를 지정된 길이로 자르고 접미사 추가

    Examples:
        >>> truncate_text("TIGER 미국나스닥100", 10)
        'TIGER 미국...'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_stock_name(name: str, max_length: int = 20) -> str:
    """
    주식명을 표시용으로 포맷팅

    Examples:
        >>> format_stock_name("삼성전자")
        '삼성전자'
        >>> format_stock_name("매우긴이름의주식회사입니다", 10)
        '매우긴이름의주...'
    """
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
    # 쉼표 제거
    cleaned = amount_str.replace(",", "")

    # 단위 처리
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
    """
    개수를 적절한 단위와 함께 표시

    Examples:
        >>> format_count(5)
        '5개'
        >>> format_count(1, '종목', '종목')
        '1종목'
    """
    unit = singular if count == 1 and singular else plural
    return f"{count:,d}{unit}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    안전한 나눗셈 (0으로 나누기 방지)

    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, -1.0)
        -1.0
    """
    return numerator / denominator if denominator != 0 else default


def format_ratio(numerator: float, denominator: float, decimal_places: int = 2) -> str:
    """
    비율을 계산하고 포맷팅

    Examples:
        >>> format_ratio(1, 4)
        '25.00%'
    """
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
