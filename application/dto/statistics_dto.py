"""
Statistics DTO (개선됨)
✅ BaseDTO 상속으로 중복 제거
"""

from dataclasses import dataclass
from typing import List, Optional

from application.dto.base_dto import BaseDTO


@dataclass
class DuplicateStockDto(BaseDTO):
    """중복 종목 통계를 전송하기 위한 DTO"""

    ticker: str
    name: str
    etf_count: int
    etf_names: List[str]
    total_amount: float
    avg_weight: float
    max_weight: float
    min_weight: float


@dataclass
class DuplicateStockStatsDto(BaseDTO):
    """중복 종목 통계 전체를 전송하기 위한 DTO"""

    date: str
    total_etfs: int
    stocks: List[DuplicateStockDto]
    summary: dict

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "date": self.date,
            "total_etfs": self.total_etfs,
            "stocks": [s.to_dict() for s in self.stocks],
            "summary": self.summary,
        }


@dataclass
class AmountRankingDto(BaseDTO):
    """평가금액 순위를 전송하기 위한 DTO"""

    rank: int
    ticker: str
    name: str
    total_amount: float
    etf_count: int
    avg_weight: float
    max_weight: float


@dataclass
class AmountRankingStatsDto(BaseDTO):
    """평가금액 순위 통계 전체를 전송하기 위한 DTO"""

    date: str
    stocks: List[AmountRankingDto]
    summary: dict

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "date": self.date,
            "stocks": [s.to_dict() for s in self.stocks],
            "summary": self.summary,
        }


@dataclass
class ThemeStatsDto(BaseDTO):
    """테마별 통계를 전송하기 위한 DTO"""

    theme: str
    etf_count: int
    etf_names: List[str]
    total_holdings: int
    unique_stocks: int
    duplicate_stocks: List[DuplicateStockDto]
    top_stocks: List[dict]

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "theme": self.theme,
            "etf_count": self.etf_count,
            "etf_names": self.etf_names,
            "total_holdings": self.total_holdings,
            "unique_stocks": self.unique_stocks,
            "duplicate_stocks": [s.to_dict() for s in self.duplicate_stocks],
            "top_stocks": self.top_stocks,
        }


@dataclass
class WeightDistributionDto(BaseDTO):
    """비중 분포 통계를 전송하기 위한 DTO"""

    under_1: int
    range_1_to_3: int
    range_3_to_5: int
    range_5_to_10: int
    over_10: int

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현 (키 이름 변경)"""
        return {
            "under_1": self.under_1,
            "1_to_3": self.range_1_to_3,
            "3_to_5": self.range_3_to_5,
            "5_to_10": self.range_5_to_10,
            "over_10": self.over_10,
        }


@dataclass
class ETFOverlapDto(BaseDTO):
    """ETF 간 중복도를 전송하기 위한 DTO"""

    etf1_ticker: str
    etf1_name: str
    etf2_ticker: str
    etf2_name: str
    overlap_count: int
    overlap_stocks: List[str]
    overlap_ratio_1: float
    overlap_ratio_2: float


@dataclass
class StatisticsSummaryDto(BaseDTO):
    """통계 요약 정보를 전송하기 위한 DTO"""

    date: str
    total_etfs: int
    total_stocks: int
    total_holdings: int
    avg_holdings_per_etf: float
    most_common_stock: Optional[dict] = None
    highest_amount_stock: Optional[dict] = None


@dataclass
class StockFrequencyDto(BaseDTO):
    """종목 빈도 통계를 전송하기 위한 DTO"""

    ticker: str
    name: str
    frequency: int
    etf_tickers: List[str]
