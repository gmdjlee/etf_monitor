"""
Holdings Analyzer Service
보유 종목 분석 비즈니스 로직을 담당하는 도메인 서비스입니다.
"""

from typing import Dict, List, Tuple

from config.logging_config import LoggerMixin
from domain.entities.holding import Holding
from domain.value_objects.weight_change import WeightChange


class HoldingsAnalyzer(LoggerMixin):
    """
    보유 종목 분석 서비스

    ETF의 보유 종목을 분석하여 비중 변화, 신규/제외 종목 등을 파악하는
    비즈니스 로직을 담당합니다.

    Examples:
        >>> analyzer = HoldingsAnalyzer()
        >>> comparison = analyzer.compare_holdings(previous_holdings, current_holdings)
        >>> new_stocks = comparison['new']
        >>> removed_stocks = comparison['removed']
    """

    def compare_holdings(
        self, previous_holdings: List[Holding], current_holdings: List[Holding]
    ) -> Dict[str, List[Holding]]:
        """
        이전과 현재 보유 종목을 비교하여 변화를 분석합니다.

        Args:
            previous_holdings: 이전 보유 종목 리스트
            current_holdings: 현재 보유 종목 리스트

        Returns:
            비교 결과 딕셔너리:
            - 'new': 신규 추가된 종목
            - 'removed': 제외된 종목
            - 'increased': 비중 증가 종목
            - 'decreased': 비중 감소 종목
            - 'unchanged': 비중 유지 종목
        """
        self.logger.debug(
            f"Comparing holdings: previous={len(previous_holdings)}, "
            f"current={len(current_holdings)}"
        )

        # 티커별로 인덱싱
        prev_dict = {h.stock_ticker: h for h in previous_holdings}
        curr_dict = {h.stock_ticker: h for h in current_holdings}

        # 모든 티커 수집
        all_tickers = set(prev_dict.keys()) | set(curr_dict.keys())

        # 분류
        result = {
            "new": [],
            "removed": [],
            "increased": [],
            "decreased": [],
            "unchanged": [],
        }

        for ticker in all_tickers:
            prev_holding = prev_dict.get(ticker)
            curr_holding = curr_dict.get(ticker)

            # 신규 추가
            if prev_holding is None and curr_holding is not None:
                result["new"].append(curr_holding)

            # 제외
            elif prev_holding is not None and curr_holding is None:
                result["removed"].append(prev_holding)

            # 비중 변화 분석
            elif prev_holding is not None and curr_holding is not None:
                change = curr_holding.calculate_weight_change(prev_holding)

                if change > 0.01:  # 0.01% 이상 증가
                    result["increased"].append(curr_holding)
                elif change < -0.01:  # 0.01% 이상 감소
                    result["decreased"].append(curr_holding)
                else:
                    result["unchanged"].append(curr_holding)

        self.logger.info(
            f"Comparison result: new={len(result['new'])}, "
            f"removed={len(result['removed'])}, "
            f"increased={len(result['increased'])}, "
            f"decreased={len(result['decreased'])}, "
            f"unchanged={len(result['unchanged'])}"
        )

        return result

    def calculate_weight_changes(
        self, previous_holdings: List[Holding], current_holdings: List[Holding]
    ) -> Dict[str, WeightChange]:
        """
        각 종목의 비중 변화를 계산합니다.

        Args:
            previous_holdings: 이전 보유 종목 리스트
            current_holdings: 현재 보유 종목 리스트

        Returns:
            {stock_ticker: WeightChange} 딕셔너리
        """
        prev_dict = {h.stock_ticker: h for h in previous_holdings}
        curr_dict = {h.stock_ticker: h for h in current_holdings}

        all_tickers = set(prev_dict.keys()) | set(curr_dict.keys())

        changes = {}
        for ticker in all_tickers:
            prev_weight = prev_dict[ticker].weight if ticker in prev_dict else 0.0
            curr_weight = curr_dict[ticker].weight if ticker in curr_dict else 0.0

            changes[ticker] = WeightChange.create(prev_weight, curr_weight)

        return changes

    def get_top_holdings(
        self, holdings: List[Holding], top_n: int = 10
    ) -> List[Holding]:
        """
        비중 상위 N개 종목을 반환합니다.

        Args:
            holdings: 보유 종목 리스트
            top_n: 반환할 개수

        Returns:
            비중 순으로 정렬된 상위 종목 리스트
        """
        sorted_holdings = sorted(holdings, key=lambda h: h.weight, reverse=True)
        return sorted_holdings[:top_n]

    def get_significant_holdings(
        self, holdings: List[Holding], threshold: float = 1.0
    ) -> List[Holding]:
        """
        유의미한 비중(threshold 이상)을 가진 종목들을 반환합니다.

        Args:
            holdings: 보유 종목 리스트
            threshold: 최소 비중 기준 (%)

        Returns:
            유의미한 비중을 가진 종목 리스트
        """
        return [h for h in holdings if h.is_significant_weight(threshold)]

    def calculate_total_weight(self, holdings: List[Holding]) -> float:
        """
        전체 비중 합계를 계산합니다.

        Args:
            holdings: 보유 종목 리스트

        Returns:
            비중 합계 (%)
        """
        return sum(h.weight for h in holdings)

    def calculate_total_amount(self, holdings: List[Holding]) -> float:
        """
        전체 평가금액 합계를 계산합니다.

        Args:
            holdings: 보유 종목 리스트

        Returns:
            평가금액 합계 (원)
        """
        return sum(h.amount for h in holdings)

    def group_by_weight_range(
        self, holdings: List[Holding]
    ) -> Dict[str, List[Holding]]:
        """
        비중 범위별로 종목을 그룹화합니다.

        Args:
            holdings: 보유 종목 리스트

        Returns:
            비중 범위별 그룹화된 종목 딕셔너리
            - 'large': 5% 이상
            - 'medium': 1% 이상 5% 미만
            - 'small': 1% 미만
        """
        groups = {
            "large": [],  # 5% 이상
            "medium": [],  # 1% ~ 5%
            "small": [],  # 1% 미만
        }

        for holding in holdings:
            if holding.weight >= 5.0:
                groups["large"].append(holding)
            elif holding.weight >= 1.0:
                groups["medium"].append(holding)
            else:
                groups["small"].append(holding)

        return groups

    def find_significant_changes(
        self, weight_changes: Dict[str, WeightChange], threshold: float = 0.5
    ) -> List[Tuple[str, WeightChange]]:
        """
        유의미한 비중 변화(threshold 이상)를 찾습니다.

        Args:
            weight_changes: 비중 변화 딕셔너리
            threshold: 최소 변화량 기준 (%)

        Returns:
            (stock_ticker, WeightChange) 튜플 리스트
        """
        significant = [
            (ticker, change)
            for ticker, change in weight_changes.items()
            if change.is_significant(threshold)
        ]

        # 변화량 절대값 기준으로 정렬
        significant.sort(key=lambda x: abs(x[1].change_amount), reverse=True)

        return significant

    def get_new_stocks(
        self, previous_holdings: List[Holding], current_holdings: List[Holding]
    ) -> List[Holding]:
        """
        신규 추가된 종목들을 반환합니다.

        Args:
            previous_holdings: 이전 보유 종목 리스트
            current_holdings: 현재 보유 종목 리스트

        Returns:
            신규 추가된 종목 리스트
        """
        prev_tickers = {h.stock_ticker for h in previous_holdings}
        return [h for h in current_holdings if h.stock_ticker not in prev_tickers]

    def get_removed_stocks(
        self, previous_holdings: List[Holding], current_holdings: List[Holding]
    ) -> List[Holding]:
        """
        제외된 종목들을 반환합니다.

        Args:
            previous_holdings: 이전 보유 종목 리스트
            current_holdings: 현재 보유 종목 리스트

        Returns:
            제외된 종목 리스트
        """
        curr_tickers = {h.stock_ticker for h in current_holdings}
        return [h for h in previous_holdings if h.stock_ticker not in curr_tickers]

    def calculate_concentration_ratio(
        self, holdings: List[Holding], top_n: int = 10
    ) -> float:
        """
        상위 N개 종목의 집중도를 계산합니다.

        Args:
            holdings: 보유 종목 리스트
            top_n: 상위 종목 개수

        Returns:
            상위 N개 종목의 비중 합계 (%)
        """
        top_holdings = self.get_top_holdings(holdings, top_n)
        return self.calculate_total_weight(top_holdings)
