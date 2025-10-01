"""
Holdings DTO (개선됨)
✅ BaseDTO 상속으로 중복 제거
"""

from dataclasses import dataclass
from typing import List

from application.dto.base_dto import BaseDTO


@dataclass
class HoldingDto(BaseDTO):
    """보유 종목 정보를 전송하기 위한 DTO"""

    stock_ticker: str
    stock_name: str
    weight: float
    amount: float
    date: str

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
class HoldingComparisonDto(BaseDTO):
    """보유 종목 비교 정보를 전송하기 위한 DTO"""

    stock_ticker: str
    stock_name: str
    prev_weight: float
    current_weight: float
    change: float
    current_amount: float
    status: str


@dataclass
class HoldingsComparisonResultDto(BaseDTO):
    """보유 종목 비교 결과 전체를 전송하기 위한 DTO"""

    etf_ticker: str
    etf_name: str
    prev_date: str
    current_date: str
    comparison: List[HoldingComparisonDto]
    summary: dict

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "etf_ticker": self.etf_ticker,
            "etf_name": self.etf_name,
            "prev_date": self.prev_date,
            "current_date": self.current_date,
            "comparison": [c.to_dict() for c in self.comparison],
            "summary": self.summary,
        }


@dataclass
class WeightHistoryDto(BaseDTO):
    """비중 추이 정보를 전송하기 위한 DTO"""

    etf_ticker: str
    stock_ticker: str
    stock_name: str
    history: List[dict]

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
class TopHoldingsDto(BaseDTO):
    """상위 보유 종목 정보를 전송하기 위한 DTO"""

    etf_ticker: str
    date: str
    top_n: int
    holdings: List[HoldingDto]
    total_weight: float

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "etf_ticker": self.etf_ticker,
            "date": self.date,
            "top_n": self.top_n,
            "holdings": [h.to_dict() for h in self.holdings],
            "total_weight": self.total_weight,
        }


@dataclass
class HoldingsSummaryDto(BaseDTO):
    """보유 종목 요약 정보를 전송하기 위한 DTO"""

    total_count: int
    total_amount: float
    total_weight: float
    top_10_weight: float
    significant_count: int


@dataclass
class HoldingsChangeDto(BaseDTO):
    """보유 종목 변화 정보를 전송하기 위한 DTO"""

    new_count: int
    removed_count: int
    increased_count: int
    decreased_count: int
    unchanged_count: int
    new_stocks: List[HoldingDto]
    removed_stocks: List[HoldingDto]

    def to_dict(self) -> dict:
        """커스텀 to_dict 구현"""
        return {
            "new_count": self.new_count,
            "removed_count": self.removed_count,
            "increased_count": self.increased_count,
            "decreased_count": self.decreased_count,
            "unchanged_count": self.unchanged_count,
            "new_stocks": [s.to_dict() for s in self.new_stocks],
            "removed_stocks": [s.to_dict() for s in self.removed_stocks],
        }
