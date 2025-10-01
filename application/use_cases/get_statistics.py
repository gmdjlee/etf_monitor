"""
Get Statistics Use Case
통계 조회 유스케이스입니다.
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

    중복 종목, 평가금액 순위, 테마별 통계 등을 조회합니다.

    Args:
        etf_repository: ETF 리포지토리
        statistics_calculator: 통계 계산 서비스
        stock_statistics_query: 통계 쿼리 (의존성 주입)
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        statistics_calculator: StatisticsCalculator,
        stock_statistics_query: StockStatisticsQuery,  # ✅ 추가: 의존성 주입
    ):
        self.etf_repo = etf_repository
        self.calculator = statistics_calculator
        self.query = stock_statistics_query  # ✅ 수정: 주입받은 Query 사용

    def get_duplicate_stocks(
        self, date: Optional[datetime] = None, min_count: int = 2, limit: int = 100
    ) -> Result[DuplicateStockStatsDto]:
        """
        중복 종목 통계를 조회합니다.

        Args:
            date: 기준일 (None이면 최신)
            min_count: 최소 중복 횟수
            limit: 최대 반환 개수

        Returns:
            Result[DuplicateStockStatsDto]: 중복 종목 통계
        """
        try:
            self.logger.info(
                f"Getting duplicate stocks statistics (min_count={min_count}, limit={limit})"
            )

            result_dto = self.query.get_duplicate_stocks(
                date=date, min_count=min_count, limit=limit
            )

            self.logger.info(f"Found {len(result_dto.stocks)} duplicate stocks")

            return Result.ok(result_dto)

        except ValueError as e:
            self.logger.warning(f"Invalid request: {e}")
            return Result.fail(str(e))

        except Exception as e:
            self.logger.error(f"Failed to get duplicate stocks: {e}", exc_info=True)
            return Result.fail(f"중복 종목 통계 조회 실패: {str(e)}")

    def get_amount_ranking(
        self, date: Optional[datetime] = None, top_n: int = 100
    ) -> Result[AmountRankingStatsDto]:
        """
        평가금액 순위를 조회합니다.

        Args:
            date: 기준일 (None이면 최신)
            top_n: 상위 N개

        Returns:
            Result[AmountRankingStatsDto]: 평가금액 순위
        """
        try:
            self.logger.info(f"Getting amount ranking (top_n={top_n})")

            result_dto = self.query.get_amount_ranking(date=date, top_n=top_n)

            self.logger.info(f"Found {len(result_dto.stocks)} stocks in amount ranking")

            return Result.ok(result_dto)

        except ValueError as e:
            self.logger.warning(f"Invalid request: {e}")
            return Result.fail(str(e))

        except Exception as e:
            self.logger.error(f"Failed to get amount ranking: {e}", exc_info=True)
            return Result.fail(f"평가금액 순위 조회 실패: {str(e)}")

    def get_theme_statistics(
        self, theme: str, date: Optional[datetime] = None, limit: int = 100
    ) -> Result[ThemeStatsDto]:
        """
        특정 테마의 통계를 조회합니다.

        Args:
            theme: 테마 키워드
            date: 기준일 (None이면 최신)
            limit: 최대 반환 개수

        Returns:
            Result[ThemeStatsDto]: 테마 통계
        """
        try:
            self.logger.info(f"Getting theme statistics for: {theme}")

            result_dto = self.query.get_theme_statistics(
                theme=theme, date=date, limit=limit
            )

            self.logger.info(
                f"Theme '{theme}': {result_dto.etf_count} ETFs, "
                f"{result_dto.unique_stocks} unique stocks"
            )

            return Result.ok(result_dto)

        except ValueError as e:
            self.logger.warning(f"Invalid request: {e}")
            return Result.fail(str(e))

        except Exception as e:
            self.logger.error(f"Failed to get theme statistics: {e}", exc_info=True)
            return Result.fail(f"테마 통계 조회 실패: {str(e)}")

    def get_statistics_summary(self, date: Optional[datetime] = None) -> Result[dict]:
        """
        전체 통계 요약 정보를 조회합니다.

        Args:
            date: 기준일 (None이면 최신)

        Returns:
            Result[dict]: 통계 요약
        """
        try:
            self.logger.info("Getting statistics summary")

            # 날짜 결정
            if date is None:
                date = self.etf_repo.get_latest_date()
                if not date:
                    return Result.fail("데이터가 없습니다")

            # 전체 ETF와 보유 종목 조회
            all_etfs = self.etf_repo.find_all()
            all_holdings = self.etf_repo.find_holdings_by_date(date)

            # 고유 종목 수 계산
            unique_stocks = len(set(h.stock_ticker for h in all_holdings))

            # ETF당 평균 보유 종목 수
            avg_holdings = len(all_holdings) / len(all_etfs) if all_etfs else 0

            # 가장 많은 ETF에 포함된 종목
            stock_frequency = self.calculator.get_top_stocks_by_frequency(
                all_holdings, top_n=1
            )
            most_common = None
            if stock_frequency:
                ticker, freq = stock_frequency[0]
                # 종목명 조회
                holdings_with_name = [
                    h for h in all_holdings if h.stock_ticker == ticker and h.stock_name
                ]
                stock_name = (
                    holdings_with_name[0].stock_name if holdings_with_name else ticker
                )
                most_common = {"ticker": ticker, "name": stock_name, "frequency": freq}

            # 평가금액이 가장 높은 종목
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
            return Result.fail(f"통계 요약 조회 실패: {str(e)}")

    def get_weight_distribution(self, date: Optional[datetime] = None) -> Result[dict]:
        """
        비중 분포 통계를 조회합니다.

        Args:
            date: 기준일 (None이면 최신)

        Returns:
            Result[dict]: 비중 분포
        """
        try:
            self.logger.info("Getting weight distribution")

            # 날짜 결정
            if date is None:
                date = self.etf_repo.get_latest_date()
                if not date:
                    return Result.fail("데이터가 없습니다")

            # 모든 보유 종목 조회
            all_holdings = self.etf_repo.find_holdings_by_date(date)

            # 비중 분포 계산
            distribution = self.calculator.calculate_weight_distribution(all_holdings)

            result = {
                "date": date.strftime("%Y-%m-%d"),
                "total_holdings": len(all_holdings),
                "distribution": distribution,
            }

            return Result.ok(result)

        except Exception as e:
            self.logger.error(f"Failed to get weight distribution: {e}", exc_info=True)
            return Result.fail(f"비중 분포 조회 실패: {str(e)}")
