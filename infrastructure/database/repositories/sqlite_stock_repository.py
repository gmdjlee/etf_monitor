"""
SQLite Stock Repository Implementation
Stock 리포지토리의 SQLite 구현체입니다.
"""

import sqlite3
from typing import List, Optional

from config.logging_config import LoggerMixin
from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from shared.exceptions import DatabaseException

from infrastructure.database.connection import DatabaseConnection


class SQLiteStockRepository(StockRepository, LoggerMixin):
    """
    SQLite 기반 Stock 리포지토리 구현

    Args:
        db_connection: 데이터베이스 연결
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db_conn = db_connection

    def save(self, entity: Stock) -> None:
        """주식을 저장합니다."""
        try:
            query = """
                INSERT OR REPLACE INTO data_stocks (ticker, name, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """

            conn = self.db_conn.get_connection()
            conn.execute(query, (entity.ticker, entity.name))
            conn.commit()

            self.logger.debug(f"Saved stock: {entity.ticker}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save stock: {e}", exc_info=True)
            raise DatabaseException("save", str(e))

    def save_all(self, entities: List[Stock]) -> None:
        """여러 주식을 일괄 저장합니다."""
        try:
            query = """
                INSERT OR IGNORE INTO data_stocks (ticker, name)
                VALUES (?, ?)
            """

            data = [(stock.ticker, stock.name) for stock in entities]

            conn = self.db_conn.get_connection()
            conn.executemany(query, data)
            conn.commit()

            self.logger.info(f"Saved {len(entities)} stocks")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save stocks: {e}", exc_info=True)
            raise DatabaseException("save_all", str(e))

    def find_by_id(self, id: str) -> Optional[Stock]:
        """ID(ticker)로 주식을 조회합니다."""
        return self.find_by_ticker(id)

    def find_by_ticker(self, ticker: str) -> Optional[Stock]:
        """티커로 주식을 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_stocks
                WHERE ticker = ?
            """

            cursor = self.db_conn.execute_query(query, (ticker,))
            row = cursor.fetchone()

            if row:
                return Stock.create(ticker=row["ticker"], name=row["name"])

            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find stock by ticker: {e}", exc_info=True)
            raise DatabaseException("find_by_ticker", str(e))

    def find_by_name(self, name: str) -> Optional[Stock]:
        """종목명으로 주식을 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_stocks
                WHERE name = ?
            """

            cursor = self.db_conn.execute_query(query, (name,))
            row = cursor.fetchone()

            if row:
                return Stock.create(ticker=row["ticker"], name=row["name"])

            return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find stock by name: {e}", exc_info=True)
            raise DatabaseException("find_by_name", str(e))

    def find_by_name_like(self, keyword: str) -> List[Stock]:
        """종목명에 키워드가 포함된 주식들을 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_stocks
                WHERE name LIKE ?
                ORDER BY name
            """

            cursor = self.db_conn.execute_query(query, (f"%{keyword}%",))
            rows = cursor.fetchall()

            return [
                Stock.create(ticker=row["ticker"], name=row["name"]) for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find stocks by name like: {e}", exc_info=True)
            raise DatabaseException("find_by_name_like", str(e))

    def find_by_tickers(self, tickers: List[str]) -> List[Stock]:
        """
        여러 티커에 해당하는 주식들을 조회합니다.

        ✅ 개선: 빈 리스트 체크 및 로깅 추가

        Args:
            tickers: 종목 코드 리스트

        Returns:
            찾은 Stock 엔티티 리스트
        """
        try:
            if not tickers:
                return []

            # SQL IN 절을 위한 플레이스홀더 생성
            placeholders = ",".join(["?" for _ in tickers])
            query = f"""
                SELECT ticker, name
                FROM data_stocks
                WHERE ticker IN ({placeholders})
                ORDER BY ticker
            """

            cursor = self.db_conn.execute_query(query, tuple(tickers))
            rows = cursor.fetchall()

            stocks = [
                Stock.create(ticker=row["ticker"], name=row["name"]) for row in rows
            ]

            # ✅ 추가: 로깅 및 누락된 ticker 확인
            found_tickers = {stock.ticker for stock in stocks}
            missing_tickers = set(tickers) - found_tickers

            if missing_tickers:
                self.logger.warning(
                    f"Some tickers not found in database: {missing_tickers}"
                )

            self.logger.debug(f"Found {len(stocks)} stocks from {len(tickers)} tickers")
            return stocks

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find stocks by tickers: {e}", exc_info=True)
            raise DatabaseException("find_by_tickers", str(e))

    def find_all(self) -> List[Stock]:
        """모든 주식을 조회합니다."""
        try:
            query = """
                SELECT ticker, name
                FROM data_stocks
                ORDER BY ticker
            """

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [
                Stock.create(ticker=row["ticker"], name=row["name"]) for row in rows
            ]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to find all stocks: {e}", exc_info=True)
            raise DatabaseException("find_all", str(e))

    def find_all_by_market(self, market: str) -> List[Stock]:
        """
        특정 시장의 모든 주식을 조회합니다.

        Note: 현재 구현에서는 시장 정보를 저장하지 않으므로 빈 리스트 반환
        """
        self.logger.warning(f"Market filtering not implemented: {market}")
        return []

    def exists(self, id: str) -> bool:
        """주식이 존재하는지 확인합니다."""
        return self.exists_by_ticker(id)

    def exists_by_ticker(self, ticker: str) -> bool:
        """티커에 해당하는 주식이 존재하는지 확인합니다."""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM data_stocks
                WHERE ticker = ?
            """

            cursor = self.db_conn.execute_query(query, (ticker,))
            row = cursor.fetchone()

            return row["count"] > 0

        except sqlite3.Error as e:
            self.logger.error(f"Failed to check stock existence: {e}", exc_info=True)
            raise DatabaseException("exists_by_ticker", str(e))

    def delete(self, id: str) -> None:
        """주식을 삭제합니다."""
        try:
            query = "DELETE FROM data_stocks WHERE ticker = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (id,))
            conn.commit()

            self.logger.debug(f"Deleted stock: {id}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete stock: {e}", exc_info=True)
            raise DatabaseException("delete", str(e))

    def delete_all(self) -> None:
        """모든 주식을 삭제합니다."""
        try:
            query = "DELETE FROM data_stocks"

            conn = self.db_conn.get_connection()
            conn.execute(query)
            conn.commit()

            self.logger.warning("Deleted all stocks")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete all stocks: {e}", exc_info=True)
            raise DatabaseException("delete_all", str(e))

    def count(self) -> int:
        """전체 주식 개수를 반환합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM data_stocks"

            cursor = self.db_conn.execute_query(query)
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count stocks: {e}", exc_info=True)
            raise DatabaseException("count", str(e))

    def count_by_market(self, market: str) -> int:
        """
        특정 시장의 주식 개수를 반환합니다.

        Note: 현재 구현에서는 시장 정보를 저장하지 않으므로 0 반환
        """
        self.logger.warning(f"Market counting not implemented: {market}")
        return 0
