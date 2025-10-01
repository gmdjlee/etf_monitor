"""
데이터 수집 과정 추적 테스트
010010 ticker가 어떤 과정에서 수집되는지 추적합니다.
"""

import logging
from datetime import datetime

from config.settings import settings
from domain.services.etf_filter_service import ETFFilterService
from domain.value_objects.filter_criteria import FilterCriteria
from infrastructure.adapters.pykrx_adapter import PyKRXAdapter
from infrastructure.database.connection import db_connection
from infrastructure.database.repositories.sqlite_etf_repository import (
    SQLiteETFRepository,
)

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TickerTracker:
    """010010 ticker를 추적하는 헬퍼 클래스"""

    def __init__(self):
        self.tracked_ticker = "010010"
        self.found_locations = []

    def track(self, location: str, data: any):
        """특정 위치에서 010010을 발견하면 기록"""
        if isinstance(data, str) and self.tracked_ticker in data:
            self.found_locations.append(
                {"location": location, "type": "string", "data": data}
            )
            print(f"  🔍 [FOUND] {location}: {data}")

        elif isinstance(data, dict):
            if self.tracked_ticker in str(data):
                self.found_locations.append(
                    {"location": location, "type": "dict", "data": data}
                )
                print(f"  🔍 [FOUND] {location}: {data}")

        elif isinstance(data, list):
            for item in data:
                if hasattr(item, "ticker") and item.ticker == self.tracked_ticker:
                    self.found_locations.append(
                        {
                            "location": location,
                            "type": "list_item",
                            "data": f"{item.ticker} - {getattr(item, 'name', 'N/A')}",
                        }
                    )
                    print(
                        f"  🔍 [FOUND] {location}: {item.ticker} - {getattr(item, 'name', 'N/A')}"
                    )

    def print_summary(self):
        """추적 결과 요약 출력"""
        print("\n" + "=" * 80)
        print(f"추적 결과 요약: '{self.tracked_ticker}' 발견 위치")
        print("=" * 80)

        if not self.found_locations:
            print("❌ 추적 대상 ticker를 발견하지 못했습니다.")
        else:
            print(f"✅ 총 {len(self.found_locations)}개 위치에서 발견:")
            for i, loc in enumerate(self.found_locations, 1):
                print(f"\n{i}. {loc['location']}")
                print(f"   타입: {loc['type']}")
                print(f"   데이터: {loc['data']}")


