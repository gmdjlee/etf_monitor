"""
Config Repository 인터페이스
설정 데이터 접근을 위한 추상 인터페이스입니다.
"""

from abc import ABC, abstractmethod
from typing import List


class ConfigRepository(ABC):
    """
    설정 리포지토리 인터페이스

    테마, 제외 키워드 등의 설정 데이터 영속성을 담당하는 추상 인터페이스입니다.
    Infrastructure 레이어에서 구체적으로 구현됩니다.
    """

    # 테마 관리

    @abstractmethod
    def get_all_themes(self) -> List[str]:
        """
        모든 테마 키워드를 조회합니다.

        Returns:
            테마 키워드 리스트
        """
        pass

    @abstractmethod
    def add_theme(self, theme: str) -> None:
        """
        테마 키워드를 추가합니다.

        Args:
            theme: 추가할 테마 키워드
        """
        pass

    @abstractmethod
    def remove_theme(self, theme: str) -> None:
        """
        테마 키워드를 삭제합니다.

        Args:
            theme: 삭제할 테마 키워드
        """
        pass

    @abstractmethod
    def theme_exists(self, theme: str) -> bool:
        """
        테마 키워드가 존재하는지 확인합니다.

        Args:
            theme: 확인할 테마 키워드

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    def count_themes(self) -> int:
        """
        테마 키워드 개수를 반환합니다.

        Returns:
            테마 개수
        """
        pass

    # 제외 키워드 관리

    @abstractmethod
    def get_all_exclusions(self) -> List[str]:
        """
        모든 제외 키워드를 조회합니다.

        Returns:
            제외 키워드 리스트
        """
        pass

    @abstractmethod
    def add_exclusion(self, exclusion: str) -> None:
        """
        제외 키워드를 추가합니다.

        Args:
            exclusion: 추가할 제외 키워드
        """
        pass

    @abstractmethod
    def remove_exclusion(self, exclusion: str) -> None:
        """
        제외 키워드를 삭제합니다.

        Args:
            exclusion: 삭제할 제외 키워드
        """
        pass

    @abstractmethod
    def exclusion_exists(self, exclusion: str) -> bool:
        """
        제외 키워드가 존재하는지 확인합니다.

        Args:
            exclusion: 확인할 제외 키워드

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    def count_exclusions(self) -> int:
        """
        제외 키워드 개수를 반환합니다.

        Returns:
            제외 키워드 개수
        """
        pass

    # 일괄 작업

    @abstractmethod
    def set_themes(self, themes: List[str]) -> None:
        """
        테마 키워드를 일괄 설정합니다 (기존 데이터 삭제 후 추가).

        Args:
            themes: 설정할 테마 키워드 리스트
        """
        pass

    @abstractmethod
    def set_exclusions(self, exclusions: List[str]) -> None:
        """
        제외 키워드를 일괄 설정합니다 (기존 데이터 삭제 후 추가).

        Args:
            exclusions: 설정할 제외 키워드 리스트
        """
        pass

    @abstractmethod
    def clear_themes(self) -> None:
        """모든 테마 키워드를 삭제합니다."""
        pass

    @abstractmethod
    def clear_exclusions(self) -> None:
        """모든 제외 키워드를 삭제합니다."""
        pass

    @abstractmethod
    def reset_to_defaults(self) -> None:
        """설정을 기본값으로 리셋합니다."""
        pass

    # 설정 상태 확인

    @abstractmethod
    def is_empty(self) -> bool:
        """
        설정이 비어있는지 확인합니다.

        Returns:
            테마와 제외 키워드가 모두 없으면 True
        """
        pass

    @abstractmethod
    def has_default_config(self) -> bool:
        """
        기본 설정이 로드되어 있는지 확인합니다.

        Returns:
            기본 설정 존재 여부
        """
        pass
