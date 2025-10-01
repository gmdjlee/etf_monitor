"""
ETF Filter Service
ETF 필터링 비즈니스 로직을 담당하는 도메인 서비스입니다.
"""

from typing import List

from config.logging_config import LoggerMixin
from domain.entities.etf import ETF
from domain.value_objects.filter_criteria import FilterCriteria


class ETFFilterService(LoggerMixin):
    """
    ETF 필터링 서비스

    ETF를 테마, 제외 키워드, 액티브 여부 등의 기준으로 필터링하는
    비즈니스 로직을 담당합니다.

    Examples:
        >>> service = ETFFilterService()
        >>> criteria = FilterCriteria.create(
        ...     themes=["반도체"],
        ...     exclusions=["레버리지"],
        ...     require_active=True
        ... )
        >>> filtered = service.filter_etfs(all_etfs, criteria)
    """

    def filter_etfs(self, etfs: List[ETF], criteria: FilterCriteria) -> List[ETF]:
        """
        필터 조건에 따라 ETF 리스트를 필터링합니다.

        Args:
            etfs: 필터링할 ETF 리스트
            criteria: 필터링 조건

        Returns:
            필터링된 ETF 리스트
        """
        if not etfs:
            self.logger.debug("No ETFs to filter")
            return []

        self.logger.info(f"Filtering {len(etfs)} ETFs with criteria: {criteria}")

        filtered = etfs

        # 액티브 필터 적용
        if criteria.require_active:
            filtered = self._filter_by_active(filtered)
            self.logger.debug(f"After active filter: {len(filtered)} ETFs")

        # 제외 키워드 필터 적용
        if criteria.has_exclusions():
            filtered = self._filter_by_exclusions(filtered, criteria.exclusions)
            self.logger.debug(f"After exclusion filter: {len(filtered)} ETFs")

        # 테마 필터 적용
        if criteria.has_themes():
            filtered = self._filter_by_themes(filtered, criteria.themes)
            self.logger.debug(f"After theme filter: {len(filtered)} ETFs")

        self.logger.info(
            f"Filtering completed: {len(filtered)}/{len(etfs)} ETFs matched"
        )

        return filtered

    def _filter_by_active(self, etfs: List[ETF]) -> List[ETF]:
        """
        액티브 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트

        Returns:
            액티브 ETF 리스트
        """
        return [etf for etf in etfs if etf.is_active()]

    def _filter_by_exclusions(
        self, etfs: List[ETF], exclusions: List[str]
    ) -> List[ETF]:
        """
        제외 키워드가 포함되지 않은 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트
            exclusions: 제외 키워드 리스트

        Returns:
            필터링된 ETF 리스트
        """
        return [etf for etf in etfs if not etf.has_exclusion(exclusions)]

    def _filter_by_themes(self, etfs: List[ETF], themes: List[str]) -> List[ETF]:
        """
        테마 키워드 중 하나라도 포함된 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트
            themes: 테마 키워드 리스트

        Returns:
            필터링된 ETF 리스트
        """
        return [etf for etf in etfs if etf.matches_theme(themes)]

    def count_by_criteria(self, etfs: List[ETF], criteria: FilterCriteria) -> int:
        """
        필터 조건에 맞는 ETF 개수를 반환합니다.

        Args:
            etfs: ETF 리스트
            criteria: 필터링 조건

        Returns:
            매칭되는 ETF 개수
        """
        filtered = self.filter_etfs(etfs, criteria)
        return len(filtered)

    def filter_by_theme(self, etfs: List[ETF], theme: str) -> List[ETF]:
        """
        특정 테마를 포함하는 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트
            theme: 테마 키워드

        Returns:
            필터링된 ETF 리스트
        """
        criteria = FilterCriteria.create(themes=[theme], require_active=False)
        return self.filter_etfs(etfs, criteria)

    def filter_active_only(self, etfs: List[ETF]) -> List[ETF]:
        """
        액티브 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트

        Returns:
            액티브 ETF 리스트
        """
        criteria = FilterCriteria.active_only()
        return self.filter_etfs(etfs, criteria)

    def exclude_keywords(self, etfs: List[ETF], exclusions: List[str]) -> List[ETF]:
        """
        제외 키워드가 포함되지 않은 ETF만 필터링합니다.

        Args:
            etfs: ETF 리스트
            exclusions: 제외 키워드 리스트

        Returns:
            필터링된 ETF 리스트
        """
        criteria = FilterCriteria.create(exclusions=exclusions, require_active=False)
        return self.filter_etfs(etfs, criteria)

    def get_matching_themes(self, etf: ETF, theme_list: List[str]) -> List[str]:
        """
        ETF에 매칭되는 테마 키워드들을 추출합니다.

        Args:
            etf: ETF 엔티티
            theme_list: 테마 키워드 리스트

        Returns:
            매칭되는 테마 리스트
        """
        return etf.extract_theme_keywords(theme_list)

    def validate_criteria(self, criteria: FilterCriteria) -> bool:
        """
        필터 조건의 유효성을 검증합니다.

        Args:
            criteria: 검증할 필터 조건

        Returns:
            유효 여부
        """
        # FilterCriteria는 생성 시 검증되므로 여기서는 추가 검증만 수행

        # 테마가 너무 많은지 확인 (성능 고려)
        if criteria.themes_count() > 50:
            self.logger.warning(f"Too many themes: {criteria.themes_count()}")
            return False

        # 제외 키워드가 너무 많은지 확인
        if criteria.exclusions_count() > 50:
            self.logger.warning(f"Too many exclusions: {criteria.exclusions_count()}")
            return False

        return True