def test_etf_collection_with_tracking():
    """ETF 수집 과정을 추적합니다."""

    print("=" * 80)
    print("TEST: ETF 수집 과정에서 010010 추적")
    print("=" * 80)

    tracker = TickerTracker()
    adapter = PyKRXAdapter()
    filter_service = ETFFilterService()
    etf_repo = SQLiteETFRepository(db_connection)

    # 최신 날짜 가져오기
    latest_date = etf_repo.get_latest_date()
    if not latest_date:
        latest_date = datetime.now()

    test_date = latest_date
    print(f"\n테스트 날짜: {test_date.strftime('%Y-%m-%d')}")

    # 1. PyKRX에서 ETF 목록 수집
    print("\n[1] PyKRX에서 ETF 목록 수집")
    print("-" * 80)

    try:
        all_etfs = adapter.collect_etfs_for_date(test_date)
        print(f"  수집된 ETF 개수: {len(all_etfs)}")

        tracker.track("PyKRX ETF 목록", all_etfs)

        # 010010이 있는지 확인
        target_etf = None
        for etf in all_etfs:
            if etf.ticker == "010010":
                target_etf = etf
                print(f"\n  ✓ 010010 ETF 발견: {etf.name}")
                break

        if not target_etf:
            print("\n  ✗ 010010 ETF 없음")

    except Exception as e:
        print(f"  ✗ ETF 목록 수집 실패: {e}")
        import traceback

        traceback.print_exc()

    # 2. 필터링 과정 추적
    print("\n[2] ETF 필터링 과정")
    print("-" * 80)

    try:
        criteria = FilterCriteria.create(
            themes=settings.DEFAULT_THEMES,
            exclusions=settings.DEFAULT_EXCLUSIONS,
            require_active=settings.REQUIRE_ACTIVE_KEYWORD,
        )

        print("  필터 조건:")
        print(f"    - 테마: {criteria.themes}")
        print(f"    - 제외: {criteria.exclusions}")
        print(f"    - 액티브 필수: {criteria.require_active}")

        filtered_etfs = filter_service.filter_etfs(all_etfs, criteria)
        print(f"\n  필터링 후 ETF 개수: {len(filtered_etfs)}")

        tracker.track("필터링된 ETF 목록", filtered_etfs)

        # 010010이 필터링되었는지 확인
        if target_etf:
            is_filtered = target_etf in filtered_etfs
            if is_filtered:
                print("  ✓ 010010 ETF가 필터를 통과했습니다.")
            else:
                print("  ✗ 010010 ETF가 필터에서 제외되었습니다.")
                # 왜 제외되었는지 확인
                if not target_etf.is_active():
                    print("    이유: 액티브 ETF가 아님")
                if target_etf.has_exclusion(criteria.exclusions):
                    print("    이유: 제외 키워드 포함")
                if not target_etf.matches_theme(criteria.themes):
                    print("    이유: 테마 매칭 안됨")

    except Exception as e:
        print(f"  ✗ 필터링 실패: {e}")
        import traceback

        traceback.print_exc()

    # 3. Holdings 수집 과정 추적 (010010이 ETF인 경우)
    if target_etf and target_etf in filtered_etfs:
        print("\n[3] 010010 ETF의 Holdings 수집")
        print("-" * 80)

        try:
            holdings = adapter.collect_holdings_for_date("010010", test_date)
            print(f"  수집된 holdings 개수: {len(holdings)}")

            if holdings:
                print("\n  상위 5개 보유 종목:")
                for h in holdings[:5]:
                    print(f"    - {h.stock_ticker}: {h.stock_name} ({h.weight}%)")

                # 각 holding의 stock_ticker 추적
                for h in holdings:
                    tracker.track("010010 ETF의 보유 종목", h.stock_ticker)

        except Exception as e:
            print(f"  ✗ Holdings 수집 실패: {e}")
            import traceback

            traceback.print_exc()

    # 4. 다른 ETF의 holdings에서 010010이 stock으로 사용되는지 확인
    print("\n[4] 다른 ETF의 holdings에서 010010 검색")
    print("-" * 80)

    try:
        # 샘플로 몇 개 ETF의 holdings를 확인
        sample_etfs = filtered_etfs[:5]  # 상위 5개만

        print(f"  샘플 ETF {len(sample_etfs)}개 검사 중...")

        for etf in sample_etfs:
            try:
                holdings = adapter.collect_holdings_for_date(etf.ticker, test_date)

                for h in holdings:
                    if h.stock_ticker == "010010":
                        print(
                            f"\n  🔍 [FOUND] {etf.ticker} ({etf.name})가 010010을 보유 종목으로 가지고 있음"
                        )
                        print(f"    - 비중: {h.weight}%")
                        print(f"    - 금액: {h.amount}")
                        print(f"    - 종목명: {h.stock_name}")

                        tracker.track(f"{etf.ticker}의 보유 종목", h.stock_ticker)

            except Exception as e:
                print(f"  ⚠️  {etf.ticker} holdings 수집 실패: {e}")

    except Exception as e:
        print(f"  ✗ Holdings 검색 실패: {e}")
        import traceback

        traceback.print_exc()

    # 추적 결과 출력
    tracker.print_summary()

    print("\n" + "=" * 80)
    print("TEST: 추적 완료")
    print("=" * 80)


def test_specific_date_holdings():
    """특정 날짜의 holdings에서 010010 검색"""

    print("=" * 80)
    print("TEST: 특정 날짜 Holdings에서 010010 검색")
    print("=" * 80)

    etf_repo = SQLiteETFRepository(db_connection)

    try:
        # 최신 날짜 가져오기
        latest_date = etf_repo.get_latest_date()
        if not latest_date:
            print("❌ 데이터베이스에 데이터가 없습니다.")
            return

        print(f"\n최신 날짜: {latest_date.strftime('%Y-%m-%d')}")

        # 해당 날짜의 모든 holdings 가져오기
        all_holdings = etf_repo.find_holdings_by_date(latest_date)
        print(f"전체 holdings 개수: {len(all_holdings)}")

        # 010010 검색
        found_as_etf = []
        found_as_stock = []

        for h in all_holdings:
            if h.etf_ticker == "010010":
                found_as_etf.append(h)
            if h.stock_ticker == "010010":
                found_as_stock.append(h)

        print("\n[결과]")
        print(f"  ETF로 사용: {len(found_as_etf)}개")
        print(f"  Stock으로 사용: {len(found_as_stock)}개")

        if found_as_etf:
            print("\n[010010이 ETF로 사용된 경우]")
            for h in found_as_etf[:10]:
                print(
                    f"  - 보유 종목: {h.stock_ticker} ({h.stock_name}), 비중: {h.weight}%"
                )

        if found_as_stock:
            print("\n[010010이 Stock으로 사용된 경우]")
            for h in found_as_stock[:10]:
                etf = etf_repo.find_by_ticker(h.etf_ticker)
                etf_name = etf.name if etf else "Unknown"
                print(f"  - ETF: {h.etf_ticker} ({etf_name}), 비중: {h.weight}%")

    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "010010 Ticker 추적 테스트" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # 테스트 1: 데이터베이스에서 검색
    test_specific_date_holdings()

    print("\n\n")

    # 테스트 2: 수집 과정 추적
    test_etf_collection_with_tracking()
