"""
Update ETF Data Use Case
ETF 데이터 업데이트 유스케이스입니다.
"""

from datetime import datetime, timedelta
from typing import List, Set

from config.logging_config import LoggerMixin
from domain.repositories.config_repository import ConfigRepository
from domain.repositories.etf_repository import ETFRepository
from domain.services.etf_filter_service import ETFFilterService
from domain.value_objects.date_range import DateRange
from domain.value_objects.filter_criteria import FilterCriteria
from infrastructure.adapters.market_data_adapter import MarketDataAdapter
from shared.exceptions import ApplicationException
from shared.result import Result


class UpdateETFDataUseCase(LoggerMixin):
    """
    ETF 데이터 업데이트 유스케이스

    최신 날짜부터 현재까지의 데이터를 수집하여 업데이트합니다.

    Args:
        etf_repository: ETF 리포지토리
        config_repository: Config 리포지토리
        market_data_adapter: 시장 데이터 어댑터
        filter_service: ETF 필터링 서비스
    """

    def __init__(
        self,
        etf_repository: ETFRepository,
        config_repository: ConfigRepository,
        market_data_adapter: MarketDataAdapter,
        filter_service: ETFFilterService,
    ):
        self.etf_repo = etf_repository
        self.config_repo = config_repository
        self.market_adapter = market_data_adapter
        self.filter_service = filter_service

    def execute(self) -> Result[dict]:
        """
        데이터 업데이트를 실행합니다.

        Returns:
            Result[dict]: 업데이트 결과
            {
                'updated': bool,
                'etfs_updated': int,
                'days_updated': int,
                'start_date': str,
                'end_date': str,
                'message': str
            }
        """
        try:
            self.logger.info("Starting ETF data update")

            # 1. 최신 날짜 확인
            latest_date = self.etf_repo.get_latest_date()
            if not latest_date:
                return Result.fail("데이터가 없습니다. 먼저 초기화를 진행해주세요.")

            # 2. 업데이트할 날짜 범위 결정
            start_date = latest_date + timedelta(days=1)
            end_date = datetime.now()

            # 업데이트할 날짜가 없는 경우
            if start_date > end_date:
                self.logger.info("Already up to date")
                return Result.ok(
                    {
                        "updated": False,
                        "etfs_updated": 0,
                        "days_updated": 0,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "message": "이미 최신 데이터입니다.",
                    }
                )

            self.logger.info(
                f"Updating data from {start_date.strftime('%Y-%m-%d')} "
                f"to {end_date.strftime('%Y-%m-%d')}"
            )

            # 3. 데이터 업데이트 수행
            etfs_updated, days_updated = self._update_data_range(start_date, end_date)

            result = {
                "updated": True,
                "etfs_updated": etfs_updated,
                "days_updated": days_updated,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "message": f"{days_updated}일치 데이터 업데이트 완료 ({etfs_updated}개 ETF)",
            }

            self.logger.info(f"Update completed: {result}")
            return Result.ok(result)

        except Exception as e:
            self.logger.error(f"Update failed: {e}", exc_info=True)
            return Result.fail(f"데이터 업데이트 중 오류가 발생했습니다: {str(e)}")

    def _update_data_range(
        self, start_date: datetime, end_date: datetime
    ) -> tuple[int, int]:
        """
        날짜 범위의 데이터를 업데이트합니다.

        Returns:
            (업데이트된 ETF 개수, 업데이트된 일수)
        """
        date_range = DateRange.create(start_date, end_date)

        # 필터 조건 생성
        criteria = FilterCriteria.create(
            themes=self.config_repo.get_all_themes(),
            exclusions=self.config_repo.get_all_exclusions(),
            require_active=True,
        )

        updated_etfs: Set[str] = set()
        days_updated = 0

        # 영업일만 업데이트
        business_days = date_range.business_days()

        for date in business_days:
            self.logger.debug(f"Updating data for {date.strftime('%Y-%m-%d')}")

            try:
                # 해당 날짜가 영업일인지 확인
                if not self.market_adapter.is_business_day(date):
                    self.logger.debug(
                        f"{date.strftime('%Y-%m-%d')} is not a business day"
                    )
                    continue

                # 해당 날짜의 데이터 수집
                etfs_on_date = self._collect_and_save_for_date(date, criteria)

                if etfs_on_date:
                    updated_etfs.update(etf.ticker for etf in etfs_on_date)
                    days_updated += 1
                    self.logger.info(
                        f"Updated {len(etfs_on_date)} ETFs for {date.strftime('%Y-%m-%d')}"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to update data for {date.strftime('%Y-%m-%d')}: {e}"
                )
                continue

        return len(updated_etfs), days_updated

    def _collect_and_save_for_date(
        self, date: datetime, criteria: FilterCriteria
    ) -> List:
        """특정 날짜의 데이터를 수집하고 저장합니다."""
        try:
            # 해당 날짜의 모든 ETF 수집
            all_etfs = self.market_adapter.collect_etfs_for_date(date)

            if not all_etfs:
                return []

            # 필터링
            filtered_etfs = self.filter_service.filter_etfs(all_etfs, criteria)

            # 새로운 ETF 저장 (기존 ETF는 자동으로 무시됨)
            for etf in filtered_etfs:
                if not self.etf_repo.exists(etf.ticker):
                    self.etf_repo.save(etf)

            # 각 ETF의 보유 종목 수집
            for etf in filtered_etfs:
                try:
                    # 이미 해당 날짜의 데이터가 있는지 확인
                    existing_holdings = self.etf_repo.find_holdings_by_etf_and_date(
                        etf.ticker, date
                    )

                    if existing_holdings:
                        self.logger.debug(
                            f"Holdings already exist for {etf.ticker} on "
                            f"{date.strftime('%Y-%m-%d')}"
                        )
                        continue

                    # 보유 종목 수집
                    holdings = self.market_adapter.collect_holdings_for_date(
                        etf.ticker, date
                    )

                    if holdings:
                        self.etf_repo.save_holdings(holdings)
                        self.logger.debug(
                            f"Saved {len(holdings)} holdings for {etf.ticker}"
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to collect holdings for {etf.ticker}: {e}"
                    )
                    continue

            return filtered_etfs

        except Exception as e:
            self.logger.error(f"Failed to collect data for date: {e}")
            raise ApplicationException(f"데이터 수집 실패: {str(e)}")

    def force_update_date(self, date: datetime) -> Result[dict]:
        """
        특정 날짜의 데이터를 강제로 업데이트합니다.

        Args:
            date: 업데이트할 날짜

        Returns:
            Result[dict]: 업데이트 결과
        """
        try:
            self.logger.info(f"Force updating data for {date.strftime('%Y-%m-%d')}")

            # 기존 데이터 삭제
            self.etf_repo.delete_holdings_by_date(date)

            # 필터 조건 생성
            criteria = FilterCriteria.create(
                themes=self.config_repo.get_all_themes(),
                exclusions=self.config_repo.get_all_exclusions(),
                require_active=True,
            )

            # 데이터 수집
            etfs = self._collect_and_save_for_date(date, criteria)

            result = {
                "updated": True,
                "etfs_updated": len(etfs),
                "date": date.strftime("%Y-%m-%d"),
                "message": f"{date.strftime('%Y-%m-%d')} 데이터 강제 업데이트 완료",
            }

            return Result.ok(result)

        except Exception as e:
            self.logger.error(f"Force update failed: {e}", exc_info=True)
            return Result.fail(f"강제 업데이트 실패: {str(e)}")
