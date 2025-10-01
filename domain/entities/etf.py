"""
ETF 엔티티
ETF를 표현하는 도메인 엔티티입니다.
"""

from dataclasses import dataclass
from typing import List

from shared.exceptions import InvalidEntityException
from shared.utils.validation import is_non_empty_string, is_valid_ticker


@dataclass(frozen=True)
class ETF:
    """
    ETF 엔티티

    불변 객체로 설계되어 있으며, 비즈니스 규칙을 강제합니다.

    Attributes:
        ticker: ETF 코드 (6자리)
        name: ETF명

    Examples:
        >>> etf = ETF.create("152100", "TIGER 반도체")
        >>> etf.ticker
        '152100'
        >>> etf.is_active()
        False
        >>> etf.contains_keyword("반도체")
        True
    """

    ticker: str
    name: str

    @staticmethod
    def create(ticker: str, name: str) -> "ETF":
        """
        ETF 인스턴스를 생성하고 유효성을 검증합니다.

        Args:
            ticker: ETF 코드
            name: ETF명

        Returns:
            검증된 ETF 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 데이터인 경우
        """
        # 티커 검증
        if not ticker:
            raise InvalidEntityException("ETF", "Ticker cannot be empty")

        # 티커를 6자리로 정규화
        normalized_ticker = ticker.strip().zfill(6)

        if not is_valid_ticker(normalized_ticker):
            raise InvalidEntityException("ETF", f"Invalid ticker format: {ticker}")

        # ETF명 검증
        if not is_non_empty_string(name):
            raise InvalidEntityException("ETF", "ETF name cannot be empty")

        return ETF(ticker=normalized_ticker, name=name.strip())

    def to_dict(self) -> dict:
        """엔티티를 딕셔너리로 변환"""
        return {"ticker": self.ticker, "name": self.name}

    def __eq__(self, other) -> bool:
        """두 ETF가 같은지 비교 (ticker 기준)"""
        if not isinstance(other, ETF):
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
        return f"ETF(ticker='{self.ticker}', name='{self.name}')"

    def is_active(self) -> bool:
        """액티브 ETF인지 확인"""
        return "액티브" in self.name

    def contains_keyword(self, keyword: str) -> bool:
        """ETF명에 특정 키워드가 포함되어 있는지 확인"""
        return keyword.lower() in self.name.lower()

    def contains_any_keyword(self, keywords: List[str]) -> bool:
        """ETF명에 키워드 목록 중 하나라도 포함되어 있는지 확인"""
        return any(self.contains_keyword(keyword) for keyword in keywords)

    def contains_all_keywords(self, keywords: List[str]) -> bool:
        """ETF명에 모든 키워드가 포함되어 있는지 확인"""
        return all(self.contains_keyword(keyword) for keyword in keywords)

    def matches_theme(self, themes: List[str]) -> bool:
        """테마 중 하나라도 일치하는지 확인"""
        return self.contains_any_keyword(themes)

    def has_exclusion(self, exclusions: List[str]) -> bool:
        """제외 키워드 중 하나라도 포함되어 있는지 확인"""
        return self.contains_any_keyword(exclusions)

    @property
    def display_name(self) -> str:
        """표시용 이름 (ETF명 + 코드)"""
        return f"{self.name} ({self.ticker})"

    def extract_theme_keywords(self, theme_list: List[str]) -> List[str]:
        """ETF명에서 일치하는 테마 키워드들을 추출"""
        matched_themes = []
        for theme in theme_list:
            if self.contains_keyword(theme):
                matched_themes.append(theme)
        return matched_themes
