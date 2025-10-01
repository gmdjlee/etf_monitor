"""
Database Connection
데이터베이스 연결을 관리합니다.
"""

import sqlite3
import threading
from typing import Optional

from config.logging_config import LoggerMixin
from config.settings import settings
from shared.exceptions import DatabaseException


class DatabaseConnection(LoggerMixin):
    """
    데이터베이스 연결 관리 클래스

    싱글톤 패턴으로 구현되어 애플리케이션 전체에서 하나의 인스턴스만 사용합니다.
    스레드 안전한 연결을 제공합니다.
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = settings.DATABASE_PATH
        self._local = threading.local()
        self._initialized = True

        self.logger.info(f"Database connection initialized: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """
        현재 스레드의 데이터베이스 연결을 반환합니다.

        각 스레드마다 독립적인 연결을 유지합니다.

        Returns:
            sqlite3.Connection: 데이터베이스 연결

        Raises:
            DatabaseException: 연결 실패 시
        """
        try:
            # 스레드 로컬 스토리지에서 연결 확인
            if not hasattr(self._local, "connection") or self._local.connection is None:
                self._local.connection = self._create_connection()

            return self._local.connection

        except Exception as e:
            self.logger.error(f"Failed to get database connection: {e}", exc_info=True)
            raise DatabaseException("get_connection", str(e))

    def _create_connection(self) -> sqlite3.Connection:
        """새로운 데이터베이스 연결을 생성합니다."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # 다중 스레드 지원
                timeout=30.0,  # 30초 타임아웃
            )

            # Row 팩토리 설정 (컬럼명으로 접근 가능)
            conn.row_factory = sqlite3.Row

            # 외래 키 제약 조건 활성화
            conn.execute("PRAGMA foreign_keys = ON")

            # WAL 모드 활성화 (성능 향상)
            conn.execute("PRAGMA journal_mode = WAL")

            self.logger.debug("New database connection created")

            return conn

        except sqlite3.Error as e:
            self.logger.error(f"Failed to create connection: {e}", exc_info=True)
            raise DatabaseException("create_connection", str(e))

    def close_connection(self) -> None:
        """현재 스레드의 데이터베이스 연결을 닫습니다."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
                self._local.connection = None
                self.logger.debug("Database connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")

    def close_all_connections(self) -> None:
        """모든 스레드의 데이터베이스 연결을 닫습니다."""
        self.close_connection()
        self.logger.info("All database connections closed")

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        쿼리를 실행하고 커서를 반환합니다.

        Args:
            query: SQL 쿼리
            params: 파라미터 튜플

        Returns:
            sqlite3.Cursor: 쿼리 결과 커서
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor

        except sqlite3.Error as e:
            self.logger.error(f"Query execution failed: {e}", exc_info=True)
            raise DatabaseException("execute_query", str(e))

    def execute_many(self, query: str, params_list: list) -> None:
        """
        여러 개의 파라미터로 쿼리를 일괄 실행합니다.

        Args:
            query: SQL 쿼리
            params_list: 파라미터 리스트
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            self.logger.error(f"Bulk execution failed: {e}", exc_info=True)
            raise DatabaseException("execute_many", str(e))

    def commit(self) -> None:
        """현재 트랜잭션을 커밋합니다."""
        try:
            conn = self.get_connection()
            conn.commit()

        except sqlite3.Error as e:
            self.logger.error(f"Commit failed: {e}", exc_info=True)
            raise DatabaseException("commit", str(e))

    def rollback(self) -> None:
        """현재 트랜잭션을 롤백합니다."""
        try:
            conn = self.get_connection()
            conn.rollback()
            self.logger.debug("Transaction rolled back")

        except sqlite3.Error as e:
            self.logger.error(f"Rollback failed: {e}", exc_info=True)
            raise DatabaseException("rollback", str(e))

    def begin_transaction(self) -> None:
        """명시적으로 트랜잭션을 시작합니다."""
        try:
            conn = self.get_connection()
            conn.execute("BEGIN")
            self.logger.debug("Transaction started")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to begin transaction: {e}", exc_info=True)
            raise DatabaseException("begin_transaction", str(e))

    def is_connected(self) -> bool:
        """데이터베이스 연결 상태를 확인합니다."""
        try:
            if not hasattr(self._local, "connection") or self._local.connection is None:
                return False

            # 간단한 쿼리로 연결 테스트
            self._local.connection.execute("SELECT 1")
            return True

        except Exception:
            return False


# 싱글톤 인스턴스
db_connection = DatabaseConnection()
