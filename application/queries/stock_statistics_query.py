"""
Stock Statistics Query (최적화 및 개선됨)
✅ 중복 코드 제거 및 헬퍼 메서드 추가
"""

from datetime import datetime
from typing import Dict, List, Optional

from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from domain.services.statistics_calculator import StatisticsCalculator
from shared.utils.date_utils import to_date_string

from application.dto.statistics_dto import (
    AmountRankingDto,
    AmountRankingStatsDto,
    DuplicateStockDto,
    DuplicateStockStatsDto,
    ThemeStatsDto,
)


class StockStatisticsQuery(LoggerMixin):
    """
    종목 통계 조회 쿼리

    중복 종목, 평가금액 순위, 테마별 통계 등을 조회합니다.
    """

    def __init__(
        self, etf_repository: ETFRepository, statistics_calculator: StatisticsCalculator
    ):
        self.etf_repo = etf_repository
        self.calculator = statistics_calculator

    def get_duplicate_stocks(
        self, date: Optional[datetime] = None, min_count: int = 2, limit: int = 100
    ) -> DuplicateStockStatsDto:
        """중복 종목 통계를 조회합니다."""
        self.logger.info("Executing duplicate stocks query")

        date = date or self.etf_repo.get_latest_date()
        if not date:
            raise ValueError("No data available")

        all_holdings = self.etf_repo.find_holdings_by_date(date)
        self.logger.debug(f"Analyzing {len(all_holdings)} holdings")

        duplicate_stocks = self.calculator.calculate_duplicate_stocks(
            all_holdings, min_count
        )[:limit]

        # ✅ 개선: 헬퍼 메서드 사용
        etf_name_map = self._get_etf_name_map(
            [ticker for stock in duplicate_stocks for ticker in stock["etf_tickers"]]
        )

        stock_dtos = [
            DuplicateStockDto(
                ticker=stock["ticker"],
                name=stock["name"],
                etf_count=stock["etf_count"],
                etf_names=[etf_name_map.get(t, t) for t in stock["etf_tickers"]],
                total_amount=stock["total_amount"],
                avg_weight=stock["avg_weight"],
                max_weight=stock["max_weight"],
                min_weight=stock["min_weight"],
            )
            for stock in duplicate_stocks
        ]

        summary = self._create_duplicate_summary(duplicate_stocks)
        total_etfs = len(set(h.etf_ticker for h in all_holdings))

        return DuplicateStockStatsDto(
            date=to_date_string(date),
            total_etfs=total_etfs,
            stocks=stock_dtos,
            summary=summary,
        )

    def get_amount_ranking(
        self, date: Optional[datetime] = None, top_n: int = 100
    ) -> AmountRankingStatsDto:
        """평가금액 순위를 조회합니다."""
        self.logger.info("Executing amount ranking query")

        date = date or self.etf_repo.get_latest_date()
        if not date:
            raise ValueError("No data available")

        all_holdings = self.etf_repo.find_holdings_by_date(date)
        ranking = self.calculator.calculate_amount_ranking(all_holdings, top_n)

        stock_dtos = [
            AmountRankingDto(
                rank=rank,
                ticker=stock["ticker"],
                name=stock["name"],
                total_amount=stock["total_amount"],
                etf_count=stock["etf_count"],
                avg_weight=stock["avg_weight"],
                max_weight=stock["max_weight"],
            )
            for rank, stock in enumerate(ranking, start=1)
        ]

        summary = self._create_amount_summary(ranking)

        return AmountRankingStatsDto(
            date=to_date_string(date), stocks=stock_dtos, summary=summary
        )

    def get_theme_statistics(
        self, theme: str, date: Optional[datetime] = None, limit: int = 100
    ) -> ThemeStatsDto:
        """특정 테마의 통계를 조회합니다."""
        self.logger.info(f"Executing theme statistics query for: {theme}")

        date = date or self.etf_repo.get_latest_date()
        if not date:
            raise ValueError("No data available")

        all_etfs = self.etf_repo.find_all()
        all_holdings = self.etf_repo.find_holdings_by_date(date)

        theme_stats = self.calculator.calculate_theme_statistics(
            all_holdings, all_etfs, theme
        )

        # ✅ 개선: 헬퍼 메서드 사용
        duplicate_stocks = theme_stats["duplicate_stocks"][:limit]
        etf_name_map = self._get_etf_name_map(
            [ticker for stock in duplicate_stocks for ticker in stock["etf_tickers"]]
        )

        duplicate_dtos = [
            DuplicateStockDto(
                ticker=stock["ticker"],
                name=stock["name"],
                etf_count=stock["etf_count"],
                etf_names=[etf_name_map.get(t, t) for t in stock["etf_tickers"]],
                total_amount=stock["total_amount"],
                avg_weight=stock["avg_weight"],
                max_weight=stock["max_weight"],
                min_weight=stock["min_weight"],
            )
            for stock in duplicate_stocks
        ]

        theme_etf_tickers = set(theme_stats["etf_tickers"])
        theme_holdings = [h for h in all_holdings if h.etf_ticker in theme_etf_tickers]
        top_stocks = self.calculator.calculate_amount_ranking(theme_holdings, 10)

        # ✅ 개선: 헬퍼 메서드 사용
        etf_names = self._get_etf_names(theme_stats["etf_tickers"])

        return ThemeStatsDto(
            theme=theme,
            etf_count=theme_stats["etf_count"],
            etf_names=etf_names,
            total_holdings=theme_stats["total_holdings"],
            unique_stocks=theme_stats["unique_stocks"],
            duplicate_stocks=duplicate_dtos,
            top_stocks=top_stocks,
        )

    # ✅ 새로운 헬퍼 메서드들

    def _get_etf_name_map(self, tickers: List[str]) -> Dict[str, str]:
        """
        ETF ticker -> name 맵핑을 생성합니다.

        중복 코드를 제거하기 위한 헬퍼 메서드입니다.
        """
        if not tickers:
            return {}

        unique_tickers = list(set(tickers))
        etfs = self.etf_repo.find_by_tickers(unique_tickers)
        return {etf.ticker: etf.name for etf in etfs}

    def _get_etf_names(self, tickers: List[str]) -> List[str]:
        """
        ETF ticker 리스트를 이름 리스트로 변환합니다.
        """
        etf_name_map = self._get_etf_name_map(tickers)
        return [etf_name_map.get(ticker, ticker) for ticker in tickers]

    def _create_duplicate_summary(self, duplicate_stocks: List[dict]) -> dict:
        """중복 종목 요약 정보 생성"""
        if not duplicate_stocks:
            return {"total_duplicate_stocks": 0, "max_etf_count": 0, "avg_etf_count": 0}

        max_count = max(s["etf_count"] for s in duplicate_stocks)
        avg_count = sum(s["etf_count"] for s in duplicate_stocks) / len(
            duplicate_stocks
        )

        return {
            "total_duplicate_stocks": len(duplicate_stocks),
            "max_etf_count": max_count,
            "avg_etf_count": round(avg_count, 2),
        }

    def _create_amount_summary(self, ranking: List[dict]) -> dict:
        """평가금액 순위 요약 정보 생성"""
        if not ranking:
            return {"total_stocks": 0, "total_amount": 0, "top_10_amount": 0}

        total_amount = sum(s["total_amount"] for s in ranking)
        top_10_amount = sum(s["total_amount"] for s in ranking[:10])

        return {
            "total_stocks": len(ranking),
            "total_amount": total_amount,
            "top_10_amount": top_10_amount,
            "top_10_ratio": round(
                (top_10_amount / total_amount * 100) if total_amount > 0 else 0, 2
            ),
        }
