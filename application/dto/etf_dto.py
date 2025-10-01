"""
ETF DTO (Data Transfer Object) - 개선됨
✅ BaseDTO 상속으로 중복 제거
"""

from dataclasses import dataclass
from typing import List, Optional

from application.dto.base_dto import BaseDTO


@dataclass
class ETFDto(BaseDTO):
    """
    ETF 정보를 전송하기 위한 DTO

    Attributes:
        ticker: ETF 코드
        name: ETF명
        is_active: 액티브 ETF 여부
        matched_themes: 매칭된 테마 리스트
    """

    ticker: str
    name: str
    is_active: bool = False
    matched_themes: List[str] = None

    def __post_init__(self):
        if self.matched_themes is None:
            self.matched_themes = []

    @staticmethod
    def from_entity(etf, matched_themes: List[str] = None):
        """엔티티로부터 DTO 생성"""
        return ETFDto(
            ticker=etf.ticker,
            name=etf.name,
            is_active=etf.is_active(),
            matched_themes=matched_themes or [],
        )


@dataclass
class ETFListDto(BaseDTO):
    """
    ETF 목록을 전송하기 위한 DTO

    Attributes:
        etfs: ETF DTO 리스트
        total_count: 전체 개수
        filter_applied: 필터 적용 여부
    """

    etfs: List[ETFDto]
    total_count: int
    filter_applied: bool = False

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (커스텀 구현)"""
        return {
            "etfs": [etf.to_dict() for etf in self.etfs],
            "total_count": self.total_count,
            "filter_applied": self.filter_applied,
        }


@dataclass
class ETFDetailDto(BaseDTO):
    """
    ETF 상세 정보를 전송하기 위한 DTO

    Attributes:
        ticker: ETF 코드
        name: ETF명
        is_active: 액티브 ETF 여부
        holdings_count: 보유 종목 수
        latest_date: 최신 데이터 날짜
        available_dates: 데이터가 있는 날짜 리스트
    """

    ticker: str
    name: str
    is_active: bool
    holdings_count: int
    latest_date: Optional[str] = None
    available_dates: List[str] = None

    def __post_init__(self):
        if self.available_dates is None:
            self.available_dates = []


@dataclass
class ETFFilterDto(BaseDTO):
    """
    ETF 필터 조건을 전송하기 위한 DTO

    Attributes:
        themes: 테마 키워드 리스트
        exclusions: 제외 키워드 리스트
        require_active: 액티브 필수 여부
        min_holdings: 최소 보유 종목 수
    """

    themes: List[str] = None
    exclusions: List[str] = None
    require_active: bool = True
    min_holdings: Optional[int] = None

    def __post_init__(self):
        if self.themes is None:
            self.themes = []
        if self.exclusions is None:
            self.exclusions = []


@dataclass
class ETFComparisonDto(BaseDTO):
    """
    ETF 비교 결과를 전송하기 위한 DTO

    Attributes:
        etf1_ticker: 첫 번째 ETF 코드
        etf2_ticker: 두 번째 ETF 코드
        overlap_count: 중복 종목 수
        overlap_ratio: 중복 비율 (%)
        unique_to_etf1: ETF1에만 있는 종목 수
        unique_to_etf2: ETF2에만 있는 종목 수
    """

    etf1_ticker: str
    etf2_ticker: str
    overlap_count: int
    overlap_ratio: float
    unique_to_etf1: int
    unique_to_etf2: int
