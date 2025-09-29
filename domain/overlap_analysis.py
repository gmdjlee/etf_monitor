from collections import defaultdict
from typing import Dict, List

from domain.repositories import EtfRepository


class OverlapAnalysisService:
    """ETF 간 중복 종목을 분석하는 서비스 클래스"""

    def __init__(self, etf_repo: EtfRepository):
        self.etf_repo = etf_repo

    def analyze_stock_overlaps(self, theme_filter: str = None) -> Dict:
        """
        모든 ETF 또는 특정 테마의 ETF들 간 중복 종목을 분석합니다.

        Args:
            theme_filter: 필터링할 테마 키워드 (None이면 전체 분석)

        Returns:
            중복 분석 결과를 담은 딕셔너리
        """
        # 1. ETF 목록 가져오기
        all_etfs = self.etf_repo.get_all_etfs()

        # 테마 필터링
        if theme_filter and theme_filter != "all":
            filtered_etfs = [etf for etf in all_etfs if theme_filter in etf.name]
        else:
            filtered_etfs = all_etfs

        if not filtered_etfs:
            return {"theme": theme_filter or "전체", "etf_count": 0, "stocks": []}

        # 2. 최신 날짜 가져오기
        latest_date = self.etf_repo.get_latest_date()
        if not latest_date:
            return {
                "theme": theme_filter or "전체",
                "etf_count": len(filtered_etfs),
                "stocks": [],
            }

        # 3. 각 종목별로 정보 수집
        stock_info = defaultdict(
            lambda: {
                "ticker": "",
                "name": "",
                "total_amount": 0.0,
                "total_weight": 0.0,
                "etf_count": 0,
                "etf_list": [],
                "holdings": [],
            }
        )

        for etf in filtered_etfs:
            holdings = self.etf_repo.get_etf_holdings_by_date(etf.ticker, latest_date)

            for holding in holdings:
                stock_key = holding.stock_ticker

                # 종목 정보 업데이트
                if not stock_info[stock_key]["ticker"]:
                    stock_info[stock_key]["ticker"] = holding.stock_ticker
                    stock_info[stock_key]["name"] = holding.stock_name

                # 금액과 비중 누적
                stock_info[stock_key]["total_amount"] += holding.amount
                stock_info[stock_key]["total_weight"] += holding.weight
                stock_info[stock_key]["etf_count"] += 1
                stock_info[stock_key]["etf_list"].append(etf.name)
                stock_info[stock_key]["holdings"].append(
                    {
                        "etf_name": etf.name,
                        "etf_ticker": etf.ticker,
                        "weight": holding.weight,
                        "amount": holding.amount,
                    }
                )

        # 4. 리스트로 변환 및 평균 계산
        stocks_list = []
        for stock_ticker, info in stock_info.items():
            if info["etf_count"] > 0:  # 최소 1개 이상의 ETF에 포함된 종목만
                stocks_list.append(
                    {
                        "ticker": info["ticker"],
                        "name": info["name"],
                        "total_amount": info["total_amount"],
                        "avg_weight": round(
                            info["total_weight"] / info["etf_count"], 2
                        ),
                        "etf_count": info["etf_count"],
                        "etf_list": info["etf_list"],
                        "holdings": sorted(
                            info["holdings"], key=lambda x: x["weight"], reverse=True
                        ),
                    }
                )

        # 5. 결과 반환
        return {
            "theme": theme_filter or "전체",
            "etf_count": len(filtered_etfs),
            "etf_names": [etf.name for etf in filtered_etfs],
            "analysis_date": latest_date,
            "stocks": stocks_list,
        }

    def get_top_overlapped_stocks(
        self, theme_filter: str = None, sort_by: str = "count", limit: int = 20
    ) -> List[Dict]:
        """
        중복 종목을 정렬하여 상위 N개를 반환합니다.

        Args:
            theme_filter: 테마 필터
            sort_by: 정렬 기준 ("count" 또는 "amount")
            limit: 반환할 종목 수

        Returns:
            정렬된 상위 종목 리스트
        """
        analysis = self.analyze_stock_overlaps(theme_filter)
        stocks = analysis["stocks"]

        # 중복이 있는 종목만 필터링 (2개 이상의 ETF에 포함)
        overlapped_stocks = [s for s in stocks if s["etf_count"] >= 2]

        # 정렬
        if sort_by == "amount":
            sorted_stocks = sorted(
                overlapped_stocks, key=lambda x: x["total_amount"], reverse=True
            )
        else:  # count
            sorted_stocks = sorted(
                overlapped_stocks,
                key=lambda x: (x["etf_count"], x["total_amount"]),
                reverse=True,
            )

        # 상위 N개만 반환
        return sorted_stocks[:limit]

    def get_available_themes(self) -> List[str]:
        """분석 가능한 테마 목록을 반환합니다."""
        all_etfs = self.etf_repo.get_all_etfs()
        themes = set()

        # ETF 이름에서 테마 추출 (간단한 키워드 기반)
        theme_keywords = [
            "반도체",
            "바이오",
            "2차전지",
            "AI",
            "인공지능",
            "배터리",
            "ESG",
            "혁신",
            "성장",
            "밸류업",
            "수출",
            "테크",
            "IT",
            "헬스케어",
            "메타버스",
            "로봇",
            "신재생",
            "친환경",
            "탄소중립",
            "전기차",
            "조선",
            "소비",
            "컬처",
            "메모리",
            "비메모리",
            "블록체인",
            "배당",
            "이노베이션",
        ]

        for etf in all_etfs:
            for keyword in theme_keywords:
                if keyword in etf.name:
                    themes.add(keyword)

        return sorted(list(themes))
