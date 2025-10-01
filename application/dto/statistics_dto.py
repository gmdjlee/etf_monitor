"""
Statistics DTO (Data Transfer Object)
통계 관련 데이터 전송을 위한 객체입니다.
"""

from dataclasses import asdict, dataclass
from typing import List, Optional


@dataclass
class DuplicateStockDto:
    """
    중복 종목 통계를 전송하기 위한 DTO

    Attributes:
        ticker: 종목 코드
        name: 종목명
        etf_count: 포함된 ETF 개수
        etf_names: ETF명 리스트
        total_amount: 총 평가금액
        avg_weight: 평균 비중
        max_weight: 최대 비중
        min_weight: 최소 비중
    """

    ticker: str
    name: str
    etf_count: int
    etf_names: List[str]
    total_amount: float
    avg_weight: float
    max_weight: float
    min_weight: float

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class DuplicateStockStatsDto:
    """
    중복 종목 통계 전체를 전송하기 위한 DTO

    Attributes:
        date: 기준일
        total_etfs: 전체 ETF 개수
        stocks: 중복 종목 리스트
        summary: 요약 정보
    """

    date: str
    total_etfs: int
    stocks: List[DuplicateStockDto]
    summary: dict

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "date": self.date,
            "total_etfs": self.total_etfs,
            "stocks": [s.to_dict() for s in self.stocks],
            "summary": self.summary,
        }


@dataclass
class AmountRankingDto:
    """
    평가금액 순위를 전송하기 위한 DTO

    Attributes:
        rank: 순위
        ticker: 종목 코드
        name: 종목명
        total_amount: 총 평가금액
        etf_count: 포함된 ETF 개수
        avg_weight: 평균 비중
        max_weight: 최대 비중
    """

    rank: int
    ticker: str
    name: str
    total_amount: float
    etf_count: int
    avg_weight: float
    max_weight: float

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class AmountRankingStatsDto:
    """
    평가금액 순위 통계 전체를 전송하기 위한 DTO

    Attributes:
        date: 기준일
        stocks: 순위 리스트
        summary: 요약 정보
    """

    date: str
    stocks: List[AmountRankingDto]
    summary: dict

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "date": self.date,
            "stocks": [s.to_dict() for s in self.stocks],
            "summary": self.summary,
        }


@dataclass
class ThemeStatsDto:
    """
    테마별 통계를 전송하기 위한 DTO

    Attributes:
        theme: 테마명
        etf_count: 해당 테마 ETF 개수
        etf_names: ETF명 리스트
        total_holdings: 총 보유 종목 수
        unique_stocks: 고유 종목 수
        duplicate_stocks: 중복 종목 리스트
        top_stocks: 상위 종목 리스트
    """

    theme: str
    etf_count: int
    etf_names: List[str]
    total_holdings: int
    unique_stocks: int
    duplicate_stocks: List[DuplicateStockDto]
    top_stocks: List[dict]

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
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
class WeightDistributionDto:
    """
    비중 분포 통계를 전송하기 위한 DTO

    Attributes:
        under_1: 1% 미만 종목 수
        range_1_to_3: 1~3% 종목 수
        range_3_to_5: 3~5% 종목 수
        range_5_to_10: 5~10% 종목 수
        over_10: 10% 이상 종목 수
    """

    under_1: int
    range_1_to_3: int
    range_3_to_5: int
    range_5_to_10: int
    over_10: int

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "under_1": self.under_1,
            "1_to_3": self.range_1_to_3,
            "3_to_5": self.range_3_to_5,
            "5_to_10": self.range_5_to_10,
            "over_10": self.over_10,
        }


@dataclass
class ETFOverlapDto:
    """
    ETF 간 중복도를 전송하기 위한 DTO

    Attributes:
        etf1_ticker: 첫 번째 ETF 코드
        etf1_name: 첫 번째 ETF명
        etf2_ticker: 두 번째 ETF 코드
        etf2_name: 두 번째 ETF명
        overlap_count: 중복 종목 수
        overlap_stocks: 중복 종목 코드 리스트
        overlap_ratio_1: ETF1 기준 중복 비율
        overlap_ratio_2: ETF2 기준 중복 비율
    """

    etf1_ticker: str
    etf1_name: str
    etf2_ticker: str
    etf2_name: str
    overlap_count: int
    overlap_stocks: List[str]
    overlap_ratio_1: float
    overlap_ratio_2: float

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class StatisticsSummaryDto:
    """
    통계 요약 정보를 전송하기 위한 DTO

    Attributes:
        date: 기준일
        total_etfs: 전체 ETF 개수
        total_stocks: 전체 종목 개수
        total_holdings: 전체 보유 종목 수
        avg_holdings_per_etf: ETF당 평균 보유 종목 수
        most_common_stock: 가장 많은 ETF에 포함된 종목
        highest_amount_stock: 평가금액이 가장 높은 종목
    """

    date: str
    total_etfs: int
    total_stocks: int
    total_holdings: int
    avg_holdings_per_etf: float
    most_common_stock: Optional[dict] = None
    highest_amount_stock: Optional[dict] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class StockFrequencyDto:
    """
    종목 빈도 통계를 전송하기 위한 DTO

    Attributes:
        ticker: 종목 코드
        name: 종목명
        frequency: 포함된 ETF 개수
        etf_tickers: ETF 코드 리스트
    """

    ticker: str
    name: str
    frequency: int
    etf_tickers: List[str]

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)
