"""
Export Data Use Case
데이터 내보내기 유스케이스입니다.
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd
from application.queries.holdings_comparison_query import HoldingsComparisonQuery
from config.logging_config import LoggerMixin
from config.settings import settings
from domain.repositories.etf_repository import ETFRepository
from shared.exceptions import EntityNotFoundException
from shared.result import Result


class ExportDataUseCase(LoggerMixin):
    """
    데이터 내보내기 유스케이스

    ETF 보유 종목 정보를 CSV 파일로 내보냅니다.

    Args:
        etf_repository: ETF 리포지토리
        holdings_query: 보유 종목 조회 쿼리
    """

    def __init__(
        self, etf_repository: ETFRepository, holdings_query: HoldingsComparisonQuery
    ):
        self.etf_repo = etf_repository
        self.holdings_query = holdings_query

    def export_holdings_to_csv(
        self, etf_ticker: str, date: Optional[datetime] = None
    ) -> Result[str]:
        """
        ETF 보유 종목을 CSV 파일로 내보냅니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일 (None이면 최신)

        Returns:
            Result[str]: 생성된 파일 경로
        """
        try:
            self.logger.info(f"Exporting holdings to CSV for ETF: {etf_ticker}")

            # ETF 존재 확인
            etf = self.etf_repo.find_by_ticker(etf_ticker)
            if not etf:
                raise EntityNotFoundException("ETF", etf_ticker)

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

            # DataFrame 생성
            data = []
            for holding in holdings:
                data.append(
                    {
                        "종목코드": holding.stock_ticker,
                        "종목명": holding.stock_name,
                        "비중(%)": holding.weight,
                        "평가금액(원)": holding.amount,
                        "평가금액(억원)": round(holding.amount / 100_000_000, 2),
                    }
                )

            df = pd.DataFrame(data)

            # 비중 기준으로 정렬
            df = df.sort_values(by="비중(%)", ascending=False)

            # 파일 경로 생성
            file_path = self._generate_file_path(etf_ticker, etf.name, date)

            # CSV 저장
            df.to_csv(file_path, index=False, encoding=settings.CSV_ENCODING)

            self.logger.info(f"CSV exported successfully: {file_path}")

            return Result.ok(file_path)

        except EntityNotFoundException as e:
            self.logger.warning(f"Entity not found: {e}")
            return Result.fail(f"ETF를 찾을 수 없습니다: {etf_ticker}")

        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}", exc_info=True)
            return Result.fail(f"CSV 내보내기 실패: {str(e)}")

    def export_comparison_to_csv(
        self,
        etf_ticker: str,
        current_date: Optional[datetime] = None,
        previous_date: Optional[datetime] = None,
    ) -> Result[str]:
        """
        ETF 보유 종목 비교 결과를 CSV 파일로 내보냅니다.

        Args:
            etf_ticker: ETF 코드
            current_date: 현재 날짜 (None이면 최신)
            previous_date: 이전 날짜 (None이면 current_date의 이전)

        Returns:
            Result[str]: 생성된 파일 경로
        """
        try:
            self.logger.info(
                f"Exporting holdings comparison to CSV for ETF: {etf_ticker}"
            )

            # ETF 존재 확인
            etf = self.etf_repo.find_by_ticker(etf_ticker)
            if not etf:
                raise EntityNotFoundException("ETF", etf_ticker)

            # 비교 결과 조회
            comparison_result = self.holdings_query.execute(
                etf_ticker=etf_ticker,
                current_date=current_date,
                previous_date=previous_date,
            )

            # DataFrame 생성
            data = []
            for item in comparison_result.comparison:
                data.append(
                    {
                        "종목코드": item.stock_ticker,
                        "종목명": item.stock_name,
                        f"이전 비중(%) [{comparison_result.prev_date}]": item.prev_weight,
                        f"현재 비중(%) [{comparison_result.current_date}]": item.current_weight,
                        "변동(%)": item.change,
                        "평가금액(원)": item.current_amount,
                        "평가금액(억원)": round(item.current_amount / 100_000_000, 2),
                        "상태": item.status,
                    }
                )

            df = pd.DataFrame(data)

            # 현재 비중 기준으로 정렬
            df = df.sort_values(
                by=f"현재 비중(%) [{comparison_result.current_date}]", ascending=False
            )

            # 파일 경로 생성
            file_name = (
                f"{etf_ticker}_{etf.name}_"
                f"비교_{comparison_result.prev_date}_vs_{comparison_result.current_date}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            file_path = os.path.join(settings.EXPORT_DIR, file_name)

            # CSV 저장
            df.to_csv(file_path, index=False, encoding=settings.CSV_ENCODING)

            self.logger.info(f"Comparison CSV exported successfully: {file_path}")

            return Result.ok(file_path)

        except EntityNotFoundException as e:
            self.logger.warning(f"Entity not found: {e}")
            return Result.fail(f"ETF를 찾을 수 없습니다: {etf_ticker}")

        except Exception as e:
            self.logger.error(f"Failed to export comparison CSV: {e}", exc_info=True)
            return Result.fail(f"CSV 내보내기 실패: {str(e)}")

    def _generate_file_path(
        self, etf_ticker: str, etf_name: str, date: datetime
    ) -> str:
        """CSV 파일 경로를 생성합니다."""
        # 파일명에서 사용할 수 없는 문자 제거
        safe_name = etf_name.replace("/", "_").replace("\\", "_")

        file_name = (
            f"{etf_ticker}_{safe_name}_"
            f"{date.strftime('%Y%m%d')}_"
            f"{datetime.now().strftime('%H%M%S')}.csv"
        )

        return os.path.join(settings.EXPORT_DIR, file_name)

    def cleanup_old_exports(self, days: int = 7) -> Result[int]:
        """
        오래된 내보내기 파일을 정리합니다.

        Args:
            days: 보관 일수

        Returns:
            Result[int]: 삭제된 파일 개수
        """
        try:
            self.logger.info(f"Cleaning up exports older than {days} days")

            if not os.path.exists(settings.EXPORT_DIR):
                return Result.ok(0)

            cutoff_time = datetime.now().timestamp() - (days * 86400)
            deleted_count = 0

            for filename in os.listdir(settings.EXPORT_DIR):
                file_path = os.path.join(settings.EXPORT_DIR, filename)

                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)

                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.debug(f"Deleted old export: {filename}")

            self.logger.info(f"Cleaned up {deleted_count} old export files")

            return Result.ok(deleted_count)

        except Exception as e:
            self.logger.error(f"Failed to cleanup exports: {e}", exc_info=True)
            return Result.fail(f"파일 정리 실패: {str(e)}")
