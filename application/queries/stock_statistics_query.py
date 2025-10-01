"""
Stock Statistics Query
종목 통계 조회를 위한 Query 객체입니다.
CQRS 패턴의 Query 측면을 구현합니다.
"""

from datetime import datetime
from typing import List, Optional

from application.dto.statistics_dto import (
    AmountRankingDto,
    AmountRankingStatsDto,
    DuplicateStockDto,
    DuplicateStockStatsDto,
    ThemeStatsDto,
)
from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from domain.services.statistics_calculator import StatisticsCalculator
from shared.utils.date_utils import to_date_string


class StockStatisticsQuery(LoggerMixin):
    """
    종목 통계 조회 쿼리

    중복 종목, 평가금액 순위, 테마별 통계 등을 조회합니다.

    Args:
        etf_repository: ETF 리포지토리
        statistics_calculator: 통계 계산 서비스
    """

    def __init__(
        self, etf_repository: ETFRepository, statistics_calculator: StatisticsCalculator
    ):
        self.etf_repo = etf_repository
        self.calculator = statistics_calculator

    def get_duplicate_stocks(
        self, date: Optional[datetime] = None, min_count: int = 2, limit: int = 100
    ) -> DuplicateStockStatsDto:
        """
        중복 종목 통계를 조회합니다.

        Args:
            date: 기준일 (None이면 최신 날짜)
            min_count: 최소 중복 횟수
            limit: 최대 반환 개수

        Returns:
            중복 종목 통계 DTO
        """
        self.logger.info("Executing duplicate stocks query")

        # 날짜 결정
        if date is None:
            date = self.etf_repo.get_latest_date()
            if not date:
                raise ValueError("No data available")

        # 전체 ETF 조회
        all_etfs = self.etf_repo.find_all()

        # 해당 날짜의 모든 보유 종목 조회
        all_holdings = self.etf_repo.find_holdings_by_date(date)

        self.logger.debug(
            f"Analyzing {len(all_holdings)} holdings from {len(all_etfs)} ETFs"
        )

        # 중복 종목 계산
        duplicate_stocks = self.calculator.calculate_duplicate_stocks(
            all_holdings, min_count
        )

        # 상위 N개만 선택
        duplicate_stocks = duplicate_stocks[:limit]

        # DTO 변환
        stock_dtos = []
        for stock in duplicate_stocks:
            # ETF 이름 조회
            etf_names = []
            for etf_ticker in stock["etf_tickers"]:
                etf = self.etf_repo.find_by_ticker(etf_ticker)
                if etf:
                    etf_names.append(etf.name)

            stock_dtos.append(
                DuplicateStockDto(
                    ticker=stock["ticker"],
                    name=stock["name"],
                    etf_count=stock["etf_count"],
                    etf_names=etf_names,
                    total_amount=stock["total_amount"],
                    avg_weight=stock["avg_weight"],
                    max_weight=stock["max_weight"],
                    min_weight=stock["min_weight"],
                )
            )

        # 요약 정보 생성
        summary = self._create_duplicate_summary(duplicate_stocks)

        return DuplicateStockStatsDto(
            date=to_date_string(date),
            total_etfs=len(all_etfs),
            stocks=stock_dtos,
            summary=summary,
        )

    def get_amount_ranking(
        self, date: Optional[datetime] = None, top_n: int = 100
    ) -> AmountRankingStatsDto:
        """
        평가금액 순위를 조회합니다.

        Args:
            date: 기준일 (None이면 최신 날짜)
            top_n: 상위 N개

        Returns:
            평가금액 순위 DTO
        """
        self.logger.info("Executing amount ranking query")

        # 날짜 결정
        if date is None:
            date = self.etf_repo.get_latest_date()
            if not date:
                raise ValueError("No data available")

        # 해당 날짜의 모든 보유 종목 조회
        all_holdings = self.etf_repo.find_holdings_by_date(date)

        # 평가금액 순위 계산
        ranking = self.calculator.calculate_amount_ranking(all_holdings, top_n)

        # DTO 변환
        stock_dtos = []
        for rank, stock in enumerate(ranking, start=1):
            stock_dtos.append(
                AmountRankingDto(
                    rank=rank,
                    ticker=stock["ticker"],
                    name=stock["name"],
                    total_amount=stock["total_amount"],
                    etf_count=stock["etf_count"],
                    avg_weight=stock["avg_weight"],
                    max_weight=stock["max_weight"],
                )
            )

        # 요약 정보 생성
        summary = self._create_amount_summary(ranking)

        return AmountRankingStatsDto(
            date=to_date_string(date), stocks=stock_dtos, summary=summary
        )

    def get_theme_statistics(
        self, theme: str, date: Optional[datetime] = None, limit: int = 100
    ) -> ThemeStatsDto:
        """
        특정 테마의 통계를 조회합니다.

        Args:
            theme: 테마 키워드
            date: 기준일 (None이면 최신 날짜)
            limit: 최대 반환 개수

        Returns:
            테마 통계 DTO
        """
        self.logger.info(f"Executing theme statistics query for: {theme}")

        # 날짜 결정
        if date is None:
            date = self.etf_repo.get_latest_date()
            if not date:
                raise ValueError("No data available")

        # 전체 ETF와 보유 종목 조회
        all_etfs = self.etf_repo.find_all()
        all_holdings = self.etf_repo.find_holdings_by_date(date)

        # 테마 통계 계산
        theme_stats = self.calculator.calculate_theme_statistics(
            all_holdings, all_etfs, theme
        )

        # 중복 종목 DTO 변환
        duplicate_dtos = []
        for stock in theme_stats["duplicate_stocks"][:limit]:
            # ETF 이름 조회
            etf_names = []
            for etf_ticker in stock["etf_tickers"]:
                etf = self.etf_repo.find_by_ticker(etf_ticker)
                if etf:
                    etf_names.append(etf.name)

            duplicate_dtos.append(
                DuplicateStockDto(
                    ticker=stock["ticker"],
                    name=stock["name"],
                    etf_count=stock["etf_count"],
                    etf_names=etf_names,
                    total_amount=stock["total_amount"],
                    avg_weight=stock["avg_weight"],
                    max_weight=stock["max_weight"],
                    min_weight=stock["min_weight"],
                )
            )

        # 상위 종목 계산 (평가금액 기준)
        theme_etf_tickers = set(theme_stats["etf_tickers"])
        theme_holdings = [h for h in all_holdings if h.etf_ticker in theme_etf_tickers]

        top_stocks = self.calculator.calculate_amount_ranking(theme_holdings, 10)

        # ETF 이름 조회
        etf_names = []
        for ticker in theme_stats["etf_tickers"]:
            etf = self.etf_repo.find_by_ticker(ticker)
            if etf:
                etf_names.append(etf.name)

        return ThemeStatsDto(
            theme=theme,
            etf_count=theme_stats["etf_count"],
            etf_names=etf_names,
            total_holdings=theme_stats["total_holdings"],
            unique_stocks=theme_stats["unique_stocks"],
            duplicate_stocks=duplicate_dtos,
            top_stocks=top_stocks,
        )

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
