"""
날짜 관련 유틸리티 함수들
날짜 변환, 검증, 범위 계산 등을 처리합니다.
"""

from datetime import datetime, timedelta
from typing import List, Optional


def to_date_string(date: datetime, format: str = "%Y-%m-%d") -> str:
    """datetime을 문자열로 변환"""
    return date.strftime(format)


def from_date_string(date_str: str, format: str = "%Y-%m-%d") -> datetime:
    """문자열을 datetime으로 변환"""
    try:
        return datetime.strptime(date_str, format)
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date_str}': {e}")


def to_krx_format(date: datetime) -> str:
    """KRX API 형식으로 변환 (YYYYMMDD)"""
    return date.strftime("%Y%m%d")


def from_krx_format(date_str: str) -> datetime:
    """KRX API 형식에서 변환 (YYYYMMDD)"""
    return from_date_string(date_str, "%Y%m%d")


def get_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """시작일부터 종료일까지의 모든 날짜 리스트 생성"""
    if start_date > end_date:
        raise ValueError(f"Start date {start_date} must be before end date {end_date}")

    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def get_business_days(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    시작일부터 종료일까지의 영업일 리스트 생성
    주말(토,일)을 제외합니다.
    """
    all_dates = get_date_range(start_date, end_date)
    # 월요일=0, 일요일=6
    return [d for d in all_dates if d.weekday() < 5]


def days_ago(days: int) -> datetime:
    """N일 전 날짜 반환"""
    return datetime.now() - timedelta(days=days)


def is_valid_date_string(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """날짜 문자열이 유효한지 검증"""
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def get_latest_business_day() -> datetime:
    """가장 최근 영업일 반환 (오늘이 주말이면 금요일)"""
    today = datetime.now()

    # 토요일이면 금요일로
    if today.weekday() == 5:
        return today - timedelta(days=1)
    # 일요일이면 금요일로
    elif today.weekday() == 6:
        return today - timedelta(days=2)

    return today


def format_period(start_date: datetime, end_date: datetime) -> str:
    """날짜 범위를 읽기 쉬운 형식으로 변환"""
    return f"{to_date_string(start_date)} ~ {to_date_string(end_date)}"


def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """두 날짜 사이의 일수 계산"""
    return (end_date - start_date).days


def get_n_days_before(date: datetime, n: int) -> datetime:
    """특정 날짜로부터 N일 전 날짜 반환"""
    return date - timedelta(days=n)


def get_n_days_after(date: datetime, n: int) -> datetime:
    """특정 날짜로부터 N일 후 날짜 반환"""
    return date + timedelta(days=n)


def parse_flexible_date(date_input: str) -> Optional[datetime]:
    """
    다양한 형식의 날짜 문자열을 파싱
    지원 형식: YYYY-MM-DD, YYYYMMDD, YYYY/MM/DD
    """
    formats = ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"]

    for fmt in formats:
        try:
            return datetime.strptime(date_input, fmt)
        except ValueError:
            continue

    return None


def is_same_date(date1: datetime, date2: datetime) -> bool:
    """두 datetime이 같은 날짜인지 확인 (시간 무시)"""
    return date1.date() == date2.date()


def get_month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """특정 년월의 시작일과 종료일 반환"""
    start = datetime(year, month, 1)

    # 다음 달 1일에서 하루 빼기
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(days=1)

    return start, end
