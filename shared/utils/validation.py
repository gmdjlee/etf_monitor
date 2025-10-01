"""
검증 관련 유틸리티 함수들
입력 데이터의 유효성을 검사합니다.
"""

import re
from datetime import datetime
from typing import Any, List, Optional


def is_valid_ticker(ticker: str) -> bool:
    """
    주식/ETF 티커 유효성 검증
    6자리 숫자 형식

    Examples:
        >>> is_valid_ticker('005930')
        True
        >>> is_valid_ticker('ABC123')
        False
    """
    if not ticker:
        return False

    # 6자리 숫자 패턴
    pattern = r"^\d{6}$"
    return bool(re.match(pattern, ticker))


def is_valid_weight(weight: float) -> bool:
    """
    비중 값 유효성 검증 (0 ~ 100)

    Examples:
        >>> is_valid_weight(50.5)
        True
        >>> is_valid_weight(150.0)
        False
    """
    return 0 <= weight <= 100


def is_valid_amount(amount: float) -> bool:
    """
    금액 유효성 검증 (0 이상)

    Examples:
        >>> is_valid_amount(1000000)
        True
        >>> is_valid_amount(-100)
        False
    """
    return amount >= 0


def is_non_empty_string(value: str) -> bool:
    """
    비어있지 않은 문자열인지 검증

    Examples:
        >>> is_non_empty_string('Hello')
        True
        >>> is_non_empty_string('   ')
        False
    """
    return bool(value and value.strip())


def is_valid_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    날짜 범위 유효성 검증 (시작일 <= 종료일)

    Examples:
        >>> is_valid_date_range(datetime(2024, 1, 1), datetime(2024, 12, 31))
        True
        >>> is_valid_date_range(datetime(2024, 12, 31), datetime(2024, 1, 1))
        False
    """
    return start_date <= end_date


def validate_required_fields(
    data: dict, required_fields: List[str]
) -> tuple[bool, Optional[str]]:
    """
    필수 필드 존재 여부 검증

    Returns:
        (유효성, 에러 메시지) 튜플

    Examples:
        >>> validate_required_fields({'name': 'Test', 'age': 30}, ['name', 'age'])
        (True, None)
        >>> validate_required_fields({'name': 'Test'}, ['name', 'age'])
        (False, "Missing required field: 'age'")
    """
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: '{field}'"

        value = data[field]
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Field '{field}' cannot be empty"

    return True, None


def validate_ticker(ticker: str) -> tuple[bool, Optional[str]]:
    """
    티커 검증 및 에러 메시지 반환

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not ticker:
        return False, "Ticker cannot be empty"

    if not is_valid_ticker(ticker):
        return False, f"Invalid ticker format: '{ticker}' (must be 6 digits)"

    return True, None


def validate_weight(weight: float) -> tuple[bool, Optional[str]]:
    """
    비중 검증 및 에러 메시지 반환

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not isinstance(weight, (int, float)):
        return False, f"Weight must be a number, got {type(weight)}"

    if not is_valid_weight(weight):
        return False, f"Weight must be between 0 and 100, got {weight}"

    return True, None


def validate_amount(amount: float) -> tuple[bool, Optional[str]]:
    """
    금액 검증 및 에러 메시지 반환

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not isinstance(amount, (int, float)):
        return False, f"Amount must be a number, got {type(amount)}"

    if not is_valid_amount(amount):
        return False, f"Amount must be non-negative, got {amount}"

    return True, None


def validate_positive_integer(
    value: int, field_name: str = "value"
) -> tuple[bool, Optional[str]]:
    """
    양의 정수 검증

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not isinstance(value, int):
        return False, f"{field_name} must be an integer, got {type(value)}"

    if value <= 0:
        return False, f"{field_name} must be positive, got {value}"

    return True, None


def validate_list_not_empty(
    items: List[Any], field_name: str = "list"
) -> tuple[bool, Optional[str]]:
    """
    리스트가 비어있지 않은지 검증

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not isinstance(items, list):
        return False, f"{field_name} must be a list, got {type(items)}"

    if len(items) == 0:
        return False, f"{field_name} cannot be empty"

    return True, None


def validate_string_length(
    value: str, min_length: int = 0, max_length: int = None, field_name: str = "string"
) -> tuple[bool, Optional[str]]:
    """
    문자열 길이 검증

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if not isinstance(value, str):
        return False, f"{field_name} must be a string, got {type(value)}"

    length = len(value)

    if length < min_length:
        return (
            False,
            f"{field_name} must be at least {min_length} characters, got {length}",
        )

    if max_length and length > max_length:
        return (
            False,
            f"{field_name} must be at most {max_length} characters, got {length}",
        )

    return True, None


def validate_enum_value(
    value: Any, allowed_values: List[Any], field_name: str = "value"
) -> tuple[bool, Optional[str]]:
    """
    값이 허용된 목록에 포함되는지 검증

    Returns:
        (유효성, 에러 메시지) 튜플
    """
    if value not in allowed_values:
        return False, f"{field_name} must be one of {allowed_values}, got '{value}'"

    return True, None


def sanitize_string(value: str) -> str:
    """
    문자열 정제 (공백 제거, 소문자 변환)

    Examples:
        >>> sanitize_string('  Hello World  ')
        'hello world'
    """
    return value.strip().lower() if value else ""


def normalize_ticker(ticker: str) -> str:
    """
    티커를 표준 형식으로 정규화 (6자리, 0 패딩)

    Examples:
        >>> normalize_ticker('5930')
        '005930'
    """
    return ticker.strip().zfill(6) if ticker else ""
