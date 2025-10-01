"""
Get Statistics Use Case (단순화됨)
✅ Query에 위임하여 중복 제거
"""

from datetime import datetime
from typing import Optional

from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from domain.services.statistics_calculator import StatisticsCalculator
from shared.result import Result

from application.dto.statistics_dto import (
    AmountRankingStatsDto,
    DuplicateStockStatsDto,
    ThemeStatsDto,
)
from application.queries.stock_statistics_query import StockStatisticsQuery


class GetStatisticsUseCase(LoggerMixin):
    """
    통계 조회 유스케이스

    Query에 실제 로직을 위임하고, 에러 처리만 담당합니다.
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        statistics_calculator: StatisticsCalculator,
        stock_statistics_query: StockStatisticsQuery,
    ):
        self.etf_repo = etf_repository
        self.calculator = statistics_calculator
        self.query = stock_statistics_query

    def get_duplicate_stocks(
        self, date: Optional[datetime] = None, min_count: int = 2, limit: int = 100
    ) -> Result[DuplicateStockStatsDto]:
        """중복 종목 통계를 조회합니다."""
        try:
            result_dto = self.query.get_duplicate_stocks(date, min_count, limit)
            return Result.ok(result_dto)
        except ValueError as e:
            return Result.fail(str(e))
        except Exception as e:
            self.logger.error(f"Failed to get duplicate stocks: {e}", exc_info=True)
            return Result.fail("중복 종목 통계 조회 실패")

    def get_amount_ranking(
        self, date: Optional[datetime] = None, top_n: int = 100
    ) -> Result[AmountRankingStatsDto]:
        """평가금액 순위를 조회합니다."""
        try:
            result_dto = self.query.get_amount_ranking(date, top_n)
            return Result.ok(result_dto)
        except ValueError as e:
            return Result.fail(str(e))
        except Exception as e:
            self.logger.error(f"Failed to get amount ranking: {e}", exc_info=True)
            return Result.fail("평가금액 순위 조회 실패")

    def get_theme_statistics(
        self, theme: str, date: Optional[datetime] = None, limit: int = 100
    ) -> Result[ThemeStatsDto]:
        """특정 테마의 통계를 조회합니다."""
        try:
            result_dto = self.query.get_theme_statistics(theme, date, limit)
            return Result.ok(result_dto)
        except ValueError as e:
            return Result.fail(str(e))
        except Exception as e:
            self.logger.error(f"Failed to get theme statistics: {e}", exc_info=True)
            return Result.fail("테마 통계 조회 실패")

    def get_statistics_summary(self, date: Optional[datetime] = None) -> Result[dict]:
        """전체 통계 요약 정보를 조회합니다."""
        try:
            date = date or self.etf_repo.get_latest_date()
            if not date:
                return Result.fail("데이터가 없습니다")

            all_etfs = self.etf_repo.find_all()
            all_holdings = self.etf_repo.find_holdings_by_date(date)

            unique_stocks = len(set(h.stock_ticker for h in all_holdings))
            avg_holdings = len(all_holdings) / len(all_etfs) if all_etfs else 0

            stock_frequency = self.calculator.get_top_stocks_by_frequency(
                all_holdings, top_n=1
            )
            most_common = None
            if stock_frequency:
                ticker, freq = stock_frequency[0]
                holdings_with_name = [
                    h for h in all_holdings if h.stock_ticker == ticker and h.stock_name
                ]
                stock_name = (
                    holdings_with_name[0].stock_name if holdings_with_name else ticker
                )
                most_common = {"ticker": ticker, "name": stock_name, "frequency": freq}

            amount_ranking = self.calculator.calculate_amount_ranking(
                all_holdings, top_n=1
            )
            highest_amount = None
            if amount_ranking:
                highest_amount = {
                    "ticker": amount_ranking[0]["ticker"],
                    "name": amount_ranking[0]["name"],
                    "amount": amount_ranking[0]["total_amount"],
                }

            summary = {
                "date": date.strftime("%Y-%m-%d"),
                "total_etfs": len(all_etfs),
                "total_stocks": unique_stocks,
                "total_holdings": len(all_holdings),
                "avg_holdings_per_etf": round(avg_holdings, 2),
                "most_common_stock": most_common,
                "highest_amount_stock": highest_amount,
            }

            return Result.ok(summary)
        except Exception as e:
            self.logger.error(f"Failed to get statistics summary: {e}", exc_info=True)
            return Result.fail("통계 요약 조회 실패")

    def get_weight_distribution(self, date: Optional[datetime] = None) -> Result[dict]:
        """비중 분포 통계를 조회합니다."""
        try:
            date = date or self.etf_repo.get_latest_date()
            if not date:
                return Result.fail("데이터가 없습니다")

            all_holdings = self.etf_repo.find_holdings_by_date(date)
            distribution = self.calculator.calculate_weight_distribution(all_holdings)

            result = {
                "date": date.strftime("%Y-%m-%d"),
                "total_holdings": len(all_holdings),
                "distribution": distribution,
            }

            return Result.ok(result)
        except Exception as e:
            self.logger.error(f"Failed to get weight distribution: {e}", exc_info=True)
            return Result.fail("비중 분포 조회 실패")
