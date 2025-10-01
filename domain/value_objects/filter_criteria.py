"""
FilterCriteria 값 객체
ETF 필터링 조건을 표현하는 불변 값 객체입니다.
"""

from dataclasses import dataclass
from typing import List, Optional

from shared.exceptions import InvalidEntityException


@dataclass(frozen=True)
class FilterCriteria:
    """
    필터링 조건 값 객체

    ETF를 필터링하기 위한 조건들을 담는 불변 객체입니다.

    Attributes:
        themes: 포함되어야 할 테마 키워드 리스트
        exclusions: 제외할 키워드 리스트
        require_active: '액티브' 키워드 필수 여부
        min_holdings: 최소 보유 종목 수 (선택사항)

    Examples:
        >>> criteria = FilterCriteria.create(
        ...     themes=["반도체", "AI"],
        ...     exclusions=["레버리지", "인버스"],
        ...     require_active=True
        ... )
        >>> criteria.has_themes()
        True
        >>> criteria.themes_count()
        2
    """

    themes: List[str]
    exclusions: List[str]
    require_active: bool
    min_holdings: Optional[int] = None

    @staticmethod
    def create(
        themes: List[str] = None,
        exclusions: List[str] = None,
        require_active: bool = True,
        min_holdings: Optional[int] = None,
    ) -> "FilterCriteria":
        """
        FilterCriteria 인스턴스를 생성하고 유효성을 검증합니다.

        Args:
            themes: 테마 키워드 리스트
            exclusions: 제외 키워드 리스트
            require_active: 액티브 필수 여부
            min_holdings: 최소 보유 종목 수

        Returns:
            검증된 FilterCriteria 인스턴스

        Raises:
            InvalidEntityException: 유효하지 않은 조건인 경우
        """
        # 기본값 설정
        themes = themes or []
        exclusions = exclusions or []

        # 테마 검증 (빈 문자열 제거)
        themes = [t.strip() for t in themes if t and t.strip()]

        # 제외 키워드 검증 (빈 문자열 제거)
        exclusions = [e.strip() for e in exclusions if e and e.strip()]

        # min_holdings 검증
        if min_holdings is not None and min_holdings < 0:
            raise InvalidEntityException(
                "FilterCriteria",
                f"min_holdings must be non-negative, got {min_holdings}",
            )

        return FilterCriteria(
            themes=themes,
            exclusions=exclusions,
            require_active=require_active,
            min_holdings=min_holdings,
        )

    @staticmethod
    def default() -> "FilterCriteria":
        """기본 필터 조건 생성 (아무것도 필터링하지 않음)"""
        return FilterCriteria.create(themes=[], exclusions=[], require_active=False)

    @staticmethod
    def active_only() -> "FilterCriteria":
        """액티브 ETF만 필터링하는 조건"""
        return FilterCriteria.create(themes=[], exclusions=[], require_active=True)

    def to_dict(self) -> dict:
        """값 객체를 딕셔너리로 변환"""
        return {
            "themes": self.themes,
            "exclusions": self.exclusions,
            "require_active": self.require_active,
            "min_holdings": self.min_holdings,
        }

    def __str__(self) -> str:
        """사람이 읽기 쉬운 문자열 표현"""
        parts = []

        if self.require_active:
            parts.append("액티브 필수")

        if self.themes:
            parts.append(f"테마: {', '.join(self.themes)}")

        if self.exclusions:
            parts.append(f"제외: {', '.join(self.exclusions)}")

        if self.min_holdings:
            parts.append(f"최소 {self.min_holdings}개 종목")

        return " | ".join(parts) if parts else "필터 없음"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"FilterCriteria(themes={self.themes}, "
            f"exclusions={self.exclusions}, "
            f"require_active={self.require_active}, "
            f"min_holdings={self.min_holdings})"
        )

    def has_themes(self) -> bool:
        """테마 필터가 있는지 확인"""
        return len(self.themes) > 0

    def has_exclusions(self) -> bool:
        """제외 필터가 있는지 확인"""
        return len(self.exclusions) > 0

    def has_any_filter(self) -> bool:
        """어떤 필터라도 설정되어 있는지 확인"""
        return (
            self.has_themes()
            or self.has_exclusions()
            or self.require_active
            or self.min_holdings is not None
        )

    def themes_count(self) -> int:
        """테마 개수 반환"""
        return len(self.themes)

    def exclusions_count(self) -> int:
        """제외 키워드 개수 반환"""
        return len(self.exclusions)

    def with_themes(self, themes: List[str]) -> "FilterCriteria":
        """테마를 설정한 새로운 FilterCriteria 반환"""
        return FilterCriteria.create(
            themes=themes,
            exclusions=self.exclusions,
            require_active=self.require_active,
            min_holdings=self.min_holdings,
        )

    def with_exclusions(self, exclusions: List[str]) -> "FilterCriteria":
        """제외 키워드를 설정한 새로운 FilterCriteria 반환"""
        return FilterCriteria.create(
            themes=self.themes,
            exclusions=exclusions,
            require_active=self.require_active,
            min_holdings=self.min_holdings,
        )

    def with_active_required(self, required: bool) -> "FilterCriteria":
        """액티브 필수 여부를 설정한 새로운 FilterCriteria 반환"""
        return FilterCriteria.create(
            themes=self.themes,
            exclusions=self.exclusions,
            require_active=required,
            min_holdings=self.min_holdings,
        )

    def add_theme(self, theme: str) -> "FilterCriteria":
        """테마를 추가한 새로운 FilterCriteria 반환"""
        if theme.strip() and theme not in self.themes:
            new_themes = self.themes + [theme.strip()]
            return self.with_themes(new_themes)
        return self

    def remove_theme(self, theme: str) -> "FilterCriteria":
        """테마를 제거한 새로운 FilterCriteria 반환"""
        new_themes = [t for t in self.themes if t != theme]
        return self.with_themes(new_themes)

    def add_exclusion(self, exclusion: str) -> "FilterCriteria":
        """제외 키워드를 추가한 새로운 FilterCriteria 반환"""
        if exclusion.strip() and exclusion not in self.exclusions:
            new_exclusions = self.exclusions + [exclusion.strip()]
            return self.with_exclusions(new_exclusions)
        return self

    def remove_exclusion(self, exclusion: str) -> "FilterCriteria":
        """제외 키워드를 제거한 새로운 FilterCriteria 반환"""
        new_exclusions = [e for e in self.exclusions if e != exclusion]
        return self.with_exclusions(new_exclusions)

    def merge(self, other: "FilterCriteria") -> "FilterCriteria":
        """
        다른 FilterCriteria와 병합

        Args:
            other: 병합할 FilterCriteria

        Returns:
            병합된 새로운 FilterCriteria
        """
        # 중복 제거하면서 병합
        merged_themes = list(set(self.themes + other.themes))
        merged_exclusions = list(set(self.exclusions + other.exclusions))

        return FilterCriteria.create(
            themes=merged_themes,
            exclusions=merged_exclusions,
            require_active=self.require_active or other.require_active,
            min_holdings=max(self.min_holdings or 0, other.min_holdings or 0) or None,
        )
