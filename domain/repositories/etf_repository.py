"""
ETF Repository 인터페이스
ETF 데이터 접근을 위한 추상 인터페이스입니다.
"""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional

from domain.entities.etf import ETF
from domain.entities.holding import Holding
from domain.repositories.base import BaseRepository


class ETFRepository(BaseRepository[ETF, str]):
    """
    ETF 리포지토리 인터페이스

    ETF 엔티티와 보유 종목 정보의 영속성을 담당하는 추상 인터페이스입니다.
    Infrastructure 레이어에서 구체적으로 구현됩니다.

    식별자: ticker (str)
    """

    # ETF 기본 조회

    @abstractmethod
    def find_by_ticker(self, ticker: str) -> Optional[ETF]:
        """
        티커로 ETF를 조회합니다.

        Args:
            ticker: ETF 코드

        Returns:
            찾은 ETF 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[ETF]:
        """
        ETF명으로 조회합니다.

        Args:
            name: ETF명

        Returns:
            찾은 ETF 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_by_name_like(self, keyword: str) -> List[ETF]:
        """
        ETF명에 키워드가 포함된 ETF들을 조회합니다.

        Args:
            keyword: 검색 키워드

        Returns:
            매칭되는 ETF 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_active_etfs(self) -> List[ETF]:
        """
        액티브 ETF들을 조회합니다.

        Returns:
            액티브 ETF 엔티티 리스트
        """
        pass

    # 보유 종목(Holdings) 관련

    @abstractmethod
    def save_holding(self, holding: Holding) -> None:
        """
        보유 종목 정보를 저장합니다.

        Args:
            holding: 저장할 Holding 엔티티
        """
        pass

    @abstractmethod
    def save_holdings(self, holdings: List[Holding]) -> None:
        """
        여러 보유 종목 정보를 일괄 저장합니다.

        Args:
            holdings: 저장할 Holding 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_holdings_by_etf_and_date(
        self, etf_ticker: str, date: datetime
    ) -> List[Holding]:
        """
        특정 ETF의 특정 날짜 보유 종목을 조회합니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일

        Returns:
            Holding 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_holdings_by_stock_and_date(
        self, stock_ticker: str, date: datetime
    ) -> List[Holding]:
        """
        특정 종목을 보유한 모든 ETF를 특정 날짜 기준으로 조회합니다.

        Args:
            stock_ticker: 종목 코드
            date: 기준일

        Returns:
            Holding 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_holdings_by_date(self, date: datetime) -> List[Holding]:
        """
        특정 날짜의 모든 보유 종목을 조회합니다.

        Args:
            date: 기준일

        Returns:
            Holding 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_weight_history(self, etf_ticker: str, stock_ticker: str) -> List[Holding]:
        """
        특정 ETF 내 특정 종목의 비중 추이를 조회합니다.

        Args:
            etf_ticker: ETF 코드
            stock_ticker: 종목 코드

        Returns:
            시간순 정렬된 Holding 엔티티 리스트
        """
        pass

    # 날짜 관련

    @abstractmethod
    def get_latest_date(self) -> Optional[datetime]:
        """
        보유 종목 데이터의 가장 최신 날짜를 조회합니다.

        Returns:
            최신 날짜, 데이터가 없으면 None
        """
        pass

    @abstractmethod
    def get_available_dates(self, etf_ticker: str) -> List[datetime]:
        """
        특정 ETF의 데이터가 있는 모든 날짜를 조회합니다.

        Args:
            etf_ticker: ETF 코드

        Returns:
            날짜 리스트 (내림차순 정렬)
        """
        pass

    @abstractmethod
    def get_all_available_dates(self) -> List[datetime]:
        """
        전체 보유 종목 데이터가 있는 모든 날짜를 조회합니다.

        Returns:
            날짜 리스트 (내림차순 정렬)
        """
        pass

    @abstractmethod
    def has_data_for_date(self, date: datetime) -> bool:
        """
        특정 날짜의 데이터가 존재하는지 확인합니다.

        Args:
            date: 확인할 날짜

        Returns:
            데이터 존재 여부
        """
        pass

    # 통계 관련

    @abstractmethod
    def count_holdings_by_etf(self, etf_ticker: str, date: datetime) -> int:
        """
        특정 ETF의 특정 날짜 보유 종목 개수를 반환합니다.

        Args:
            etf_ticker: ETF 코드
            date: 기준일

        Returns:
            보유 종목 개수
        """
        pass

    @abstractmethod
    def count_etfs_holding_stock(self, stock_ticker: str, date: datetime) -> int:
        """
        특정 종목을 보유한 ETF 개수를 반환합니다.

        Args:
            stock_ticker: 종목 코드
            date: 기준일

        Returns:
            ETF 개수
        """
        pass

    @abstractmethod
    def delete_holdings_by_date(self, date: datetime) -> None:
        """
        특정 날짜의 모든 보유 종목 데이터를 삭제합니다.

        Args:
            date: 삭제할 날짜
        """
        pass

    @abstractmethod
    def delete_holdings_by_etf(self, etf_ticker: str) -> None:
        """
        특정 ETF의 모든 보유 종목 데이터를 삭제합니다.

        Args:
            etf_ticker: ETF 코드
        """
        pass
