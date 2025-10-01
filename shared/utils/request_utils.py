"""
Request 관련 유틸리티 함수들
Flask request 처리를 위한 공통 함수를 제공합니다.
"""

from datetime import datetime
from typing import Optional

from flask import request

from shared.utils.date_utils import parse_flexible_date


def parse_date_from_request(param_name: str) -> Optional[datetime]:
    """
    Flask request에서 날짜 파라미터를 파싱합니다.

    Args:
        param_name: 쿼리 파라미터 이름

    Returns:
        파싱된 datetime 객체, 없으면 None

    Raises:
        ValueError: 날짜 형식이 유효하지 않은 경우

    Examples:
        >>> # GET /api/etf/123?date=2024-01-01
        >>> date = parse_date_from_request('date')
        >>> print(date)
        2024-01-01 00:00:00
    """
    date_str = request.args.get(param_name)

    if not date_str:
        return None

    date = parse_flexible_date(date_str)
    if not date:
        raise ValueError(f"Invalid date format: {date_str}")

    return date


def get_int_param(param_name: str, default: int = None) -> Optional[int]:
    """
    Flask request에서 정수 파라미터를 가져옵니다.

    Args:
        param_name: 쿼리 파라미터 이름
        default: 기본값

    Returns:
        파라미터 값, 없으면 기본값
    """
    return request.args.get(param_name, default, type=int)


def get_str_param(param_name: str, default: str = None) -> Optional[str]:
    """
    Flask request에서 문자열 파라미터를 가져옵니다.

    Args:
        param_name: 쿼리 파라미터 이름
        default: 기본값

    Returns:
        파라미터 값, 없으면 기본값
    """
    return request.args.get(param_name, default, type=str)


def get_bool_param(param_name: str, default: bool = False) -> bool:
    """
    Flask request에서 boolean 파라미터를 가져옵니다.

    Args:
        param_name: 쿼리 파라미터 이름
        default: 기본값

    Returns:
        파라미터 값, 없으면 기본값
    """
    value = request.args.get(param_name, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    return default
