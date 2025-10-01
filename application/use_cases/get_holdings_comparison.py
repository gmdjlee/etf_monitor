"""
Get Holdings Comparison Use Case (개선됨)
보유 종목 비교 조회 유스케이스입니다.
✅ 중복 Query 생성 제거
"""

from datetime import datetime
from typing import Optional

from config.logging_config import LoggerMixin
from domain.repositories.etf_repository import ETFRepository
from shared.exceptions import EntityNotFoundException
from shared.result import Result

from application.dto.holdings_dto import HoldingsComparisonResultDto
from application.queries.holdings_comparison_query import HoldingsComparisonQuery


class GetHoldingsComparisonUseCase(LoggerMixin):
    """
    보유 종목 비교 조회 유스케이스

    특정 ETF의 두 시점 간 보유 종목을 비교하여 변화를 조회합니다.

    ✅ 개선: Query를 직접 생성하지 않고 주입받음 (단일 책임 원칙)

    Args:
        etf_repository: ETF 리포지토리
        holdings_comparison_query: 보유 종목 비교 쿼리 (주입)
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        holdings_comparison_query: HoldingsComparisonQuery,  # ✅ 주입받기
    ):
        self.etf_repo = etf_repository
        self.query = holdings_comparison_query  # ✅ 중복 생성 제거

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

            # ✅ 주입받은 쿼리 실행
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

            # 상위 N개 추출 (비중 기준 정렬)
            top_holdings = sorted(holdings, key=lambda h: h.weight, reverse=True)[
                :top_n
            ]

            # 집중도 계산
            concentration = sum(h.weight for h in top_holdings)

            result = {
                "etf_ticker": etf_ticker,
                "date": date.strftime("%Y-%m-%d"),
                "top_n": top_n,
                "holdings": [
                    {
                        "stock_ticker": h.stock_ticker,
                        "stock_name": h.stock_name,
                        "weight": h.weight,
                        "amount": h.amount,
                    }
                    for h in top_holdings
                ],
                "concentration_ratio": round(concentration, 2),
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
            total_weight = sum(h.weight for h in holdings)
            total_amount = sum(h.amount for h in holdings)

            # 상위 10개 비중 합계
            top_10 = sorted(holdings, key=lambda h: h.weight, reverse=True)[:10]
            top_10_concentration = sum(h.weight for h in top_10)

            # 유의미한 비중(1% 이상) 종목 수
            significant_holdings = [h for h in holdings if h.weight >= 1.0]

            # 비중 범위별 분류
            weight_groups = {
                "large": [h for h in holdings if h.weight >= 5.0],
                "medium": [h for h in holdings if 1.0 <= h.weight < 5.0],
                "small": [h for h in holdings if h.weight < 1.0],
            }

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
