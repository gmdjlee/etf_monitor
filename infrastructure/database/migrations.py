"""
Database Migrations
데이터베이스 스키마 마이그레이션을 관리합니다.
"""

import sqlite3

from config.logging_config import LoggerMixin
from shared.exceptions import DatabaseException

from infrastructure.database.connection import DatabaseConnection


class DatabaseMigrations(LoggerMixin):
    """
    데이터베이스 마이그레이션 관리 클래스
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db_conn = db_connection

    def create_tables(self) -> None:
        """필요한 모든 테이블을 생성합니다."""
        try:
            self.logger.info("Creating database tables")

            conn = self.db_conn.get_connection()

            with conn:
                # 설정 테이블
                self._create_config_tables(conn)

                # 데이터 테이블
                self._create_data_tables(conn)

                # ✅ 인덱스 생성 (성능 최적화)
                self._create_indexes(conn)

            self.logger.info("Database tables created successfully")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise DatabaseException("create_tables", str(e))

    def _create_config_tables(self, conn: sqlite3.Connection) -> None:
        """설정 관련 테이블을 생성합니다."""
        # 테마 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 제외 키워드 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS config_exclusions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.logger.debug("Config tables created")

    def _create_data_tables(self, conn: sqlite3.Connection) -> None:
        """데이터 관련 테이블을 생성합니다."""
        # 주식 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_stocks (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ETF 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_etfs (
                ticker TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ETF 보유 종목 테이블
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_etf_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etf_ticker TEXT NOT NULL,
                stock_ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                weight REAL NOT NULL,
                amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (etf_ticker) REFERENCES data_etfs (ticker) ON DELETE CASCADE,
                FOREIGN KEY (stock_ticker) REFERENCES data_stocks (ticker) ON DELETE CASCADE,
                UNIQUE (etf_ticker, stock_ticker, date)
            )
        """)

        self.logger.debug("Data tables created")

    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """
        성능 향상을 위한 인덱스를 생성합니다.

        ✅ Medium Priority: 쿼리 성능 최적화
        """
        # ==========================================
        # 기존 인덱스 (High Priority에서 생성됨)
        # ==========================================

        # ETF + 날짜 복합 인덱스 (가장 많이 사용)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_etf_date 
            ON data_etf_holdings (etf_ticker, date)
        """)

        # 종목 + 날짜 복합 인덱스
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_stock_date 
            ON data_etf_holdings (stock_ticker, date)
        """)

        # 날짜 단독 인덱스
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_date 
            ON data_etf_holdings (date)
        """)

        # 비중 인덱스 (정렬용)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_weight 
            ON data_etf_holdings (weight)
        """)

        # 금액 인덱스 (정렬용)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_amount 
            ON data_etf_holdings (amount)
        """)

        # ==========================================
        # ✅ NEW: Medium Priority 최적화 인덱스
        # ==========================================

        # 1. 날짜 + 비중 DESC 복합 인덱스
        # 용도: 특정 날짜의 상위 비중 종목 조회 시 정렬 성능 향상
        # 쿼리 예: SELECT * FROM holdings WHERE date = ? ORDER BY weight DESC
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_date_weight_desc 
            ON data_etf_holdings (date, weight DESC)
        """)

        # 2. 날짜 + 금액 DESC 복합 인덱스
        # 용도: 특정 날짜의 금액 순위 조회 시 성능 향상
        # 쿼리 예: SELECT * FROM holdings WHERE date = ? ORDER BY amount DESC
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_date_amount_desc 
            ON data_etf_holdings (date, amount DESC)
        """)

        # 3. ETF + 날짜 + 비중 DESC 복합 인덱스
        # 용도: 특정 ETF의 특정 날짜 상위 종목 조회 최적화
        # 쿼리 예: SELECT * FROM holdings WHERE etf_ticker = ? AND date = ? ORDER BY weight DESC
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_etf_date_weight 
            ON data_etf_holdings (etf_ticker, date, weight DESC)
        """)

        # 4. 종목 + 날짜 + 비중 복합 인덱스
        # 용도: 특정 종목이 여러 ETF에서 차지하는 비중 조회
        # 쿼리 예: SELECT * FROM holdings WHERE stock_ticker = ? AND date = ? ORDER BY weight DESC
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_stock_date_weight 
            ON data_etf_holdings (stock_ticker, date, weight DESC)
        """)

        # 5. 날짜 + ETF + 종목 커버링 인덱스
        # 용도: 통계 쿼리 시 테이블 스캔 없이 인덱스만으로 조회
        # 쿼리 예: SELECT etf_ticker, stock_ticker, weight FROM holdings WHERE date = ?
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_holdings_date_covering 
            ON data_etf_holdings (date, etf_ticker, stock_ticker, weight, amount)
        """)

        # 6. ETF명 검색 최적화 (LIKE 쿼리용)
        # 용도: ETF명 부분 검색 성능 향상
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_etfs_name 
            ON data_etfs (name COLLATE NOCASE)
        """)

        # 7. 주식명 검색 최적화
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_stocks_name 
            ON data_stocks (name COLLATE NOCASE)
        """)

        # 8. Config 테마/제외 키워드 검색 최적화
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_themes_name 
            ON config_themes (name COLLATE NOCASE)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_exclusions_keyword 
            ON config_exclusions (keyword COLLATE NOCASE)
        """)

        self.logger.info("✅ All indexes created (including performance optimizations)")

    def migrate_add_amount_column(self) -> None:
        """
        기존 테이블에 amount 컬럼을 추가하는 마이그레이션
        (이미 존재하는 경우 무시)
        """
        try:
            conn = self.db_conn.get_connection()
            cursor = conn.cursor()

            # 테이블 정보 조회
            cursor.execute("PRAGMA table_info(data_etf_holdings)")
            columns = [col[1] for col in cursor.fetchall()]

            # amount 컬럼이 없으면 추가
            if "amount" not in columns:
                self.logger.info("Adding amount column to data_etf_holdings")
                conn.execute(
                    "ALTER TABLE data_etf_holdings ADD COLUMN amount REAL DEFAULT 0"
                )
                conn.commit()
                self.logger.info("Amount column added successfully")
            else:
                self.logger.debug("Amount column already exists")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add amount column: {e}", exc_info=True)
            raise DatabaseException("migrate_add_amount_column", str(e))

    def migrate_add_timestamps(self) -> None:
        """
        기존 테이블에 타임스탬프 컬럼을 추가하는 마이그레이션
        (이미 존재하는 경우 무시)
        """
        try:
            conn = self.db_conn.get_connection()

            tables = ["data_stocks", "data_etfs"]

            for table in tables:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                if "created_at" not in columns:
                    self.logger.info(f"Adding created_at to {table}")
                    conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )

                if "updated_at" not in columns:
                    self.logger.info(f"Adding updated_at to {table}")
                    conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )

            conn.commit()
            self.logger.info("Timestamp columns migration completed")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add timestamp columns: {e}", exc_info=True)
            raise DatabaseException("migrate_add_timestamps", str(e))

    def run_all_migrations(self) -> None:
        """모든 마이그레이션을 실행합니다."""
        try:
            self.logger.info("Running all migrations")

            # 테이블 생성
            self.create_tables()

            # 추가 마이그레이션
            self.migrate_add_amount_column()
            self.migrate_add_timestamps()

            # ✅ NEW: 최적화 인덱스 추가
            self.migrate_add_optimized_indexes()

            self.logger.info("All migrations completed successfully")

        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            raise

    def drop_all_tables(self) -> None:
        """
        모든 테이블을 삭제합니다.

        주의: 이 메서드는 모든 데이터를 삭제합니다!
        """
        try:
            self.logger.warning("Dropping all tables - ALL DATA WILL BE LOST")

            conn = self.db_conn.get_connection()

            with conn:
                # 외래 키 제약 조건 임시 비활성화
                conn.execute("PRAGMA foreign_keys = OFF")

                # 모든 테이블 삭제
                tables = [
                    "data_etf_holdings",
                    "data_etfs",
                    "data_stocks",
                    "config_exclusions",
                    "config_themes",
                ]

                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
                    self.logger.debug(f"Dropped table: {table}")

                # 외래 키 제약 조건 재활성화
                conn.execute("PRAGMA foreign_keys = ON")

            self.logger.warning("All tables dropped")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise DatabaseException("drop_all_tables", str(e))

    def is_database_empty(self) -> bool:
        """데이터베이스가 비어있는지 확인합니다."""
        try:
            conn = self.db_conn.get_connection()
            cursor = conn.cursor()

            # ETF 테이블에 데이터가 있는지 확인
            cursor.execute("SELECT COUNT(*) FROM data_etfs")
            count = cursor.fetchone()[0]

            return count == 0

        except sqlite3.Error:
            # 테이블이 존재하지 않으면 비어있는 것으로 간주
            return True

    def get_database_info(self) -> dict:
        """데이터베이스 정보를 반환합니다."""
        try:
            conn = self.db_conn.get_connection()
            cursor = conn.cursor()

            info = {}

            # 테이블별 레코드 수
            tables = [
                "config_themes",
                "config_exclusions",
                "data_stocks",
                "data_etfs",
                "data_etf_holdings",
            ]

            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info[table] = count
                except sqlite3.Error:
                    info[table] = 0

            return info

        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}", exc_info=True)
            return {}

    def analyze_query_plan(self, query: str, params: tuple = ()) -> None:
        """
        쿼리 실행 계획을 분석하여 인덱스 사용 여부를 확인합니다.

        ✅ 개발/디버깅 용도: 쿼리 최적화 확인

        Args:
            query: 분석할 SQL 쿼리
            params: 쿼리 파라미터
        """
        try:
            conn = self.db_conn.get_connection()
            cursor = conn.cursor()

            # EXPLAIN QUERY PLAN 실행
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor.execute(explain_query, params)

            self.logger.info("Query Plan Analysis:")
            self.logger.info(f"Query: {query}")

            for row in cursor.fetchall():
                # SQLite EXPLAIN QUERY PLAN 결과 출력
                self.logger.info(f"  {row}")

            cursor.close()

        except sqlite3.Error as e:
            self.logger.error(f"Failed to analyze query plan: {e}", exc_info=True)

    def get_index_usage_stats(self) -> dict:
        """
        인덱스 사용 통계를 반환합니다.

        Returns:
            인덱스 정보 딕셔너리
        """
        try:
            conn = self.db_conn.get_connection()
            cursor = conn.cursor()

            # 모든 인덱스 조회
            cursor.execute("""
                SELECT name, tbl_name 
                FROM sqlite_master 
                WHERE type = 'index' 
                  AND sql IS NOT NULL
                ORDER BY tbl_name, name
            """)

            indexes = {}
            for row in cursor.fetchall():
                index_name = row[0]
                table_name = row[1]

                if table_name not in indexes:
                    indexes[table_name] = []

                indexes[table_name].append(index_name)

            cursor.close()
            return indexes

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get index stats: {e}", exc_info=True)
            return {}

    def migrate_add_optimized_indexes(self) -> None:
        """
        ✅ Medium Priority 마이그레이션: 최적화된 인덱스 추가

        기존 데이터베이스에 새로운 인덱스만 추가합니다.
        """
        try:
            self.logger.info("Adding optimized indexes for Medium Priority...")

            conn = self.db_conn.get_connection()

            with conn:
                # 날짜 + 비중 DESC
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_date_weight_desc 
                    ON data_etf_holdings (date, weight DESC)
                """)

                # 날짜 + 금액 DESC
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_date_amount_desc 
                    ON data_etf_holdings (date, amount DESC)
                """)

                # ETF + 날짜 + 비중
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_etf_date_weight 
                    ON data_etf_holdings (etf_ticker, date, weight DESC)
                """)

                # 종목 + 날짜 + 비중
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_stock_date_weight 
                    ON data_etf_holdings (stock_ticker, date, weight DESC)
                """)

                # 커버링 인덱스
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_date_covering 
                    ON data_etf_holdings (date, etf_ticker, stock_ticker, weight, amount)
                """)

                # ETF명 검색
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_etfs_name 
                    ON data_etfs (name COLLATE NOCASE)
                """)

                # 주식명 검색
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_stocks_name 
                    ON data_stocks (name COLLATE NOCASE)
                """)

                # Config 인덱스
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_themes_name 
                    ON config_themes (name COLLATE NOCASE)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_exclusions_keyword 
                    ON config_exclusions (keyword COLLATE NOCASE)
                """)

            self.logger.info("✅ Optimized indexes added successfully")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add optimized indexes: {e}", exc_info=True)
            raise DatabaseException("migrate_add_optimized_indexes", str(e))
