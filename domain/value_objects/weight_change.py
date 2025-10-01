"""
WeightChange 값 객체
비중 변화를 표현하는 불변 값 객체입니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from shared.exceptions import InvalidEntityException


class ChangeStatus(Enum):
    """비중 변화 상태"""

    NEW = "신규"  # 새로 추가된 종목
    REMOVED = "제외"  # 제외된 종목
    INCREASED = "비중 증가"  # 비중 증가
    DECREASED = "비중 감소"  # 비중 감소
    UNCHANGED = "유지"  # 비중 유지


@dataclass(frozen=True)
class WeightChange:
    """
    비중 변화 값 객체

    이전 비중과 현재 비중의 변화를 표현합니다.

    Attributes:
        previous_weight: 이전 비중 (%)
        current_weight: 현재 비중 (%)
        change_amount: 변화량 (%)
        status: 변화 상태

    Examples:
        >>> change = WeightChange.create(10.0, 15.0)
        >>> change.change_amount
        5.0
        >>> change.status
        ChangeStatus.INCREASED
        >>> change.is_significant(threshold=1.0)
        True
    """

    previous_weight: float
    current_weight: float
    change_amount: float
    status: ChangeStatus

    @staticmethod
    def create(
        previous_weight: float, current_weight: float, threshold: float = 0.01
    ) -> "WeightChange":
        """
        WeightChange 인스턴스를 생성하고 상태를 결정합니다.

        Args:
            previous_weight: 이전 비중 (0이면 신규)
            current_weight: 현재 비중 (0이면 제외)
            threshold: 유의미한 변화로 간주할 최소 변화량

        Returns:
            WeightChange 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 비중 값인 경우
        """
        # 비중 검증
        if previous_weight < 0 or current_weight < 0:
            raise InvalidEntityException(
                "WeightChange",
                f"Weights must be non-negative: previous={previous_weight}, current={current_weight}",
            )

        if previous_weight > 100 or current_weight > 100:
            raise InvalidEntityException(
                "WeightChange",
                f"Weights must be <= 100: previous={previous_weight}, current={current_weight}",
            )

        # 변화량 계산
        change_amount = round(current_weight - previous_weight, 4)

        # 상태 결정
        status = WeightChange._determine_status(
            previous_weight, current_weight, change_amount, threshold
        )

        return WeightChange(
            previous_weight=round(previous_weight, 4),
            current_weight=round(current_weight, 4),
            change_amount=change_amount,
            status=status,
        )

    @staticmethod
    def create_new(current_weight: float) -> "WeightChange":
        """신규 추가된 종목의 WeightChange 생성"""
        return WeightChange.create(0.0, current_weight)

    @staticmethod
    def create_removed(previous_weight: float) -> "WeightChange":
        """제외된 종목의 WeightChange 생성"""
        return WeightChange.create(previous_weight, 0.0)

    @staticmethod
    def _determine_status(
        previous: float, current: float, change: float, threshold: float
    ) -> ChangeStatus:
        """비중 변화 상태 결정"""
        # 신규 추가
        if previous == 0.0 and current > 0.0:
            return ChangeStatus.NEW

        # 제외
        if previous > 0.0 and current == 0.0:
            return ChangeStatus.REMOVED

        # 변화량이 threshold 미만이면 유지로 간주
        if abs(change) < threshold:
            return ChangeStatus.UNCHANGED

        # 비중 증가
        if change > 0:
            return ChangeStatus.INCREASED

        # 비중 감소
        return ChangeStatus.DECREASED

    def to_dict(self) -> dict:
        """값 객체를 딕셔너리로 변환"""
        return {
            "previous_weight": self.previous_weight,
            "current_weight": self.current_weight,
            "change_amount": self.change_amount,
            "status": self.status.value,
        }

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        sign = "+" if self.change_amount > 0 else ""
        return f"{self.status.value}: {sign}{self.change_amount}%"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"WeightChange(previous={self.previous_weight}%, "
            f"current={self.current_weight}%, "
            f"change={self.change_amount}%, "
            f"status={self.status.value})"
        )

    def is_new(self) -> bool:
        """신규 추가된 종목인지 확인"""
        return self.status == ChangeStatus.NEW

    def is_removed(self) -> bool:
        """제외된 종목인지 확인"""
        return self.status == ChangeStatus.REMOVED

    def is_increased(self) -> bool:
        """비중이 증가했는지 확인"""
        return self.status == ChangeStatus.INCREASED

    def is_decreased(self) -> bool:
        """비중이 감소했는지 확인"""
        return self.status == ChangeStatus.DECREASED

    def is_unchanged(self) -> bool:
        """비중이 유지되었는지 확인"""
        return self.status == ChangeStatus.UNCHANGED

    def is_significant(self, threshold: float = 0.5) -> bool:
        """
        유의미한 변화인지 확인

        Args:
            threshold: 유의미한 변화로 간주할 최소 변화량 (기본값: 0.5%)
        """
        return abs(self.change_amount) >= threshold

    def has_changed(self) -> bool:
        """비중에 변화가 있는지 확인 (신규, 제외, 증가, 감소)"""
        return self.status != ChangeStatus.UNCHANGED

    def change_percentage(self) -> Optional[float]:
        """
        이전 비중 대비 변화율 계산 (%)

        Returns:
            변화율 (이전 비중이 0이면 None)

        Examples:
            >>> change = WeightChange.create(10.0, 15.0)
            >>> change.change_percentage()
            50.0  # 50% 증가
        """
        if self.previous_weight == 0.0:
            return None

        return round((self.change_amount / self.previous_weight) * 100, 2)

    def format_change(self, show_sign: bool = True) -> str:
        """
        변화량을 포맷팅된 문자열로 반환

        Args:
            show_sign: 양수일 때 + 기호 표시 여부

        Examples:
            >>> change = WeightChange.create(10.0, 15.0)
            >>> change.format_change()
            '+5.00%'
        """
        sign = "+" if self.change_amount > 0 and show_sign else ""
        return f"{sign}{self.change_amount:.2f}%"

    def compare_significance(self, other: "WeightChange") -> int:
        """
        다른 WeightChange와 변화량 크기 비교

        Returns:
            1: self가 더 큰 변화, 0: 같음, -1: other가 더 큰 변화
        """
        self_abs = abs(self.change_amount)
        other_abs = abs(other.change_amount)

        if self_abs > other_abs:
            return 1
        elif self_abs < other_abs:
            return -1
        else:
            return 0
