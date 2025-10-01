"""
Initialize System Use Case
시스템 초기화 유스케이스입니다.
"""

from datetime import datetime, timedelta
from typing import List

from config.logging_config import LoggerMixin
from config.settings import settings
from domain.entities.stock import Stock
from domain.repositories.config_repository import ConfigRepository
from domain.repositories.etf_repository import ETFRepository
from domain.repositories.stock_repository import StockRepository
from domain.services.etf_filter_service import ETFFilterService
from domain.value_objects.date_range import DateRange
from domain.value_objects.filter_criteria import FilterCriteria
from infrastructure.adapters.market_data_adapter import MarketDataAdapter
from shared.exceptions import ApplicationException
from shared.result import Result


class InitializeSystemUseCase(LoggerMixin):
    """시스템 초기화 유스케이스"""

    def __init__(
        self,
        etf_repository: ETFRepository,
        stock_repository: StockRepository,
        config_repository: ConfigRepository,
        market_data_adapter: MarketDataAdapter,
        filter_service: ETFFilterService,
    ):
        self.etf_repo = etf_repository
        self.stock_repo = stock_repository
        self.config_repo = config_repository
        self.market_adapter = market_data_adapter
        self.filter_service = filter_service

    def execute(self) -> Result[dict]:
        """시스템 초기화를 실행합니다."""
        try:
            self.logger.info("Starting system initialization")

            # 1. DB가 이미 초기화되어 있는지 확인
            if not self._is_initialization_needed():
                self.logger.info("System already initialized")
                return Result.ok(
                    {
                        "initialized": False,
                        "stocks_collected": 0,
                        "etfs_collected": 0,
                        "days_collected": 0,
                        "message": "이미 데이터베이스가 존재합니다.",
                    }
                )

            # 2. 기본 설정 로드
            self.logger.info("Loading default configuration")
            self._load_default_config()

            # 3. 전체 주식 목록 수집
            self.logger.info("Collecting all stocks")
            stocks_count = self._collect_all_stocks()

            # 4. 초기 ETF 데이터 수집
            self.logger.info(
                f"Collecting ETF data for {settings.DEFAULT_COLLECT_DAYS} days"
            )
            etfs_count, days_count = self._collect_initial_etf_data()

            result = {
                "initialized": True,
                "stocks_collected": stocks_count,
                "etfs_collected": etfs_count,
                "days_collected": days_count,
                "message": f"초기화 완료: {stocks_count}개 주식, {etfs_count}개 ETF, {days_count}일치 데이터 수집",
            }

            self.logger.info(f"Initialization completed: {result}")
            return Result.ok(result)

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return Result.fail(f"초기화 중 오류가 발생했습니다: {str(e)}")

    def _is_initialization_needed(self) -> bool:
        """초기화가 필요한지 확인"""
        etf_count = self.etf_repo.count()
        return etf_count == 0

    def _load_default_config(self) -> None:
        """기본 설정을 로드합니다."""
        existing_themes = self.config_repo.get_all_themes()
        if not existing_themes:
            self.logger.debug(f"Adding {len(settings.DEFAULT_THEMES)} default themes")
            self.config_repo.set_themes(settings.DEFAULT_THEMES)

        existing_exclusions = self.config_repo.get_all_exclusions()
        if not existing_exclusions:
            self.logger.debug(
                f"Adding {len(settings.DEFAULT_EXCLUSIONS)} default exclusions"
            )
            self.config_repo.set_exclusions(settings.DEFAULT_EXCLUSIONS)

    def _collect_all_stocks(self) -> int:
        """전체 주식 목록을 수집합니다."""
        try:
            stocks = self.market_adapter.collect_all_stocks()

            if stocks:
                self.stock_repo.save_all(stocks)
                self.logger.info(f"Collected {len(stocks)} stocks")
                return len(stocks)
            else:
                self.logger.warning("No stocks collected")
                return 0

        except Exception as e:
            self.logger.error(f"Failed to collect stocks: {e}")
            raise ApplicationException(f"주식 목록 수집 실패: {str(e)}")

    def _collect_initial_etf_data(self) -> tuple[int, int]:
        """초기 ETF 데이터를 수집합니다."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=settings.DEFAULT_COLLECT_DAYS)
        date_range = DateRange.create(start_date, end_date)

        criteria = FilterCriteria.create(
            themes=self.config_repo.get_all_themes(),
            exclusions=self.config_repo.get_all_exclusions(),
            require_active=settings.REQUIRE_ACTIVE_KEYWORD,
        )

        collected_etfs = set()
        days_collected = 0

        business_days = date_range.business_days()

        for date in business_days:
            self.logger.debug(f"Collecting data for {date.strftime('%Y-%m-%d')}")

            try:
                if not self.market_adapter.is_business_day(date):
                    self.logger.debug(
                        f"{date.strftime('%Y-%m-%d')} is not a business day"
                    )
                    continue

                etfs_on_date = self._collect_etf_data_for_date(date, criteria)

                if etfs_on_date:
                    collected_etfs.update(etf.ticker for etf in etfs_on_date)
                    days_collected += 1
                    self.logger.info(
                        f"Collected {len(etfs_on_date)} ETFs for {date.strftime('%Y-%m-%d')}"
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to collect data for {date.strftime('%Y-%m-%d')}: {e}"
                )
                continue

        return len(collected_etfs), days_collected

    def _collect_etf_data_for_date(
        self, date: datetime, criteria: FilterCriteria
    ) -> List:
        """✅ 수정: 특정 날짜의 ETF 데이터를 수집합니다."""
        try:
            # 해당 날짜의 모든 ETF 수집
            all_etfs = self.market_adapter.collect_etfs_for_date(date)

            if not all_etfs:
                return []

            # 필터링
            filtered_etfs = self.filter_service.filter_etfs(all_etfs, criteria)

            # ETF 저장
            for etf in filtered_etfs:
                self.etf_repo.save(etf)

            # 각 ETF의 보유 종목 수집
            for etf in filtered_etfs:
                try:
                    holdings = self.market_adapter.collect_holdings_for_date(
                        etf.ticker, date
                    )

                    if holdings:
                        # ✅ 추가: Holdings 저장 전에 종목 정보 먼저 저장
                        unique_stocks = {}
                        for holding in holdings:
                            if holding.stock_ticker not in unique_stocks:
                                stock = Stock.create(
                                    ticker=holding.stock_ticker,
                                    name=holding.stock_name or holding.stock_ticker,
                                )
                                unique_stocks[holding.stock_ticker] = stock

                        # 종목 정보 먼저 저장 (INSERT OR IGNORE로 중복 무시)
                        if unique_stocks:
                            self.stock_repo.save_all(list(unique_stocks.values()))
                            self.logger.debug(
                                f"Ensured {len(unique_stocks)} stocks exist for {etf.ticker}"
                            )

                        # 이제 Holdings 저장
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
            self.logger.error(f"Failed to collect ETF data for date: {e}")
            raise ApplicationException(f"데이터 수집 실패: {str(e)}")
