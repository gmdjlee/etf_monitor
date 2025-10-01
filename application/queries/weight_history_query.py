"""
Weight History Query
비중 추이 조회를 위한 Query 객체입니다.
CQRS 패턴의 Query 측면을 구현합니다.
"""

from typing import Optional

from application.dto.holdings_dto import WeightHistoryDto
from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository


class WeightHistoryQuery(LoggerMixin):
    """
    비중 추이 조회 쿼리

    특정 ETF 내 특정 종목의 비중 추이를 조회합니다.

    Args:
        etf_repository: ETF 리포지토리
    """

    def __init__(self, etf_repository: ETFRepository):
        self.etf_repo = etf_repository

    def execute(self, etf_ticker: str, stock_ticker: str) -> WeightHistoryDto:
        """
        비중 추이 조회를 실행합니다.

        Args:
            etf_ticker: ETF 코드
            stock_ticker: 종목 코드

        Returns:
            비중 추이 DTO

        Raises:
            ValueError: ETF나 데이터를 찾을 수 없는 경우
        """
        self.logger.info(
            f"Executing weight history query: ETF={etf_ticker}, Stock={stock_ticker}"
        )

        # ETF 조회
        etf = self.etf_repo.find_by_ticker(etf_ticker)
        if not etf:
            raise ValueError(f"ETF not found: {etf_ticker}")

        # 비중 추이 조회
        holdings = self.etf_repo.find_weight_history(etf_ticker, stock_ticker)

        if not holdings:
            raise ValueError(
                f"No history found for stock {stock_ticker} in ETF {etf_ticker}"
            )

        # 종목명 가져오기
        stock_name = holdings[0].stock_name if holdings else stock_ticker

        self.logger.debug(f"Found {len(holdings)} history records")

        # DTO 변환
        return WeightHistoryDto.from_holdings(
            etf_ticker=etf_ticker,
            stock_ticker=stock_ticker,
            stock_name=stock_name,
            holdings=holdings,
        )

    def get_latest_weight(self, etf_ticker: str, stock_ticker: str) -> Optional[float]:
        """
        특정 종목의 최신 비중을 조회합니다.

        Args:
            etf_ticker: ETF 코드
            stock_ticker: 종목 코드

        Returns:
            최신 비중 (%), 데이터가 없으면 None
        """
        holdings = self.etf_repo.find_weight_history(etf_ticker, stock_ticker)

        if not holdings:
            return None

        # 날짜 기준으로 정렬되어 있으므로 마지막 항목이 최신
        return holdings[-1].weight

    def has_history(self, etf_ticker: str, stock_ticker: str) -> bool:
        """
        비중 추이 데이터가 존재하는지 확인합니다.

        Args:
            etf_ticker: ETF 코드
            stock_ticker: 종목 코드

        Returns:
            데이터 존재 여부
        """
        holdings = self.etf_repo.find_weight_history(etf_ticker, stock_ticker)
        return len(holdings) > 0
