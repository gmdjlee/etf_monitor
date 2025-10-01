"""
SQLite ETF Repository Implementation
ETF 리포지토리의 SQLite 구현체입니다.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from config.logging_config import LoggerMixin
from domain.entities.etf import ETF
from domain.entities.holding import Holding
from domain.repositories.etf_repository import ETFRepository
from shared.exceptions import DatabaseException
from shared.utils.date_utils import from_date_string, to_date_string

from infrastructure.cache import cached, invalidate_cache
from infrastructure.database.connection import DatabaseConnection


class SQLiteETFRepository(ETFRepository, LoggerMixin):
    """
    SQLite 기반 ETF 리포지토리 구현

    Args:
        db_connection: 데이터베이스 연결
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db_conn = db_connection

    # ETF 기본 조회

    # ✅ 캐시 무효화: 데이터 저장 시
    def save(self, entity: ETF) -> None:
        """
        ETF를 저장합니다.

        ✅ 캐시 무효화: ETF 관련 캐시 삭제
        """
        try:
            query = """
                INSERT OR REPLACE INTO data_etfs (ticker, name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """

            conn = self.db_conn.get_connection()
            conn.execute(query, (entity.ticker, entity.name))
            conn.commit()

            # ✅ 캐시 무효화
            invalidate_cache("etf:*")

            self.logger.debug(f"Saved ETF: {entity.ticker} (cache invalidated)")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save ETF: {e}", exc_info=True)
            raise DatabaseException("save", str(e))

    # ✅ 캐시 무효화: 일괄 저장 시
    def save_all(self, entities: List[ETF]) -> None:
        """
        여러 ETF를 일괄 저장합니다.

        ✅ 캐시 무효화: ETF 관련 캐시 삭제
        """
        try:
            query = """
                INSERT OR IGNORE INTO data_etfs (ticker, name)
                VALUES (?, ?)
            """

            data = [(etf.ticker, etf.name) for etf in entities]

            conn = self.db_conn.get_connection()
            conn.executemany(query, data)
            conn.commit()

            # ✅ 캐시 무효화
            invalidate_cache("etf:*")

            self.logger.info(f"Saved {len(entities)} ETFs (cache invalidated)")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save ETFs: {e}", exc_info=True)
            raise DatabaseException("save_all", str(e))

    def find_by_id(self, id: str) -> Optional[ETF]:
        """ID(ticker)로 ETF를 조회합니다."""
        return self.find_by_ticker(id)

    # ✅ 캐싱 적용: 개별 ETF 조회 (10분 캐시)
    @cached(ttl=600, key_prefix="etf")
    def find_by_ticker(self, ticker: str) -> Optional[ETF]:
        """
        티커로 ETF를 조회합니다.

        ✅ 캐싱: 10분간 캐시 유지
        """
        try:
            query = """
                SELECT ticker, name
                FROM data_etfs
                WHERE ticker = ?
            """

            cursor = self.db_conn.execute_query(query, (ticker,))
            row = cursor.fetchone()

            if row:
                return ETF.create(ticker=row["ticker"], name=row["name"])

            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find ETF by ticker: {e}", exc_info=True)
            raise DatabaseException("find_by_ticker", str(e))

    def find_by_name(self, name: str) -> Optional[ETF]:
        """ETF명으로 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_etfs
                WHERE name = ?
            """

            cursor = self.db_conn.execute_query(query, (name,))
            row = cursor.fetchone()

            if row:
                return ETF.create(ticker=row["ticker"], name=row["name"])

            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find ETF by name: {e}", exc_info=True)
            raise DatabaseException("find_by_name", str(e))

    def find_by_name_like(self, keyword: str) -> List[ETF]:
        """ETF명에 키워드가 포함된 ETF들을 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_etfs
                WHERE name LIKE ?
                ORDER BY name
            """

            cursor = self.db_conn.execute_query(query, (f"%{keyword}%",))
            rows = cursor.fetchall()

            return [ETF.create(ticker=row["ticker"], name=row["name"]) for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find ETFs by name like: {e}", exc_info=True)
            raise DatabaseException("find_by_name_like", str(e))

    # ✅ 캐싱 적용: 액티브 ETF 목록 (5분 캐시)
    @cached(ttl=300, key_prefix="etf:active")
    def find_active_etfs(self) -> List[ETF]:
        """
        액티브 ETF들을 조회합니다.

        ✅ 캐싱: 5분간 캐시 유지
        """
        try:
            query = """
                SELECT ticker, name
                FROM data_etfs
                WHERE name LIKE '%액티브%'
                ORDER BY name
            """

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [ETF.create(ticker=row["ticker"], name=row["name"]) for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find active ETFs: {e}", exc_info=True)
            raise DatabaseException("find_active_etfs", str(e))

    # ✅ 캐싱 적용: ETF 목록 (5분 캐시)
    @cached(ttl=300, key_prefix="etf")
    def find_all(self) -> List[ETF]:
        """
        모든 ETF를 조회합니다.

        ✅ 캐싱: 5분간 캐시 유지
        ETF 목록은 자주 변경되지 않으므로 캐싱 효과가 큼
        """
        try:
            query = """
                SELECT ticker, name
                FROM data_etfs
                ORDER BY name
            """

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [ETF.create(ticker=row["ticker"], name=row["name"]) for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find all ETFs: {e}", exc_info=True)
            raise DatabaseException("find_all", str(e))

    def exists(self, id: str) -> bool:
        """ETF가 존재하는지 확인합니다."""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM data_etfs
                WHERE ticker = ?
            """

            cursor = self.db_conn.execute_query(query, (id,))
            row = cursor.fetchone()

            return row["count"] > 0

        except sqlite3.Error as e:
            self.logger.error(f"Failed to check ETF existence: {e}", exc_info=True)
            raise DatabaseException("exists", str(e))

    def delete(self, id: str) -> None:
        """ETF를 삭제합니다."""
        try:
            query = "DELETE FROM data_etfs WHERE ticker = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (id,))
            conn.commit()

            self.logger.debug(f"Deleted ETF: {id}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete ETF: {e}", exc_info=True)
            raise DatabaseException("delete", str(e))

    def delete_all(self) -> None:
        """모든 ETF를 삭제합니다."""
        try:
            query = "DELETE FROM data_etfs"

            conn = self.db_conn.get_connection()
            conn.execute(query)
            conn.commit()

            self.logger.warning("Deleted all ETFs")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete all ETFs: {e}", exc_info=True)
            raise DatabaseException("delete_all", str(e))

    def count(self) -> int:
        """전체 ETF 개수를 반환합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM data_etfs"

            cursor = self.db_conn.execute_query(query)
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count ETFs: {e}", exc_info=True)
            raise DatabaseException("count", str(e))

    # 보유 종목(Holdings) 관련

    def save_holding(self, holding: Holding) -> None:
        """보유 종목 정보를 저장합니다."""
        try:
            query = """
                INSERT OR REPLACE INTO data_etf_holdings 
                (etf_ticker, stock_ticker, date, weight, amount)
                VALUES (?, ?, ?, ?, ?)
            """

            conn = self.db_conn.get_connection()
            conn.execute(
                query,
                (
                    holding.etf_ticker,
                    holding.stock_ticker,
                    to_date_string(holding.date),
                    holding.weight,
                    holding.amount,
                ),
            )
            conn.commit()

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save holding: {e}", exc_info=True)
            raise DatabaseException("save_holding", str(e))

    # ✅ 캐시 무효화: Holdings 저장 시
    def save_holdings(self, holdings: List[Holding]) -> None:
        """
        여러 보유 종목 정보를 일괄 저장합니다.

        ✅ 개선: 배치 캐시 무효화
        """
        try:
            query = """
                INSERT OR IGNORE INTO data_etf_holdings 
                (etf_ticker, stock_ticker, date, weight, amount)
                VALUES (?, ?, ?, ?, ?)
            """

            data = [
                (
                    h.etf_ticker,
                    h.stock_ticker,
                    to_date_string(h.date),
                    h.weight,
                    h.amount,
                )
                for h in holdings
            ]

            conn = self.db_conn.get_connection()
            conn.executemany(query, data)
            conn.commit()

            # ✅ 개선: 배치 캐시 무효화
            if holdings:
                from infrastructure.cache import cache_manager

                etf_tickers = set(h.etf_ticker for h in holdings)
                patterns = []

                for ticker in etf_tickers:
                    patterns.append(f"etf:holdings:{ticker}:*")
                    patterns.append(f"etf:dates:{ticker}")

                # 한 번에 무효화
                deleted_count = cache_manager.invalidate_multiple_patterns(patterns)

                self.logger.debug(
                    f"Saved {len(holdings)} holdings, "
                    f"invalidated {deleted_count} cache entries"
                )

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save holdings: {e}", exc_info=True)
            raise DatabaseException("save_holdings", str(e))

    def find_holdings_by_etf_and_date(
        self, etf_ticker: str, date: datetime
    ) -> List[Holding]:
        """특정 ETF의 특정 날짜 보유 종목을 조회합니다."""
        try:
            query = """
                SELECT h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount, s.name as stock_name
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.etf_ticker = ? AND h.date = ?
                ORDER BY h.weight DESC
            """

            cursor = self.db_conn.execute_query(
                query, (etf_ticker, to_date_string(date))
            )
            rows = cursor.fetchall()

            return [
                Holding.create(
                    etf_ticker=row["etf_ticker"],
                    stock_ticker=row["stock_ticker"],
                    date=from_date_string(row["date"]),
                    weight=row["weight"],
                    amount=row["amount"],
                    stock_name=row["stock_name"],
                )
                for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find holdings: {e}", exc_info=True)
            raise DatabaseException("find_holdings_by_etf_and_date", str(e))

    def find_holdings_by_stock_and_date(
        self, stock_ticker: str, date: datetime
    ) -> List[Holding]:
        """특정 종목을 보유한 모든 ETF를 특정 날짜 기준으로 조회합니다."""
        try:
            query = """
                SELECT h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount, s.name as stock_name
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.stock_ticker = ? AND h.date = ?
                ORDER BY h.weight DESC
            """

            cursor = self.db_conn.execute_query(
                query, (stock_ticker, to_date_string(date))
            )
            rows = cursor.fetchall()

            return [
                Holding.create(
                    etf_ticker=row["etf_ticker"],
                    stock_ticker=row["stock_ticker"],
                    date=from_date_string(row["date"]),
                    weight=row["weight"],
                    amount=row["amount"],
                    stock_name=row["stock_name"],
                )
                for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find holdings by stock: {e}", exc_info=True)
            raise DatabaseException("find_holdings_by_stock_and_date", str(e))

    def find_holdings_by_date(self, date: datetime) -> List[Holding]:
        """특정 날짜의 모든 보유 종목을 조회합니다."""
        try:
            query = """
                SELECT h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount, s.name as stock_name
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.date = ?
            """

            cursor = self.db_conn.execute_query(query, (to_date_string(date),))
            rows = cursor.fetchall()

            return [
                Holding.create(
                    etf_ticker=row["etf_ticker"],
                    stock_ticker=row["stock_ticker"],
                    date=from_date_string(row["date"]),
                    weight=row["weight"],
                    amount=row["amount"],
                    stock_name=row["stock_name"],
                )
                for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find holdings by date: {e}", exc_info=True)
            raise DatabaseException("find_holdings_by_date", str(e))

    def find_weight_history(self, etf_ticker: str, stock_ticker: str) -> List[Holding]:
        """특정 ETF 내 특정 종목의 비중 추이를 조회합니다."""
        try:
            query = """
                SELECT h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount, s.name as stock_name
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.etf_ticker = ? AND h.stock_ticker = ?
                ORDER BY h.date ASC
            """

            cursor = self.db_conn.execute_query(query, (etf_ticker, stock_ticker))
            rows = cursor.fetchall()

            return [
                Holding.create(
                    etf_ticker=row["etf_ticker"],
                    stock_ticker=row["stock_ticker"],
                    date=from_date_string(row["date"]),
                    weight=row["weight"],
                    amount=row["amount"],
                    stock_name=row["stock_name"],
                )
                for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find weight history: {e}", exc_info=True)
            raise DatabaseException("find_weight_history", str(e))

    # 날짜 관련

    def get_latest_date(self) -> Optional[datetime]:
        """보유 종목 데이터의 가장 최신 날짜를 조회합니다."""
        try:
            query = "SELECT MAX(date) as latest FROM data_etf_holdings"

            cursor = self.db_conn.execute_query(query)
            row = cursor.fetchone()

            if row and row["latest"]:
                return from_date_string(row["latest"])

            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest date: {e}", exc_info=True)
            raise DatabaseException("get_latest_date", str(e))

    # ✅ 캐싱 적용: 날짜 목록 (10분 캐시)
    @cached(ttl=600, key_prefix="etf:dates")
    def get_available_dates(self, etf_ticker: str) -> List[datetime]:
        """
        특정 ETF의 데이터가 있는 모든 날짜를 조회합니다.

        ✅ 캐싱: 10분간 캐시 유지
        """
        try:
            query = """
                SELECT DISTINCT date
                FROM data_etf_holdings
                WHERE etf_ticker = ?
                ORDER BY date DESC
            """

            cursor = self.db_conn.execute_query(query, (etf_ticker,))
            rows = cursor.fetchall()

            return [from_date_string(row["date"]) for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get available dates: {e}", exc_info=True)
            raise DatabaseException("get_available_dates", str(e))

    def get_all_available_dates(self) -> List[datetime]:
        """전체 보유 종목 데이터가 있는 모든 날짜를 조회합니다."""
        try:
            query = """
                SELECT DISTINCT date
                FROM data_etf_holdings
                ORDER BY date DESC
            """

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [from_date_string(row["date"]) for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get all available dates: {e}", exc_info=True)
            raise DatabaseException("get_all_available_dates", str(e))

    def has_data_for_date(self, date: datetime) -> bool:
        """특정 날짜의 데이터가 존재하는지 확인합니다."""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM data_etf_holdings
                WHERE date = ?
            """

            cursor = self.db_conn.execute_query(query, (to_date_string(date),))
            row = cursor.fetchone()

            return row["count"] > 0

        except sqlite3.Error as e:
            self.logger.error(f"Failed to check data for date: {e}", exc_info=True)
            raise DatabaseException("has_data_for_date", str(e))

    # 통계 관련

    def count_holdings_by_etf(self, etf_ticker: str, date: datetime) -> int:
        """특정 ETF의 특정 날짜 보유 종목 개수를 반환합니다."""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM data_etf_holdings
                WHERE etf_ticker = ? AND date = ?
            """

            cursor = self.db_conn.execute_query(
                query, (etf_ticker, to_date_string(date))
            )
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count holdings: {e}", exc_info=True)
            raise DatabaseException("count_holdings_by_etf", str(e))

    def count_etfs_holding_stock(self, stock_ticker: str, date: datetime) -> int:
        """특정 종목을 보유한 ETF 개수를 반환합니다."""
        try:
            query = """
                SELECT COUNT(DISTINCT etf_ticker) as count
                FROM data_etf_holdings
                WHERE stock_ticker = ? AND date = ?
            """

            cursor = self.db_conn.execute_query(
                query, (stock_ticker, to_date_string(date))
            )
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count ETFs holding stock: {e}", exc_info=True)
            raise DatabaseException("count_etfs_holding_stock", str(e))

    def delete_holdings_by_date(self, date: datetime) -> None:
        """특정 날짜의 모든 보유 종목 데이터를 삭제합니다."""
        try:
            query = "DELETE FROM data_etf_holdings WHERE date = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (to_date_string(date),))
            conn.commit()

            self.logger.info(f"Deleted holdings for date: {to_date_string(date)}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete holdings by date: {e}", exc_info=True)
            raise DatabaseException("delete_holdings_by_date", str(e))

    def delete_holdings_by_etf(self, etf_ticker: str) -> None:
        """특정 ETF의 모든 보유 종목 데이터를 삭제합니다."""
        try:
            query = "DELETE FROM data_etf_holdings WHERE etf_ticker = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (etf_ticker,))
            conn.commit()

            self.logger.info(f"Deleted holdings for ETF: {etf_ticker}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete holdings by ETF: {e}", exc_info=True)
            raise DatabaseException("delete_holdings_by_etf", str(e))

    def find_by_tickers(self, tickers: List[str]) -> List[ETF]:
        """
        여러 티커에 해당하는 ETF들을 한 번에 조회합니다.

        ✅ N+1 쿼리 방지: 단일 쿼리로 여러 ETF를 한 번에 조회
        """
        try:
            if not tickers:
                return []

            # SQL IN 절을 위한 플레이스홀더 생성
            placeholders = ",".join(["?" for _ in tickers])
            query = f"""
                SELECT ticker, name
                FROM data_etfs
                WHERE ticker IN ({placeholders})
                ORDER BY name
            """

            cursor = self.db_conn.execute_query(query, tuple(tickers))
            rows = cursor.fetchall()

            etfs = [ETF.create(ticker=row["ticker"], name=row["name"]) for row in rows]

            self.logger.debug(f"Found {len(etfs)} ETFs from {len(tickers)} tickers")
            return etfs

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find ETFs by tickers: {e}", exc_info=True)
            raise DatabaseException("find_by_tickers", str(e))
