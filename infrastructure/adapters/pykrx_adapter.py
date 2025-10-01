"""
PyKRX Adapter
PyKRX 라이브러리를 사용한 시장 데이터 어댑터 구현체입니다.
"""

import time
from datetime import datetime
from typing import List, Optional

import pandas as pd
from config.logging_config import LoggerMixin
from config.settings import market_settings, settings
from domain.entities.etf import ETF
from domain.entities.holding import Holding
from domain.entities.stock import Stock
from pykrx import stock
from shared.exceptions import ExternalAPIException
from shared.utils.date_utils import to_krx_format

from infrastructure.adapters.market_data_adapter import MarketDataAdapter


class PyKRXAdapter(MarketDataAdapter, LoggerMixin):
    """PyKRX 라이브러리를 사용한 시장 데이터 어댑터"""

    def __init__(self):
        self.api_delay = settings.API_DELAY_SECONDS
        self.retry_max = settings.RETRY_MAX_ATTEMPTS
        self.retry_delay = settings.RETRY_DELAY_SECONDS

    def collect_all_stocks(self) -> List[Stock]:
        """전체 주식 목록을 수집합니다."""
        try:
            self.logger.info("Collecting all stocks from all markets")

            all_stocks = []
            # today = to_krx_format(datetime.now())

            for market in market_settings.MARKETS:
                self.logger.debug("Collecting stocks from market: %s", market)

                stocks = self.collect_stocks_by_market(market)
                all_stocks.extend(stocks)

                time.sleep(self.api_delay)

            self.logger.info("Collected total stocks: %d", len(all_stocks))
            return all_stocks

        except Exception as e:
            self.logger.error("Failed to collect all stocks: %s", str(e), exc_info=True)
            raise ExternalAPIException("PyKRX", str(e))

    def collect_stocks_by_market(self, market: str) -> List[Stock]:
        """특정 시장의 주식 목록을 수집합니다."""
        try:
            today = to_krx_format(datetime.now())

            # 재시도 로직
            for attempt in range(self.retry_max):
                try:
                    tickers = stock.get_market_ticker_list(today, market=market)
                    break
                except Exception as e:
                    if attempt < self.retry_max - 1:
                        self.logger.warning(
                            "Retry %d/%d for market %s",
                            attempt + 1,
                            self.retry_max,
                            market,
                        )
                        time.sleep(self.retry_delay)
                    else:
                        raise e

            stocks = []
            for ticker in tickers:
                try:
                    # ✅ 수정: 안전하게 종목명 가져오기
                    name = self._safe_get_stock_name(ticker)
                    if name:
                        stocks.append(Stock.create(ticker=ticker, name=name))

                    time.sleep(self.api_delay)

                except Exception as e:
                    self.logger.warning(
                        "Failed to get stock name for ticker %s: %s", ticker, str(e)
                    )
                    continue

            self.logger.info("Collected %d stocks from %s", len(stocks), market)
            return stocks

        except Exception as e:
            self.logger.error(
                "Failed to collect stocks from market %s: %s",
                market,
                str(e),
                exc_info=True,
            )
            raise ExternalAPIException("PyKRX", str(e))

    def _safe_get_stock_name(self, ticker: str) -> Optional[str]:
        """
        ✅ 추가: 안전하게 종목명을 가져옵니다.

        Args:
            ticker: 종목 코드

        Returns:
            종목명, 실패 시 None
        """
        try:
            name = stock.get_market_ticker_name(ticker)
            if name and isinstance(name, str) and name.strip():
                return name.strip()
            return None
        except Exception as e:
            self.logger.debug("Could not get name for ticker %s: %s", ticker, str(e))
            return None

    def collect_etfs_for_date(self, date: datetime) -> List[ETF]:
        """특정 날짜의 ETF 목록을 수집합니다."""
        try:
            date_str = to_krx_format(date)
            self.logger.debug("Collecting ETFs for date: %s", date_str)

            # 재시도 로직
            for attempt in range(self.retry_max):
                try:
                    tickers = stock.get_etf_ticker_list(date_str)
                    break
                except Exception as e:
                    if attempt < self.retry_max - 1:
                        self.logger.warning(
                            "Retry %d/%d for ETF list", attempt + 1, self.retry_max
                        )
                        time.sleep(self.retry_delay)
                    else:
                        raise e

            etfs = []
            for ticker in tickers:
                try:
                    # ✅ 수정: 안전하게 ETF명 가져오기
                    name = self._safe_get_etf_name(ticker)
                    if name:
                        etfs.append(ETF.create(ticker=ticker, name=name))

                    time.sleep(self.api_delay)

                except Exception as e:
                    self.logger.warning(
                        "Failed to get ETF name for ticker %s: %s", ticker, str(e)
                    )
                    continue

            self.logger.info("Collected %d ETFs for %s", len(etfs), date_str)
            return etfs

        except Exception as e:
            self.logger.error("Failed to collect ETFs: %s", str(e), exc_info=True)
            raise ExternalAPIException("PyKRX", str(e))

    def _safe_get_etf_name(self, ticker: str) -> Optional[str]:
        """
        ✅ 추가: 안전하게 ETF명을 가져옵니다.

        Args:
            ticker: ETF 코드

        Returns:
            ETF명, 실패 시 None
        """
        try:
            name = stock.get_etf_ticker_name(ticker)
            if name and isinstance(name, str) and name.strip():
                return name.strip()
            return None
        except Exception as e:
            self.logger.debug(
                "Could not get name for ETF ticker %s: %s", ticker, str(e)
            )
            return None

    def collect_holdings_for_date(
        self, etf_ticker: str, date: datetime
    ) -> List[Holding]:
        """특정 ETF의 특정 날짜 보유 종목을 수집합니다."""
        try:
            date_str = to_krx_format(date)

            # 재시도 로직
            for attempt in range(self.retry_max):
                try:
                    df = stock.get_etf_portfolio_deposit_file(etf_ticker, date_str)
                    break
                except Exception as e:
                    if attempt < self.retry_max - 1:
                        self.logger.warning(
                            "Retry %d/%d for holdings", attempt + 1, self.retry_max
                        )
                        time.sleep(self.retry_delay)
                    else:
                        raise e

            if df.empty:
                self.logger.debug("No holdings data for %s on %s", etf_ticker, date_str)
                return []

            # '비중' 컬럼이 없으면 빈 리스트 반환
            if "비중" not in df.columns:
                self.logger.warning(
                    "No weight column for %s on %s", etf_ticker, date_str
                )
                return []

            holdings = []
            for stock_ticker, row in df.iterrows():
                try:
                    # 평가금액 처리
                    amount = 0.0
                    if "금액" in df.columns:
                        amount = float(row["금액"]) if pd.notna(row["금액"]) else 0.0

                    # ✅ 수정: 종목명 안전하게 가져오기
                    stock_name = self._get_holding_stock_name(
                        df, row, str(stock_ticker)
                    )

                    holding = Holding.create(
                        etf_ticker=etf_ticker,
                        stock_ticker=str(stock_ticker),
                        date=date,
                        weight=float(row["비중"]),
                        amount=amount,
                        stock_name=stock_name,
                    )
                    holdings.append(holding)

                except Exception as e:
                    self.logger.warning(
                        "Failed to create holding for ticker %s: %s",
                        stock_ticker,
                        str(e),
                    )
                    continue

            self.logger.debug(
                "Collected %d holdings for %s on %s",
                len(holdings),
                etf_ticker,
                date_str,
            )
            return holdings

        except Exception as e:
            self.logger.error(
                "Failed to collect holdings for %s: %s",
                etf_ticker,
                str(e),
                exc_info=True,
            )
            raise ExternalAPIException("PyKRX", str(e))

    def _get_holding_stock_name(
        self, df: pd.DataFrame, row: pd.Series, stock_ticker: str
    ) -> str:
        """
        ✅ 추가: Holdings의 종목명을 안전하게 가져옵니다.

        우선순위:
        1. DataFrame의 '종목명' 컬럼
        2. PyKRX API로 조회
        3. 티커를 이름으로 사용
        """
        # 1. DataFrame에서 시도
        if "종목명" in df.columns and pd.notna(row["종목명"]):
            name = str(row["종목명"]).strip()
            if name:
                return name

        # 2. PyKRX API로 시도
        try:
            name = self._safe_get_stock_name(stock_ticker)
            if name:
                return name
        except:
            pass

        # 3. 티커를 이름으로 사용
        return stock_ticker

    def is_business_day(self, date: datetime) -> bool:
        """특정 날짜가 영업일인지 확인합니다."""
        try:
            # 주말 확인
            if date.weekday() >= 5:
                return False

            # 대표 종목(삼성전자)의 시세 조회로 영업일 확인
            date_str = to_krx_format(date)

            try:
                df = stock.get_market_ohlcv(
                    date_str, date_str, market_settings.REFERENCE_TICKER
                )
                return not df.empty
            except Exception:
                return False

        except Exception as e:
            self.logger.warning("Failed to check business day: %s", str(e))
            return False

    def get_stock_name(self, ticker: str) -> str:
        """종목 코드로 종목명을 조회합니다."""
        # ✅ 수정: 안전한 메서드 사용
        name = self._safe_get_stock_name(ticker)
        if name:
            return name

        # 실패 시 예외 발생
        raise ExternalAPIException("PyKRX", f"Could not get stock name for {ticker}")

    def get_etf_name(self, ticker: str) -> str:
        """ETF 코드로 ETF명을 조회합니다."""
        # ✅ 수정: 안전한 메서드 사용
        name = self._safe_get_etf_name(ticker)
        if name:
            return name

        # 실패 시 예외 발생
        raise ExternalAPIException("PyKRX", f"Could not get ETF name for {ticker}")
