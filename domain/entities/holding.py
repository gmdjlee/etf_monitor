"""
Holding 엔티티
ETF의 보유 종목 정보를 표현하는 도메인 엔티티입니다.
"""

from dataclasses import dataclass
from datetime import datetime

from shared.exceptions import InvalidEntityException
from shared.utils.date_utils import to_date_string
from shared.utils.validation import is_valid_amount, is_valid_ticker, is_valid_weight


@dataclass(frozen=True)
class Holding:
    """
    보유 종목 엔티티

    특정 날짜의 ETF 보유 종목 정보를 표현합니다.

    Attributes:
        etf_ticker: ETF 코드
        stock_ticker: 종목 코드
        date: 기준일
        weight: 비중 (%)
        amount: 평가금액 (원)
        stock_name: 종목명 (조회 시 조인으로 채워짐)

    Examples:
        >>> holding = Holding.create(
        ...     etf_ticker="152100",
        ...     stock_ticker="005930",
        ...     date=datetime(2024, 1, 1),
        ...     weight=15.5,
        ...     amount=1500000000
        ... )
        >>> holding.weight
        15.5
        >>> holding.is_significant_weight()
        True
    """

    etf_ticker: str
    stock_ticker: str
    date: datetime
    weight: float
    amount: float = 0.0
    stock_name: str = ""

    @staticmethod
    def create(
        etf_ticker: str,
        stock_ticker: str,
        date: datetime,
        weight: float,
        amount: float = 0.0,
        stock_name: str = "",
    ) -> "Holding":
        """
        Holding 인스턴스를 생성하고 유효성을 검증합니다.

        Args:
            etf_ticker: ETF 코드
            stock_ticker: 종목 코드
            date: 기준일
            weight: 비중 (%)
            amount: 평가금액 (원)
            stock_name: 종목명

        Returns:
            검증된 Holding 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 데이터인 경우
        """
        # ETF 티커 검증
        normalized_etf_ticker = etf_ticker.strip().zfill(6)
        if not is_valid_ticker(normalized_etf_ticker):
            raise InvalidEntityException("Holding", f"Invalid ETF ticker: {etf_ticker}")

        # 종목 티커 검증
        normalized_stock_ticker = stock_ticker.strip().zfill(6)
        if not is_valid_ticker(normalized_stock_ticker):
            raise InvalidEntityException(
                "Holding", f"Invalid stock ticker: {stock_ticker}"
            )

        # 날짜 검증
        if not isinstance(date, datetime):
            raise InvalidEntityException("Holding", "Date must be a datetime object")

        # 비중 검증
        if not is_valid_weight(weight):
            raise InvalidEntityException(
                "Holding", f"Invalid weight: {weight} (must be 0-100)"
            )

        # 금액 검증
        if not is_valid_amount(amount):
            raise InvalidEntityException(
                "Holding", f"Invalid amount: {amount} (must be >= 0)"
            )

        return Holding(
            etf_ticker=normalized_etf_ticker,
            stock_ticker=normalized_stock_ticker,
            date=date,
            weight=round(weight, 4),  # 소수점 4자리까지
            amount=round(amount, 2),  # 소수점 2자리까지
            stock_name=stock_name.strip() if stock_name else "",
        )

    def to_dict(self) -> dict:
        """엔티티를 딕셔너리로 변환"""
        return {
            "etf_ticker": self.etf_ticker,
            "stock_ticker": self.stock_ticker,
            "stock_name": self.stock_name,
            "date": to_date_string(self.date),
            "weight": self.weight,
            "amount": self.amount,
        }

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        stock_display = self.stock_name if self.stock_name else self.stock_ticker
        return f"{stock_display}: {self.weight}% ({self.amount:,.0f}원)"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"Holding(etf_ticker='{self.etf_ticker}', "
            f"stock_ticker='{self.stock_ticker}', "
            f"date='{to_date_string(self.date)}', "
            f"weight={self.weight}, "
            f"amount={self.amount})"
        )

    def is_significant_weight(self, threshold: float = 1.0) -> bool:
        """
        비중이 유의미한지 확인

        Args:
            threshold: 기준 비중 (기본값: 1%)
        """
        return self.weight >= threshold

    def is_top_holding(self, threshold: float = 5.0) -> bool:
        """
        상위 보유 종목인지 확인

        Args:
            threshold: 기준 비중 (기본값: 5%)
        """
        return self.weight >= threshold

    def calculate_weight_change(self, other: "Holding") -> float:
        """
        다른 Holding과의 비중 차이 계산

        Args:
            other: 비교할 Holding 객체

        Returns:
            비중 변화량 (양수: 증가, 음수: 감소)
        """
        if self.stock_ticker != other.stock_ticker:
            raise ValueError("Cannot compare holdings of different stocks")

        return self.weight - other.weight

    def has_weight_increased(self, other: "Holding", threshold: float = 0.01) -> bool:
        """
        비중이 증가했는지 확인

        Args:
            other: 비교할 이전 Holding 객체
            threshold: 유의미한 변화 기준 (기본값: 0.01%)
        """
        change = self.calculate_weight_change(other)
        return change > threshold

    def has_weight_decreased(self, other: "Holding", threshold: float = 0.01) -> bool:
        """
        비중이 감소했는지 확인

        Args:
            other: 비교할 이전 Holding 객체
            threshold: 유의미한 변화 기준 (기본값: 0.01%)
        """
        change = self.calculate_weight_change(other)
        return change < -threshold

    def with_stock_name(self, stock_name: str) -> "Holding":
        """
        종목명을 설정한 새로운 Holding 반환 (불변성 유지)

        Args:
            stock_name: 설정할 종목명
        """
        return Holding(
            etf_ticker=self.etf_ticker,
            stock_ticker=self.stock_ticker,
            date=self.date,
            weight=self.weight,
            amount=self.amount,
            stock_name=stock_name,
        )

    @property
    def date_string(self) -> str:
        """날짜를 문자열로 반환"""
        return to_date_string(self.date)

    @property
    def amount_in_billions(self) -> float:
        """평가금액을 억원 단위로 반환"""
        return self.amount / 100_000_000
