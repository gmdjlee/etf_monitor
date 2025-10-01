"""
Market Data Adapter
시장 데이터 수집을 위한 어댑터 인터페이스입니다.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from domain.entities.etf import ETF
from domain.entities.holding import Holding
from domain.entities.stock import Stock


class MarketDataAdapter(ABC):
    """
    시장 데이터 어댑터 인터페이스

    외부 시장 데이터 소스로부터 데이터를 수집하는 추상 인터페이스입니다.
    Adapter 패턴을 사용하여 외부 의존성을 격리합니다.
    """

    @abstractmethod
    def collect_all_stocks(self) -> List[Stock]:
        """
        전체 주식 목록을 수집합니다.

        Returns:
            Stock 엔티티 리스트
        """
        pass

    @abstractmethod
    def collect_stocks_by_market(self, market: str) -> List[Stock]:
        """
        특정 시장의 주식 목록을 수집합니다.

        Args:
            market: 시장 코드 (예: KOSPI, KOSDAQ)

        Returns:
            Stock 엔티티 리스트
        """
        pass

    @abstractmethod
    def collect_etfs_for_date(self, date: datetime) -> List[ETF]:
        """
        특정 날짜의 ETF 목록을 수집합니다.

        Args:
            date: 기준일

        Returns:
            ETF 엔티티 리스트
        """
        pass

    @abstractmethod
    def collect_holdings_for_date(
        self, etf_ticker: str, date: datetime
    ) -> List[Holding]:
        """
        특정 ETF의 특정 날짜 보유 종목을 수집합니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일

        Returns:
            Holding 엔티티 리스트
        """
        pass

    @abstractmethod
    def is_business_day(self, date: datetime) -> bool:
        """
        특정 날짜가 영업일인지 확인합니다.

        Args:
            date: 확인할 날짜

        Returns:
            영업일 여부
        """
        pass

    @abstractmethod
    def get_stock_name(self, ticker: str) -> str:
        """
        종목 코드로 종목명을 조회합니다.

        Args:
            ticker: 종목 코드

        Returns:
            종목명
        """
        pass

    @abstractmethod
    def get_etf_name(self, ticker: str) -> str:
        """
        ETF 코드로 ETF명을 조회합니다.

        Args:
            ticker: ETF 코드

        Returns:
            ETF명
        """
        pass
