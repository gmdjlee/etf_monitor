import logging
import sqlite3
from threading import Lock


class DatabaseManager:
    """SQLite 데이터베이스 연결 및 테이블 생성을 관리하는 클래스"""

    _instance = None
    _lock = Lock()

    def __new__(cls, db_path):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance.db_path = db_path
                cls._instance.connection = None
                logging.info(f"데이터베이스 관리자 초기화: {db_path}")
            return cls._instance

    def get_connection(self):
        """데이터베이스 연결을 반환합니다. (스레드 안전)"""
        try:
            # check_same_thread=False는 Flask의 다중 요청 처리를 위해 필요합니다.
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logging.error(f"데이터베이스 연결 실패: {e}", exc_info=True)
            return None

    def create_tables(self):
        """
        필요한 모든 테이블을 생성합니다.
        스키마 분리를 위해 테이블명에 접두사를 사용합니다.
        """
        conn = self.get_connection()
        if not conn:
            return

        try:
            with conn:
                # 설정 스키마
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS config_themes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS config_exclusions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT UNIQUE NOT NULL
                    )
                """)
                # 데이터 스키마
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_stocks (
                        ticker TEXT PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_etfs (
                        ticker TEXT PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_etf_holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        etf_ticker TEXT NOT NULL,
                        stock_ticker TEXT NOT NULL,
                        date TEXT NOT NULL,
                        weight REAL NOT NULL,
                        amount REAL DEFAULT 0,
                        FOREIGN KEY (etf_ticker) REFERENCES data_etfs (ticker),
                        FOREIGN KEY (stock_ticker) REFERENCES data_stocks (ticker),
                        UNIQUE (etf_ticker, stock_ticker, date)
                    )
                """)

                # 기존 테이블에 amount 컬럼이 없다면 추가
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(data_etf_holdings)")
                columns = [col[1] for col in cursor.fetchall()]
                if "amount" not in columns:
                    logging.info("기존 테이블에 amount 컬럼 추가 중...")
                    conn.execute(
                        "ALTER TABLE data_etf_holdings ADD COLUMN amount REAL DEFAULT 0"
                    )

                # 인덱스 추가로 성능 확보
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_holdings_etf_date ON data_etf_holdings (etf_ticker, date)"
                )
                logging.info("데이터베이스 테이블 생성 또는 확인 완료.")
        except sqlite3.Error as e:
            logging.error(f"테이블 생성 실패: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()

    def is_db_empty(self):
        """데이터베이스에 ETF 데이터가 비어 있는지 확인합니다."""
        conn = self.get_connection()
        if not conn:
            return True
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM data_etfs")
            count = cursor.fetchone()[0]
            return count == 0
        except sqlite3.Error:
            return True  # 테이블이 없는 경우 등
        finally:
            if conn:
                conn.close()
