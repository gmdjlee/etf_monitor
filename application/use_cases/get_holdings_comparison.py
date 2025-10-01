"""
Get Holdings Comparison Use Case
보유 종목 비교 조회 유스케이스입니다.
"""

from datetime import datetime
from typing import Optional

from application.dto.holdings_dto import HoldingsComparisonResultDto
from application.queries.holdings_comparison_query import HoldingsComparisonQuery
from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from domain.repositories.stock_repository import StockRepository
from domain.services.holdings_analyzer import HoldingsAnalyzer
from shared.exceptions import EntityNotFoundException
from shared.result import Result


class GetHoldingsComparisonUseCase(LoggerMixin):
    """
    보유 종목 비교 조회 유스케이스

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
        self.query = HoldingsComparisonQuery(
            etf_repository, stock_repository, holdings_analyzer
        )

    def execute(
        self,
        etf_ticker: str,
        current_date: Optional[datetime] = None,
        previous_date: Optional[datetime] = None,
    ) -> Result[HoldingsComparisonResultDto]:
        """
        보유 종목 비교를 실행합니다.

        Args:
            etf_ticker: ETF 코드
            current_date: 현재 날짜 (None이면 최신)
            previous_date: 이전 날짜 (None이면 current_date의 이전)

        Returns:
            Result[HoldingsComparisonResultDto]: 비교 결과
        """
        try:
            self.logger.info(f"Getting holdings comparison for ETF: {etf_ticker}")

            # ETF 존재 확인
            etf = self.etf_repo.find_by_ticker(etf_ticker)
            if not etf:
                raise EntityNotFoundException("ETF", etf_ticker)

            # 쿼리 실행
            result_dto = self.query.execute(
                etf_ticker=etf_ticker,
                current_date=current_date,
                previous_date=previous_date,
            )

            self.logger.info(
                f"Comparison completed: {len(result_dto.comparison)} holdings"
            )

            return Result.ok(result_dto)

        except EntityNotFoundException as e:
            self.logger.warning(f"Entity not found: {e}")
            return Result.fail(f"ETF를 찾을 수 없습니다: {etf_ticker}")

        except ValueError as e:
            self.logger.warning(f"Invalid request: {e}")
            return Result.fail(str(e))

        except Exception as e:
            self.logger.error(f"Failed to get holdings comparison: {e}", exc_info=True)
            return Result.fail(f"보유 종목 비교 조회 실패: {str(e)}")

    def get_top_holdings(
        self, etf_ticker: str, date: Optional[datetime] = None, top_n: int = 10
    ) -> Result[dict]:
        """
        상위 N개 보유 종목을 조회합니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일 (None이면 최신)
            top_n: 상위 종목 개수

        Returns:
            Result[dict]: 상위 종목 정보
        """
        try:
            self.logger.info(f"Getting top {top_n} holdings for ETF: {etf_ticker}")

            # 날짜 결정
            if date is None:
                available_dates = self.etf_repo.get_available_dates(etf_ticker)
                if not available_dates:
                    return Result.fail(f"데이터가 없습니다: {etf_ticker}")
                date = available_dates[0]

            # 보유 종목 조회
            holdings = self.etf_repo.find_holdings_by_etf_and_date(etf_ticker, date)

            if not holdings:
                return Result.fail(
                    f"해당 날짜의 데이터가 없습니다: {date.strftime('%Y-%m-%d')}"
                )

            # 상위 N개 추출
            top_holdings = self.analyzer.get_top_holdings(holdings, top_n)

            # 집중도 계산
            concentration = self.analyzer.calculate_concentration_ratio(holdings, top_n)

            result = {
                "etf_ticker": etf_ticker,
                "date": date.strftime("%Y-%m-%d"),
                "top_n": top_n,
                "holdings": [h.to_dict() for h in top_holdings],
                "concentration_ratio": concentration,
                "total_holdings": len(holdings),
            }

            return Result.ok(result)

        except Exception as e:
            self.logger.error(f"Failed to get top holdings: {e}", exc_info=True)
            return Result.fail(f"상위 종목 조회 실패: {str(e)}")

    def get_holdings_summary(
        self, etf_ticker: str, date: Optional[datetime] = None
    ) -> Result[dict]:
        """
        보유 종목 요약 정보를 조회합니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일 (None이면 최신)

        Returns:
            Result[dict]: 요약 정보
        """
        try:
            self.logger.info(f"Getting holdings summary for ETF: {etf_ticker}")

            # 날짜 결정
            if date is None:
                available_dates = self.etf_repo.get_available_dates(etf_ticker)
                if not available_dates:
                    return Result.fail(f"데이터가 없습니다: {etf_ticker}")
                date = available_dates[0]

            # 보유 종목 조회
            holdings = self.etf_repo.find_holdings_by_etf_and_date(etf_ticker, date)

            if not holdings:
                return Result.fail(
                    f"해당 날짜의 데이터가 없습니다: {date.strftime('%Y-%m-%d')}"
                )

            # 통계 계산
            total_weight = self.analyzer.calculate_total_weight(holdings)
            total_amount = self.analyzer.calculate_total_amount(holdings)
            top_10_concentration = self.analyzer.calculate_concentration_ratio(
                holdings, 10
            )
            significant_holdings = self.analyzer.get_significant_holdings(holdings, 1.0)
            weight_groups = self.analyzer.group_by_weight_range(holdings)

            summary = {
                "etf_ticker": etf_ticker,
                "date": date.strftime("%Y-%m-%d"),
                "total_count": len(holdings),
                "total_weight": round(total_weight, 2),
                "total_amount": total_amount,
                "top_10_concentration": round(top_10_concentration, 2),
                "significant_count": len(significant_holdings),
                "weight_distribution": {
                    "large": len(weight_groups["large"]),
                    "medium": len(weight_groups["medium"]),
                    "small": len(weight_groups["small"]),
                },
            }

            return Result.ok(summary)

        except Exception as e:
            self.logger.error(f"Failed to get holdings summary: {e}", exc_info=True)
            return Result.fail(f"요약 정보 조회 실패: {str(e)}")
