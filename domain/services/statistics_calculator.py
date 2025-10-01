"""
Statistics Calculator Service
통계 계산 비즈니스 로직을 담당하는 도메인 서비스입니다.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from config.logging_config import LoggerMixin
from domain.entities.etf import ETF
from domain.entities.holding import Holding


class StatisticsCalculator(LoggerMixin):
    """
    통계 계산 서비스

    중복 종목, 금액 순위, 비중 분석 등의 통계를 계산하는
    비즈니스 로직을 담당합니다.

    Examples:
        >>> calculator = StatisticsCalculator()
        >>> duplicates = calculator.calculate_duplicate_stocks(all_holdings)
        >>> top_by_amount = calculator.calculate_amount_ranking(all_holdings)
    """

    def calculate_duplicate_stocks(
        self, holdings: List[Holding], min_count: int = 2
    ) -> List[Dict]:
        """
        중복 종목 통계를 계산합니다.

        여러 ETF에 포함된 종목들을 찾아 중복 횟수와 통계를 계산합니다.

        Args:
            holdings: 보유 종목 리스트
            min_count: 최소 중복 횟수 (기본값: 2)

        Returns:
            중복 종목 통계 리스트, 각 항목:
            {
                'ticker': 종목코드,
                'name': 종목명,
                'etf_count': 포함된 ETF 개수,
                'etf_tickers': ETF 코드 리스트,
                'total_amount': 총 평가금액,
                'avg_weight': 평균 비중,
                'max_weight': 최대 비중,
                'min_weight': 최소 비중
            }
        """
        self.logger.debug(f"Calculating duplicate stocks from {len(holdings)} holdings")

        # 종목별로 그룹화
        stock_stats = defaultdict(
            lambda: {
                "ticker": "",
                "name": "",
                "etf_tickers": set(),
                "weights": [],
                "amounts": [],
            }
        )

        for holding in holdings:
            ticker = holding.stock_ticker
            stats = stock_stats[ticker]

            stats["ticker"] = holding.stock_ticker
            stats["name"] = holding.stock_name
            stats["etf_tickers"].add(holding.etf_ticker)
            stats["weights"].append(holding.weight)
            stats["amounts"].append(holding.amount)

        # min_count 이상인 종목만 필터링하고 통계 계산
        results = []
        for ticker, stats in stock_stats.items():
            etf_count = len(stats["etf_tickers"])

            if etf_count >= min_count:
                results.append(
                    {
                        "ticker": stats["ticker"],
                        "name": stats["name"],
                        "etf_count": etf_count,
                        "etf_tickers": list(stats["etf_tickers"]),
                        "total_amount": sum(stats["amounts"]),
                        "avg_weight": round(
                            sum(stats["weights"]) / len(stats["weights"]), 2
                        ),
                        "max_weight": round(max(stats["weights"]), 2),
                        "min_weight": round(min(stats["weights"]), 2),
                    }
                )

        # ETF 개수와 총 금액 기준으로 정렬
        results.sort(key=lambda x: (x["etf_count"], x["total_amount"]), reverse=True)

        self.logger.info(f"Found {len(results)} duplicate stocks")
        return results

    def calculate_amount_ranking(
        self, holdings: List[Holding], top_n: int = 100
    ) -> List[Dict]:
        """
        평가금액 순위를 계산합니다.

        Args:
            holdings: 보유 종목 리스트
            top_n: 상위 N개 (0이면 전체)

        Returns:
            평가금액 순위 리스트, 각 항목:
            {
                'ticker': 종목코드,
                'name': 종목명,
                'total_amount': 총 평가금액,
                'etf_count': 포함된 ETF 개수,
                'avg_weight': 평균 비중,
                'max_weight': 최대 비중
            }
        """
        self.logger.debug(f"Calculating amount ranking from {len(holdings)} holdings")

        # 종목별로 그룹화
        stock_stats = defaultdict(
            lambda: {
                "ticker": "",
                "name": "",
                "etf_count": 0,
                "weights": [],
                "amounts": [],
            }
        )

        for holding in holdings:
            ticker = holding.stock_ticker
            stats = stock_stats[ticker]

            stats["ticker"] = holding.stock_ticker
            stats["name"] = holding.stock_name
            stats["etf_count"] += 1
            stats["weights"].append(holding.weight)
            stats["amounts"].append(holding.amount)

        # 통계 계산
        results = []
        for ticker, stats in stock_stats.items():
            total_amount = sum(stats["amounts"])

            if total_amount > 0:  # 금액이 있는 종목만
                results.append(
                    {
                        "ticker": stats["ticker"],
                        "name": stats["name"],
                        "total_amount": total_amount,
                        "etf_count": stats["etf_count"],
                        "avg_weight": round(
                            sum(stats["weights"]) / len(stats["weights"]), 2
                        ),
                        "max_weight": round(max(stats["weights"]), 2),
                    }
                )

        # 총 평가금액 기준으로 정렬
        results.sort(key=lambda x: x["total_amount"], reverse=True)

        # 상위 N개만 반환
        if top_n > 0:
            results = results[:top_n]

        self.logger.info(f"Calculated amount ranking: {len(results)} stocks")
        return results

    def calculate_theme_statistics(
        self, holdings: List[Holding], etfs: List[ETF], theme: str
    ) -> Dict:
        """
        특정 테마의 통계를 계산합니다.

        Args:
            holdings: 보유 종목 리스트
            etfs: ETF 리스트
            theme: 테마 키워드

        Returns:
            테마 통계:
            {
                'theme': 테마명,
                'etf_count': 해당 테마 ETF 개수,
                'etf_tickers': ETF 코드 리스트,
                'total_holdings': 총 보유 종목 수,
                'unique_stocks': 고유 종목 수,
                'duplicate_stocks': 중복 종목 통계
            }
        """
        self.logger.debug(f"Calculating statistics for theme: {theme}")

        # 테마에 해당하는 ETF 필터링
        theme_etfs = [etf for etf in etfs if etf.contains_keyword(theme)]
        theme_etf_tickers = {etf.ticker for etf in theme_etfs}

        # 해당 ETF의 보유 종목만 필터링
        theme_holdings = [h for h in holdings if h.etf_ticker in theme_etf_tickers]

        # 고유 종목 수 계산
        unique_stocks = len(set(h.stock_ticker for h in theme_holdings))

        # 중복 종목 통계
        duplicate_stocks = self.calculate_duplicate_stocks(theme_holdings, min_count=2)

        result = {
            "theme": theme,
            "etf_count": len(theme_etfs),
            "etf_tickers": [etf.ticker for etf in theme_etfs],
            "total_holdings": len(theme_holdings),
            "unique_stocks": unique_stocks,
            "duplicate_stocks": duplicate_stocks,
        }

        self.logger.info(
            f"Theme '{theme}' statistics: {result['etf_count']} ETFs, "
            f"{result['unique_stocks']} unique stocks"
        )

        return result

    def calculate_weight_distribution(self, holdings: List[Holding]) -> Dict[str, int]:
        """
        비중 분포를 계산합니다.

        Args:
            holdings: 보유 종목 리스트

        Returns:
            비중 범위별 종목 개수:
            {
                'under_1': 1% 미만,
                '1_to_3': 1~3%,
                '3_to_5': 3~5%,
                '5_to_10': 5~10%,
                'over_10': 10% 이상
            }
        """
        distribution = {
            "under_1": 0,
            "1_to_3": 0,
            "3_to_5": 0,
            "5_to_10": 0,
            "over_10": 0,
        }

        for holding in holdings:
            weight = holding.weight

            if weight < 1.0:
                distribution["under_1"] += 1
            elif weight < 3.0:
                distribution["1_to_3"] += 1
            elif weight < 5.0:
                distribution["3_to_5"] += 1
            elif weight < 10.0:
                distribution["5_to_10"] += 1
            else:
                distribution["over_10"] += 1

        return distribution

    def calculate_etf_overlap(
        self, etf1_holdings: List[Holding], etf2_holdings: List[Holding]
    ) -> Dict:
        """
        두 ETF 간의 종목 중복도를 계산합니다.

        Args:
            etf1_holdings: 첫 번째 ETF 보유 종목
            etf2_holdings: 두 번째 ETF 보유 종목

        Returns:
            중복도 통계:
            {
                'overlap_count': 중복 종목 수,
                'overlap_tickers': 중복 종목 코드 리스트,
                'overlap_ratio_1': ETF1 기준 중복 비율,
                'overlap_ratio_2': ETF2 기준 중복 비율
            }
        """
        tickers1 = {h.stock_ticker for h in etf1_holdings}
        tickers2 = {h.stock_ticker for h in etf2_holdings}

        overlap = tickers1 & tickers2
        overlap_count = len(overlap)

        ratio1 = overlap_count / len(tickers1) if tickers1 else 0
        ratio2 = overlap_count / len(tickers2) if tickers2 else 0

        return {
            "overlap_count": overlap_count,
            "overlap_tickers": list(overlap),
            "overlap_ratio_1": round(ratio1 * 100, 2),
            "overlap_ratio_2": round(ratio2 * 100, 2),
        }

    def get_top_stocks_by_frequency(
        self, holdings: List[Holding], top_n: int = 20
    ) -> List[Tuple[str, int]]:
        """
        가장 많은 ETF에 포함된 종목을 찾습니다.

        Args:
            holdings: 보유 종목 리스트
            top_n: 상위 N개

        Returns:
            (종목코드, ETF 개수) 튜플 리스트
        """
        frequency = defaultdict(set)

        for holding in holdings:
            frequency[holding.stock_ticker].add(holding.etf_ticker)

        # ETF 개수로 정렬
        sorted_stocks = sorted(frequency.items(), key=lambda x: len(x[1]), reverse=True)

        return [(ticker, len(etf_set)) for ticker, etf_set in sorted_stocks[:top_n]]
