"""
DateRange 값 객체
날짜 범위를 표현하는 불변 값 객체입니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from shared.exceptions import InvalidEntityException
from shared.utils.date_utils import (
    calculate_days_between,
    get_business_days,
    get_date_range,
    to_date_string,
)


@dataclass(frozen=True)
class DateRange:
    """
    날짜 범위 값 객체

    시작일과 종료일을 가지는 불변 객체입니다.

    Attributes:
        start_date: 시작일
        end_date: 종료일

    Examples:
        >>> range = DateRange.create(
        ...     datetime(2024, 1, 1),
        ...     datetime(2024, 1, 31)
        ... )
        >>> range.days_count()
        31
        >>> range.contains(datetime(2024, 1, 15))
        True
    """

    start_date: datetime
    end_date: datetime

    @staticmethod
    def create(start_date: datetime, end_date: datetime) -> "DateRange":
        """
        DateRange 인스턴스를 생성하고 유효성을 검증합니다.

        Args:
            start_date: 시작일
            end_date: 종료일

        Returns:
            검증된 DateRange 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 날짜 범위인 경우
        """
        if not isinstance(start_date, datetime):
            raise InvalidEntityException(
                "DateRange", "start_date must be a datetime object"
            )

        if not isinstance(end_date, datetime):
            raise InvalidEntityException(
                "DateRange", "end_date must be a datetime object"
            )

        if start_date > end_date:
            raise InvalidEntityException(
                "DateRange",
                f"start_date ({to_date_string(start_date)}) must be before or equal to "
                f"end_date ({to_date_string(end_date)})",
            )

        return DateRange(start_date=start_date, end_date=end_date)

    @staticmethod
    def from_days_ago(days: int) -> "DateRange":
        """
        N일 전부터 오늘까지의 DateRange 생성

        Args:
            days: 과거 일수

        Examples:
            >>> range = DateRange.from_days_ago(7)  # 최근 7일
        """
        end_date = datetime.now()
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - days)

        return DateRange.create(start_date, end_date)

    @staticmethod
    def single_day(date: datetime) -> "DateRange":
        """
        하루짜리 DateRange 생성

        Args:
            date: 대상 날짜
        """
        return DateRange.create(date, date)

    def to_dict(self) -> dict:
        """값 객체를 딕셔너리로 변환"""
        return {
            "start_date": to_date_string(self.start_date),
            "end_date": to_date_string(self.end_date),
        }

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        return f"{to_date_string(self.start_date)} ~ {to_date_string(self.end_date)}"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"DateRange(start_date='{to_date_string(self.start_date)}', "
            f"end_date='{to_date_string(self.end_date)}')"
        )

    def days_count(self) -> int:
        """날짜 범위의 총 일수 반환"""
        return calculate_days_between(self.start_date, self.end_date) + 1

    def all_dates(self) -> List[datetime]:
        """범위 내의 모든 날짜 리스트 반환"""
        return get_date_range(self.start_date, self.end_date)

    def business_days(self) -> List[datetime]:
        """범위 내의 영업일 리스트 반환"""
        return get_business_days(self.start_date, self.end_date)

    def business_days_count(self) -> int:
        """범위 내의 영업일 개수 반환"""
        return len(self.business_days())

    def contains(self, date: datetime) -> bool:
        """특정 날짜가 범위 내에 있는지 확인"""
        return self.start_date <= date <= self.end_date

    def overlaps(self, other: "DateRange") -> bool:
        """다른 DateRange와 겹치는지 확인"""
        return self.start_date <= other.end_date and self.end_date >= other.start_date

    def is_single_day(self) -> bool:
        """하루짜리 범위인지 확인"""
        return self.start_date.date() == self.end_date.date()

    def split_by_days(self, chunk_size: int) -> List["DateRange"]:
        """
        날짜 범위를 지정된 일수로 분할

        Args:
            chunk_size: 분할할 일수

        Returns:
            분할된 DateRange 리스트
        """
        ranges = []
        current_start = self.start_date

        while current_start <= self.end_date:
            current_end = min(
                current_start.replace(day=current_start.day + chunk_size - 1),
                self.end_date,
            )
            ranges.append(DateRange.create(current_start, current_end))
            current_start = current_end.replace(day=current_end.day + 1)

        return ranges

    def extend_start(self, days: int) -> "DateRange":
        """
        시작일을 N일 앞으로 확장

        Args:
            days: 확장할 일수
        """
        new_start = self.start_date.replace(day=self.start_date.day - days)
        return DateRange.create(new_start, self.end_date)

    def extend_end(self, days: int) -> "DateRange":
        """
        종료일을 N일 뒤로 확장

        Args:
            days: 확장할 일수
        """
        new_end = self.end_date.replace(day=self.end_date.day + days)
        return DateRange.create(self.start_date, new_end)

    def shrink_start(self, days: int) -> "DateRange":
        """
        시작일을 N일 뒤로 축소

        Args:
            days: 축소할 일수
        """
        new_start = self.start_date.replace(day=self.start_date.day + days)
        if new_start > self.end_date:
            raise InvalidEntityException("DateRange", "Cannot shrink beyond end_date")
        return DateRange.create(new_start, self.end_date)

    def shrink_end(self, days: int) -> "DateRange":
        """
        종료일을 N일 앞으로 축소

        Args:
            days: 축소할 일수
        """
        new_end = self.end_date.replace(day=self.end_date.day - days)
        if new_end < self.start_date:
            raise InvalidEntityException("DateRange", "Cannot shrink before start_date")
        return DateRange.create(self.start_date, new_end)
