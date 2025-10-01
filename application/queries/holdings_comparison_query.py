"""
Holdings Comparison Query
보유 종목 비교 조회를 위한 Query 객체입니다.
CQRS 패턴의 Query 측면을 구현합니다.
"""

from datetime import datetime
from typing import List, Optional

from application.dto.holdings_dto import (
    HoldingComparisonDto,
    HoldingsComparisonResultDto,
)
from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from domain.repositories.stock_repository import StockRepository
from domain.services.holdings_analyzer import HoldingsAnalyzer
from shared.utils.date_utils import to_date_string


class HoldingsComparisonQuery(LoggerMixin):
    """
    보유 종목 비교 조회 쿼리

    특정 ETF의 두 시점 간 보유 종목을 비교하여 변화를 조회합니다.

    Args:
        etf_repository: ETF 리포지토리
        stock_repository: Stock 리포지토리
        holdings_analyzer: 보유 종목 분석 서비스
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        stock_repository: StockRepository,
        holdings_analyzer: HoldingsAnalyzer,
    ):
        self.etf_repo = etf_repository
        self.stock_repo = stock_repository
        self.analyzer = holdings_analyzer

    def execute(
        self,
        etf_ticker: str,
        current_date: Optional[datetime] = None,
        previous_date: Optional[datetime] = None,
    ) -> HoldingsComparisonResultDto:
        """
        보유 종목 비교 조회를 실행합니다.

        Args:
            etf_ticker: ETF 코드
            current_date: 현재 날짜 (None이면 최신 날짜)
            previous_date: 이전 날짜 (None이면 current_date의 이전 날짜)

        Returns:
            비교 결과 DTO

        Raises:
            ValueError: ETF를 찾을 수 없거나 데이터가 부족한 경우
        """
        self.logger.info(f"Executing holdings comparison query for ETF: {etf_ticker}")

        # ETF 조회
        etf = self.etf_repo.find_by_ticker(etf_ticker)
        if not etf:
            raise ValueError(f"ETF not found: {etf_ticker}")

        # 날짜 결정
        available_dates = self.etf_repo.get_available_dates(etf_ticker)
        if not available_dates:
            raise ValueError(f"No data available for ETF: {etf_ticker}")

        if current_date is None:
            current_date = available_dates[0]  # 최신 날짜

        if previous_date is None:
            # current_date 이전의 가장 최근 날짜 찾기
            prev_dates = [d for d in available_dates if d < current_date]
            if not prev_dates:
                # 데이터가 하나만 있는 경우
                previous_date = current_date
            else:
                previous_date = prev_dates[0]

        self.logger.debug(
            f"Comparing dates: {to_date_string(previous_date)} vs {to_date_string(current_date)}"
        )

        # 보유 종목 조회
        current_holdings = self.etf_repo.find_holdings_by_etf_and_date(
            etf_ticker, current_date
        )
        previous_holdings = self.etf_repo.find_holdings_by_etf_and_date(
            etf_ticker, previous_date
        )

        # 비교 수행
        comparison_result = self.analyzer.compare_holdings(
            previous_holdings, current_holdings
        )

        # DTO 변환
        comparison_dtos = self._create_comparison_dtos(
            previous_holdings, current_holdings, comparison_result
        )

        # 요약 정보 생성
        summary = self._create_summary(comparison_result)

        return HoldingsComparisonResultDto(
            etf_ticker=etf_ticker,
            etf_name=etf.name,
            prev_date=to_date_string(previous_date),
            current_date=to_date_string(current_date),
            comparison=comparison_dtos,
            summary=summary,
        )

    def _create_comparison_dtos(
        self, previous_holdings: List, current_holdings: List, comparison_result: dict
    ) -> List[HoldingComparisonDto]:
        """비교 결과를 DTO 리스트로 변환"""
        prev_dict = {h.stock_ticker: h for h in previous_holdings}
        curr_dict = {h.stock_ticker: h for h in current_holdings}

        all_tickers = set(prev_dict.keys()) | set(curr_dict.keys())

        dtos = []
        for ticker in all_tickers:
            prev_holding = prev_dict.get(ticker)
            curr_holding = curr_dict.get(ticker)

            prev_weight = prev_holding.weight if prev_holding else 0.0
            curr_weight = curr_holding.weight if curr_holding else 0.0
            change = curr_weight - prev_weight
            curr_amount = curr_holding.amount if curr_holding else 0.0
            stock_name = (
                curr_holding.stock_name
                if curr_holding
                else prev_holding.stock_name
                if prev_holding
                else ""
            )

            # 상태 결정
            if prev_holding is None:
                status = "신규"
            elif curr_holding is None:
                status = "제외"
            elif change > 0.01:
                status = "비중 증가"
            elif change < -0.01:
                status = "비중 감소"
            else:
                status = "유지"

            dtos.append(
                HoldingComparisonDto(
                    stock_ticker=ticker,
                    stock_name=stock_name,
                    prev_weight=prev_weight,
                    current_weight=curr_weight,
                    change=round(change, 4),
                    current_amount=curr_amount,
                    status=status,
                )
            )

        # 현재 비중 기준으로 정렬
        dtos.sort(key=lambda x: x.current_weight, reverse=True)

        return dtos

    def _create_summary(self, comparison_result: dict) -> dict:
        """요약 정보 생성"""
        return {
            "new_count": len(comparison_result["new"]),
            "removed_count": len(comparison_result["removed"]),
            "increased_count": len(comparison_result["increased"]),
            "decreased_count": len(comparison_result["decreased"]),
            "unchanged_count": len(comparison_result["unchanged"]),
            "total_current": (
                len(comparison_result["new"])
                + len(comparison_result["increased"])
                + len(comparison_result["decreased"])
                + len(comparison_result["unchanged"])
            ),
        }
