"""
Stock 엔티티
주식을 표현하는 도메인 엔티티입니다.
"""

from dataclasses import dataclass

from shared.exceptions import InvalidEntityException
from shared.utils.validation import is_non_empty_string, is_valid_ticker


@dataclass(frozen=True)
class Stock:
    """
    주식 엔티티

    불변 객체로 설계되어 있으며, 비즈니스 규칙을 강제합니다.

    Attributes:
        ticker: 종목 코드 (6자리)
        name: 종목명

    Examples:
        >>> stock = Stock.create("005930", "삼성전자")
        >>> stock.ticker
        '005930'
        >>> stock.name
        '삼성전자'
    """

    ticker: str
    name: str

    @staticmethod
    def create(ticker: str, name: str) -> "Stock":
        """
        Stock 인스턴스를 생성하고 유효성을 검증합니다.

        Args:
            ticker: 종목 코드
            name: 종목명

        Returns:
            검증된 Stock 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 데이터인 경우
        """
        # 티커 검증
        if not ticker:
            raise InvalidEntityException("Stock", "Ticker cannot be empty")

        # 티커를 6자리로 정규화
        normalized_ticker = ticker.strip().zfill(6)

        if not is_valid_ticker(normalized_ticker):
            raise InvalidEntityException("Stock", f"Invalid ticker format: {ticker}")

        # 종목명 검증
        if not is_non_empty_string(name):
            raise InvalidEntityException("Stock", "Stock name cannot be empty")

        return Stock(ticker=normalized_ticker, name=name.strip())

    def to_dict(self) -> dict:
        """엔티티를 딕셔너리로 변환"""
        return {"ticker": self.ticker, "name": self.name}

    def __eq__(self, other) -> bool:
        """두 Stock이 같은지 비교 (ticker 기준)"""
        if not isinstance(other, Stock):
            return False
        return self.ticker == other.ticker

    def __hash__(self) -> int:
        """해시 값 반환 (Set, Dict 키로 사용 가능)"""
        return hash(self.ticker)

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        return f"{self.name}({self.ticker})"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return f"Stock(ticker='{self.ticker}', name='{self.name}')"

    def matches_name(self, keyword: str) -> bool:
        """종목명에 특정 키워드가 포함되어 있는지 확인"""
        return keyword.lower() in self.name.lower()

    @property
    def display_name(self) -> str:
        """표시용 이름 (종목명 + 코드)"""
        return f"{self.name} ({self.ticker})"
