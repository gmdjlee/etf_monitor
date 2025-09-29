import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from pykrx import stock

from domain.models import ETF, ETFHolding, Stock
from domain.repositories import ConfigRepository, EtfRepository, StockRepository

DEFAULT_COLLECT_DAYS = 5  # 초기 수집 시 10일치 데이터 수집


class EtfDataService:
    """ETF 데이터 수집, 필터링, 분석 등 핵심 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(
        self,
        etf_repo: EtfRepository,
        stock_repo: StockRepository,
        config_repo: ConfigRepository,
    ):
        self.etf_repo = etf_repo
        self.stock_repo = stock_repo
        self.config_repo = config_repo

    def _get_default_themes_and_exclusions(self):
        """기본 테마와 제외 키워드를 반환합니다."""
        default_themes = [
            "반도체",
            "바이오",
            "혁신기술",
            "배당성장",
            "신재생",
            "2차전지",
            "AI",
            "코스피",
            "조선",
            "테크",
            "수출",
            "로봇",
            "컬처",
            "밸류업",
            "친환경",
            "소비",
            "이노베이션",
            "메모리",
            "비메모리",
            "인공지능",
            "전기차",
            "배터리",
            "ESG",
            "탄소중립",
            "메타버스",
            "블록체인",
            "헬스케어",
            "IT",
            "성장",
        ]
        default_exclusions = [
            "인버스",
            "레버리지",
            "곱버스",
            "2X",
            "3X",
            "글로벌",
            "차이나",
            "채권",
            "달러",
            "China",
            "아시아",
            "미국",
            "일본",
            "코스피",
            "코스닥",
        ]
        return default_themes, default_exclusions

    def run_initial_setup(self) -> bool:
        """
        초기 설정을 실행합니다.
        1. DB가 비어있는지 확인합니다.
        2. 기본 설정(테마, 제외어)을 DB에 추가합니다.
        3. 전체 주식 목록을 수집하여 DB에 저장합니다.
        4. 10일치 ETF 데이터를 수집하고 필터링하여 DB에 저장합니다.
        """
        if not self.etf_repo.db_manager.is_db_empty():
            logging.info("데이터베이스가 이미 존재하여 초기 설정을 건너뜁니다.")
            return False

        logging.info("초기 설정을 시작합니다...")

        # 1. 기본 설정 추가
        themes, exclusions = self._get_default_themes_and_exclusions()
        for theme in themes:
            self.config_repo.add_theme(theme)
        for exclusion in exclusions:
            self.config_repo.add_exclusion(exclusion)

        # 2. 전체 주식 목록 수집
        logging.info("전체 주식 목록 수집 중...")
        all_stocks = []
        today_str = datetime.now().strftime("%Y%m%d")
        for market in ["KOSPI", "KOSDAQ"]:
            tickers = stock.get_market_ticker_list(today_str, market=market)
            for ticker in tickers:
                name = stock.get_market_ticker_name(ticker)
                all_stocks.append(Stock(ticker=ticker, name=name))
                time.sleep(0.01)  # API 과부하 방지
        self.stock_repo.bulk_insert_stocks(all_stocks)
        logging.info(f"{len(all_stocks)}개의 주식 정보 저장 완료.")

        # 3. 10일치 데이터 수집
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DEFAULT_COLLECT_DAYS)
        logging.info(
            f"{start_date.strftime('%Y-%m-%d')}부터 {end_date.strftime('%Y-%m-%d')}까지의 데이터를 수집합니다."
        )

        # 날짜를 하루씩 순회하며 데이터 수집
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            # 주식 시장 개장일(business day)인지 확인
            # 대표 종목(삼성전자)의 시세 조회가 가능하면 개장일로 판단
            df_market_check = stock.get_market_ohlcv(date_str, date_str, "005930")
            if not df_market_check.empty:
                logging.info(f"{date_str} 데이터 처리 중...")
                try:
                    self._fetch_and_store_data_for_date(date_str)
                except Exception as e:
                    logging.warning(f"{date_str} 데이터 처리 중 오류 발생: {e}")
            else:
                logging.info(f"{date_str}은 주식 시장 개장일이 아니므로 건너뜁니다.")

            current_date += timedelta(days=1)

        logging.info("초기 데이터 설정이 성공적으로 완료되었습니다.")
        return True

    def _fetch_and_store_data_for_date(self, date_str: str):
        """특정 날짜의 ETF 데이터를 가져와 필터링 후 저장합니다."""
        etf_tickers = stock.get_etf_ticker_list(date_str)
        filtered_etfs = self._filter_etfs(etf_tickers, date_str)

        for etf in filtered_etfs:
            self.etf_repo.add_etf(etf)
            try:
                holdings_df = stock.get_etf_portfolio_deposit_file(etf.ticker, date_str)
                # '비중' 컬럼이 없는 경우 건너뛰기
                if "비중" not in holdings_df.columns:
                    logging.warning(
                        f"{date_str} {etf.name}({etf.ticker}) ETF의 '비중' 정보가 없습니다."
                    )
                    continue

                holdings = []
                for _, row in holdings_df.iterrows():
                    # 평가금액 컬럼 처리
                    amount = 0.0
                    if "금액" in holdings_df.columns:
                        amount = float(row["금액"]) if pd.notna(row["금액"]) else 0.0

                    holdings.append(
                        ETFHolding(
                            etf_ticker=etf.ticker,
                            stock_ticker=row.name,  # Ticker가 index로 들어감
                            date=datetime.strptime(date_str, "%Y%m%d").strftime(
                                "%Y-%m-%d"
                            ),
                            weight=row["비중"],
                            amount=amount,
                        )
                    )
                if holdings:
                    self.etf_repo.bulk_insert_holdings(holdings)
            except Exception as e:
                logging.warning(
                    f"{date_str} {etf.name}({etf.ticker}) ETF 보유 종목 조회 실패: {e}"
                )
            time.sleep(0.1)  # API 과부하 방지

    def _filter_etfs(self, etf_tickers: List[str], date_str: str) -> List[ETF]:
        """주어진 ETF 목록을 '액티브'를 포함하며, 설정된 테마와 제외 키워드에 따라 필터링합니다."""
        themes = [t["name"] for t in self.config_repo.get_themes()]
        exclusions = [e["keyword"] for e in self.config_repo.get_exclusions()]

        filtered_list = []
        for ticker in etf_tickers:
            name = stock.get_etf_ticker_name(ticker)

            # 1. 제외 키워드 포함 여부 확인
            if any(ex in name for ex in exclusions):
                continue

            # 2. '액티브' 키워드 필수 포함 여부 확인
            if "액티브" not in name:
                continue

            # 3. 테마 키워드 포함 여부 확인
            if any(theme in name for theme in themes):
                filtered_list.append(ETF(ticker, name))

        return filtered_list

    def update_latest_data(self) -> int:
        """최신 데이터를 업데이트합니다."""
        last_date_str = self.etf_repo.get_latest_date()
        if last_date_str is None:
            raise Exception("데이터가 없습니다. 먼저 초기화를 진행해주세요.")

        start_date = datetime.strptime(last_date_str, "%Y-%m-%d") + timedelta(days=1)
        end_date = datetime.now()

        logging.info(
            f"데이터 업데이트 시작: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
        )

        updated_etf_count = set()
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            # 주식 시장 개장일(business day)인지 확인
            df_market_check = stock.get_market_ohlcv(date_str, date_str, "005930")
            if not df_market_check.empty:
                logging.info(f"{date_str} 데이터 업데이트 중...")
                try:
                    self._fetch_and_store_data_for_date(date_str)
                    # 업데이트된 ETF Ticker 수를 세기 위해 set에 추가
                    etfs_on_date = stock.get_etf_ticker_list(date_str)
                    updated_etf_count.update(etfs_on_date)
                except Exception as e:
                    logging.warning(f"{date_str} 데이터 업데이트 중 오류 발생: {e}")
            else:
                logging.info(
                    f"{date_str}은 주식 시장 개장일이 아니므로 업데이트를 건너뜁니다."
                )

            current_date += timedelta(days=1)

        logging.info(
            f"데이터 업데이트 완료. 총 {len(updated_etf_count)}개 ETF 정보 확인."
        )
        return len(updated_etf_count)

    def get_holdings_comparison(self, etf_ticker: str) -> Dict:
        """
        최신 두 날짜의 보유 종목을 비교하여 결과를 반환합니다.
        """
        available_dates = self.etf_repo.get_available_dates_for_etf(etf_ticker)
        if len(available_dates) < 2:
            # 데이터가 하루치만 있을 경우
            latest_date = available_dates[0] if available_dates else None
            holdings = (
                self.etf_repo.get_etf_holdings_by_date(etf_ticker, latest_date)
                if latest_date
                else []
            )
            comparison_list = []
            for h in holdings:
                comparison_list.append(
                    {
                        "stock_ticker": h.stock_ticker,
                        "stock_name": h.stock_name,
                        "prev_weight": 0,
                        "current_weight": h.weight,
                        "change": h.weight,
                        "current_amount": h.amount,
                        "status": "신규",
                    }
                )
            return {
                "etf_ticker": etf_ticker,
                "prev_date": "N/A",
                "current_date": latest_date,
                "comparison": sorted(
                    comparison_list, key=lambda x: x["current_weight"], reverse=True
                ),
            }

        current_date, prev_date = available_dates[0], available_dates[1]

        current_holdings_list = self.etf_repo.get_etf_holdings_by_date(
            etf_ticker, current_date
        )
        prev_holdings_list = self.etf_repo.get_etf_holdings_by_date(
            etf_ticker, prev_date
        )

        current_holdings = {h.stock_ticker: h for h in current_holdings_list}
        prev_holdings = {h.stock_ticker: h for h in prev_holdings_list}

        comparison_list = []
        all_tickers = set(current_holdings.keys()) | set(prev_holdings.keys())

        for ticker in all_tickers:
            current = current_holdings.get(ticker)
            prev = prev_holdings.get(ticker)

            item = {
                "stock_ticker": ticker,
                "stock_name": current.stock_name if current else prev.stock_name,
                "prev_weight": prev.weight if prev else 0,
                "current_weight": current.weight if current else 0,
                "current_amount": current.amount if current else 0,
            }

            if current and not prev:
                item["status"] = "신규"
                item["change"] = item["current_weight"]
            elif not current and prev:
                item["status"] = "제외"
                item["change"] = -item["prev_weight"]
            else:
                change = item["current_weight"] - item["prev_weight"]
                item["change"] = round(change, 4)
                if change > 0:
                    item["status"] = "비중 증가"
                elif change < 0:
                    item["status"] = "비중 감소"
                else:
                    item["status"] = "유지"

            comparison_list.append(item)

        # 현재 비중 기준으로 정렬
        sorted_comparison = sorted(
            comparison_list, key=lambda x: x["current_weight"], reverse=True
        )

        return {
            "etf_ticker": etf_ticker,
            "prev_date": prev_date,
            "current_date": current_date,
            "comparison": sorted_comparison,
        }

    def get_duplicate_stock_stats(self) -> Dict:
        """전체 ETF에서 중복 종목 순위를 반환합니다."""
        return self.etf_repo.get_duplicate_stock_statistics()

    def get_amount_ranking_stats(self) -> Dict:
        """전체 ETF에서 종목별 총 평가금액 순위를 반환합니다."""
        return self.etf_repo.get_amount_ranking_statistics()

    def get_theme_duplicate_stock_stats(self, theme: str) -> Dict:
        """특정 테마 ETF들에서 중복 종목 순위를 반환합니다."""
        return self.etf_repo.get_theme_duplicate_stock_statistics(theme)

    def export_to_csv(self, ticker: str, data: Dict) -> str:
        """비교 데이터를 CSV 파일로 변환하여 저장하고 파일 경로를 반환합니다."""
        df = pd.DataFrame(data["comparison"])

        # 금액을 억원 단위로 변환하여 표시
        df["amount_billion"] = df["current_amount"] / 100000000

        df = df.rename(
            columns={
                "stock_name": "종목명",
                "stock_ticker": "종목코드",
                "prev_weight": f"이전 비중({data['prev_date']})",
                "current_weight": f"현재 비중({data['current_date']})",
                "change": "변동률",
                "amount_billion": "금액(억원)",
                "status": "상태",
            }
        )

        # 필요한 컬럼만 선택하여 저장
        df = df[
            [
                "종목명",
                "종목코드",
                f"이전 비중({data['prev_date']})",
                f"현재 비중({data['current_date']})",
                "변동률",
                "금액(억원)",
                "상태",
            ]
        ]

        # 임시 파일로 저장
        temp_dir = "temp_exports"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        file_path = os.path.join(
            temp_dir,
            f"{ticker}_holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        return file_path
