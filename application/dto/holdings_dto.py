"""
Holdings DTO (Data Transfer Object)
보유 종목 관련 데이터 전송을 위한 객체입니다.
"""

from dataclasses import asdict, dataclass
from typing import List


@dataclass
class HoldingDto:
    """
    보유 종목 정보를 전송하기 위한 DTO

    Attributes:
        stock_ticker: 종목 코드
        stock_name: 종목명
        weight: 비중 (%)
        amount: 평가금액 (원)
        date: 기준일
    """

    stock_ticker: str
    stock_name: str
    weight: float
    amount: float
    date: str

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    @staticmethod
    def from_entity(holding):
        """엔티티로부터 DTO 생성"""
        return HoldingDto(
            stock_ticker=holding.stock_ticker,
            stock_name=holding.stock_name,
            weight=holding.weight,
            amount=holding.amount,
            date=holding.date_string,
        )


@dataclass
class HoldingComparisonDto:
    """
    보유 종목 비교 정보를 전송하기 위한 DTO

    Attributes:
        stock_ticker: 종목 코드
        stock_name: 종목명
        prev_weight: 이전 비중 (%)
        current_weight: 현재 비중 (%)
        change: 비중 변화량 (%)
        current_amount: 현재 평가금액 (원)
        status: 변화 상태 (신규, 제외, 비중 증가, 비중 감소, 유지)
    """

    stock_ticker: str
    stock_name: str
    prev_weight: float
    current_weight: float
    change: float
    current_amount: float
    status: str

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class HoldingsComparisonResultDto:
    """
    보유 종목 비교 결과 전체를 전송하기 위한 DTO

    Attributes:
        etf_ticker: ETF 코드
        etf_name: ETF명
        prev_date: 이전 날짜
        current_date: 현재 날짜
        comparison: 비교 결과 리스트
        summary: 요약 정보
    """

    etf_ticker: str
    etf_name: str
    prev_date: str
    current_date: str
    comparison: List[HoldingComparisonDto]
    summary: dict

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "etf_ticker": self.etf_ticker,
            "etf_name": self.etf_name,
            "prev_date": self.prev_date,
            "current_date": self.current_date,
            "comparison": [c.to_dict() for c in self.comparison],
            "summary": self.summary,
        }


@dataclass
class WeightHistoryDto:
    """
    비중 추이 정보를 전송하기 위한 DTO

    Attributes:
        etf_ticker: ETF 코드
        stock_ticker: 종목 코드
        stock_name: 종목명
        history: 날짜별 비중 기록
    """

    etf_ticker: str
    stock_ticker: str
    stock_name: str
    history: List[dict]  # [{'date': '2024-01-01', 'weight': 10.5, 'amount': 1000000}]

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    @staticmethod
    def from_holdings(
        etf_ticker: str, stock_ticker: str, stock_name: str, holdings: list
    ):
        """Holdings 리스트로부터 DTO 생성"""
        history = [
            {"date": h.date_string, "weight": h.weight, "amount": h.amount}
            for h in holdings
        ]

        return WeightHistoryDto(
            etf_ticker=etf_ticker,
            stock_ticker=stock_ticker,
            stock_name=stock_name,
            history=history,
        )


@dataclass
class TopHoldingsDto:
    """
    상위 보유 종목 정보를 전송하기 위한 DTO

    Attributes:
        etf_ticker: ETF 코드
        date: 기준일
        top_n: 상위 N개
        holdings: 상위 보유 종목 리스트
        total_weight: 상위 종목 비중 합계 (집중도)
    """

    etf_ticker: str
    date: str
    top_n: int
    holdings: List[HoldingDto]
    total_weight: float

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "etf_ticker": self.etf_ticker,
            "date": self.date,
            "top_n": self.top_n,
            "holdings": [h.to_dict() for h in self.holdings],
            "total_weight": self.total_weight,
        }


@dataclass
class HoldingsSummaryDto:
    """
    보유 종목 요약 정보를 전송하기 위한 DTO

    Attributes:
        total_count: 총 보유 종목 수
        total_amount: 총 평가금액
        total_weight: 총 비중
        top_10_weight: 상위 10개 종목 비중
        significant_count: 유의미한 비중(1% 이상) 종목 수
    """

    total_count: int
    total_amount: float
    total_weight: float
    top_10_weight: float
    significant_count: int

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class HoldingsChangeDto:
    """
    보유 종목 변화 정보를 전송하기 위한 DTO

    Attributes:
        new_count: 신규 추가 종목 수
        removed_count: 제외된 종목 수
        increased_count: 비중 증가 종목 수
        decreased_count: 비중 감소 종목 수
        unchanged_count: 비중 유지 종목 수
        new_stocks: 신규 추가 종목 리스트
        removed_stocks: 제외된 종목 리스트
    """

    new_count: int
    removed_count: int
    increased_count: int
    decreased_count: int
    unchanged_count: int
    new_stocks: List[HoldingDto]
    removed_stocks: List[HoldingDto]

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "new_count": self.new_count,
            "removed_count": self.removed_count,
            "increased_count": self.increased_count,
            "decreased_count": self.decreased_count,
            "unchanged_count": self.unchanged_count,
            "new_stocks": [s.to_dict() for s in self.new_stocks],
            "removed_stocks": [s.to_dict() for s in self.removed_stocks],
        }
