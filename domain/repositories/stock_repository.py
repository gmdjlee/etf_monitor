"""
Stock Repository 인터페이스
주식 데이터 접근을 위한 추상 인터페이스입니다.
"""

from abc import abstractmethod
from typing import List, Optional

from domain.entities.stock import Stock
from domain.repositories.base import BaseRepository


class StockRepository(BaseRepository[Stock, str]):
    """
    주식 리포지토리 인터페이스

    주식 엔티티의 영속성을 담당하는 추상 인터페이스입니다.
    Infrastructure 레이어에서 구체적으로 구현됩니다.

    식별자: ticker (str)
    """

    @abstractmethod
    def find_by_ticker(self, ticker: str) -> Optional[Stock]:
        """
        티커로 주식을 조회합니다.

        Args:
            ticker: 종목 코드

        Returns:
            찾은 Stock 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Stock]:
        """
        종목명으로 주식을 조회합니다.

        Args:
            name: 종목명

        Returns:
            찾은 Stock 엔티티, 없으면 None
        """
        pass

    @abstractmethod
    def find_by_name_like(self, keyword: str) -> List[Stock]:
        """
        종목명에 키워드가 포함된 주식들을 조회합니다.

        Args:
            keyword: 검색 키워드

        Returns:
            매칭되는 Stock 엔티티 리스트
        """
        pass

    @abstractmethod
    def find_by_tickers(self, tickers: List[str]) -> List[Stock]:
        """
        여러 티커에 해당하는 주식들을 조회합니다.

        Args:
            tickers: 종목 코드 리스트

        Returns:
            찾은 Stock 엔티티 리스트
        """
        pass

    @abstractmethod
    def exists_by_ticker(self, ticker: str) -> bool:
        """
        티커에 해당하는 주식이 존재하는지 확인합니다.

        Args:
            ticker: 종목 코드

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    def find_all_by_market(self, market: str) -> List[Stock]:
        """
        특정 시장의 모든 주식을 조회합니다.

        Args:
            market: 시장 코드 (KOSPI, KOSDAQ)

        Returns:
            Stock 엔티티 리스트
        """
        pass

    @abstractmethod
    def count_by_market(self, market: str) -> int:
        """
        특정 시장의 주식 개수를 반환합니다.

        Args:
            market: 시장 코드

        Returns:
            주식 개수
        """
        pass

    # BaseRepository 메서드 구현은 Infrastructure에서
    # 여기서는 Stock 특화 메서드만 추가 정의
