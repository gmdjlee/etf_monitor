"""
Ticker 010010 추적 테스트 코드
문제가 되는 ticker가 어디서 나타나는지 추적합니다.
"""

import logging

from infrastructure.adapters.pykrx_adapter import PyKRXAdapter
from infrastructure.database.connection import db_connection
from infrastructure.database.repositories.sqlite_etf_repository import (
    SQLiteETFRepository,
)
from infrastructure.database.repositories.sqlite_stock_repository import (
    SQLiteStockRepository,
)

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_trace_010010():
    """010010 ticker를 추적합니다."""

    print("=" * 80)
    print("TEST: 010010 Ticker 추적 시작")
    print("=" * 80)

    # 1. 데이터베이스에서 010010 검색
    print("\n[1] 데이터베이스에서 010010 검색")
    print("-" * 80)

    etf_repo = SQLiteETFRepository(db_connection)
    stock_repo = SQLiteStockRepository(db_connection)

    # ETF 테이블에서 검색
    print("\n[1-1] ETF 테이블 검색:")
    try:
        etf = etf_repo.find_by_ticker("010010")
        if etf:
            print(f"  ✓ ETF 테이블에 존재: {etf.ticker} - {etf.name}")
        else:
            print("  ✗ ETF 테이블에 없음")
    except Exception as e:
        print(f"  ✗ ETF 검색 실패: {e}")

    # Stock 테이블에서 검색
    print("\n[1-2] Stock 테이블 검색:")
    try:
        stock = stock_repo.find_by_ticker("010010")
        if stock:
            print(f"  ✓ Stock 테이블에 존재: {stock.ticker} - {stock.name}")
        else:
            print("  ✗ Stock 테이블에 없음")
    except Exception as e:
        print(f"  ✗ Stock 검색 실패: {e}")

    # Holdings 테이블에서 검색
    print("\n[1-3] Holdings 테이블에서 010010이 포함된 데이터 검색:")
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # ETF로서 검색
        cursor.execute("""
            SELECT DISTINCT etf_ticker, COUNT(*) as cnt 
            FROM data_etf_holdings 
            WHERE etf_ticker = '010010'
            GROUP BY etf_ticker
        """)
        etf_holdings = cursor.fetchall()
        if etf_holdings:
            for row in etf_holdings:
                print(
                    f"  ✓ ETF로 사용됨: {row['etf_ticker']} ({row['cnt']}개 종목 보유)"
                )
        else:
            print("  ✗ ETF로 사용된 기록 없음")

        # Stock으로서 검색
        cursor.execute("""
            SELECT DISTINCT etf_ticker, date, weight, amount 
            FROM data_etf_holdings 
            WHERE stock_ticker = '010010'
            ORDER BY date DESC
            LIMIT 5
        """)
        stock_holdings = cursor.fetchall()
        if stock_holdings:
            print(f"  ✓ Stock으로 사용됨 ({len(stock_holdings)}개 기록):")
            for row in stock_holdings:
                print(
                    f"    - ETF: {row['etf_ticker']}, 날짜: {row['date']}, 비중: {row['weight']}%, 금액: {row['amount']}"
                )
        else:
            print("  ✗ Stock으로 사용된 기록 없음")

    except Exception as e:
        print(f"  ✗ Holdings 검색 실패: {e}")

    # 2. PyKRX API로 010010 조회
    print("\n[2] PyKRX API로 010010 조회")
    print("-" * 80)

    adapter = PyKRXAdapter()

    # Stock 이름 조회
    print("\n[2-1] Stock 이름 조회:")
    try:
        name = adapter._safe_get_stock_name("010010")
        if name:
            print(f"  ✓ PyKRX Stock 이름: {name}")
        else:
            print("  ✗ PyKRX에서 Stock 이름 조회 실패")
    except Exception as e:
        print(f"  ✗ PyKRX Stock 이름 조회 오류: {e}")

    # ETF 이름 조회
    print("\n[2-2] ETF 이름 조회:")
    try:
        name = adapter._safe_get_etf_name("010010")
        if name:
            print(f"  ✓ PyKRX ETF 이름: {name}")
        else:
            print("  ✗ PyKRX에서 ETF 이름 조회 실패")
    except Exception as e:
        print(f"  ✗ PyKRX ETF 이름 조회 오류: {e}")

    # 3. 특정 날짜의 ETF 목록에서 010010 확인
    print("\n[3] 최근 날짜 ETF 목록에서 010010 확인")
    print("-" * 80)

    try:
        latest_date = etf_repo.get_latest_date()
        if latest_date:
            print(f"\n최신 날짜: {latest_date.strftime('%Y-%m-%d')}")

            # 해당 날짜의 모든 ETF 조회
            all_etfs = etf_repo.find_all()
            print(f"전체 ETF 개수: {len(all_etfs)}")

            # 010010이 있는지 확인
            target_etf = None
            for etf in all_etfs:
                if etf.ticker == "010010":
                    target_etf = etf
                    break

            if target_etf:
                print(f"\n  ✓ 010010 ETF 발견: {target_etf.name}")

                # 해당 ETF의 holdings 조회
                holdings = etf_repo.find_holdings_by_etf_and_date("010010", latest_date)
                print(f"  ✓ 010010 ETF가 보유한 종목 수: {len(holdings)}")

                if holdings:
                    print("\n  상위 5개 보유 종목:")
                    for h in holdings[:5]:
                        print(f"    - {h.stock_ticker}: {h.stock_name} ({h.weight}%)")
            else:
                print("\n  ✗ 010010 ETF 없음")

    except Exception as e:
        print(f"  ✗ ETF 목록 확인 실패: {e}")

    # 4. 010010이 다른 ETF의 보유 종목으로 사용되는 경우 확인
    print("\n[4] 010010을 보유 종목으로 가진 ETF 검색")
    print("-" * 80)

    try:
        if latest_date:
            holdings_with_010010 = etf_repo.find_holdings_by_stock_and_date(
                "010010", latest_date
            )

            if holdings_with_010010:
                print(f"\n  ✓ 010010을 보유한 ETF 개수: {len(holdings_with_010010)}")
                print("\n  010010을 보유한 ETF 목록:")
                for h in holdings_with_010010:
                    etf = etf_repo.find_by_ticker(h.etf_ticker)
                    etf_name = etf.name if etf else "Unknown"
                    print(
                        f"    - {h.etf_ticker}: {etf_name} (비중: {h.weight}%, 금액: {h.amount})"
                    )
            else:
                print("\n  ✗ 010010을 보유한 ETF 없음")
    except Exception as e:
        print(f"  ✗ 010010 보유 ETF 검색 실패: {e}")

    # 5. 데이터베이스에서 '010010'이 포함된 모든 레코드 검색
    print("\n[5] 데이터베이스 전체 스캔 (010010 관련)")
    print("-" * 80)

    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # ETF 테이블
        cursor.execute("SELECT * FROM data_etfs WHERE ticker LIKE '%010010%'")
        etf_records = cursor.fetchall()
        print(f"\n[5-1] ETF 테이블: {len(etf_records)}개 레코드")
        for row in etf_records:
            print(f"  - {row['ticker']}: {row['name']}")

        # Stock 테이블
        cursor.execute("SELECT * FROM data_stocks WHERE ticker LIKE '%010010%'")
        stock_records = cursor.fetchall()
        print(f"\n[5-2] Stock 테이블: {len(stock_records)}개 레코드")
        for row in stock_records:
            print(f"  - {row['ticker']}: {row['name']}")

        # Holdings 테이블 (ETF로서)
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM data_etf_holdings WHERE etf_ticker = '010010'"
        )
        etf_holdings_count = cursor.fetchone()["cnt"]
        print(f"\n[5-3] Holdings 테이블 (ETF로서): {etf_holdings_count}개 레코드")

        # Holdings 테이블 (Stock으로서)
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM data_etf_holdings WHERE stock_ticker = '010010'"
        )
        stock_holdings_count = cursor.fetchone()["cnt"]
        print(f"[5-4] Holdings 테이블 (Stock으로서): {stock_holdings_count}개 레코드")

    except Exception as e:
        print(f"  ✗ 전체 스캔 실패: {e}")

    print("\n" + "=" * 80)
    print("TEST: 010010 Ticker 추적 완료")
    print("=" * 80)


if __name__ == "__main__":
    test_trace_010010()
