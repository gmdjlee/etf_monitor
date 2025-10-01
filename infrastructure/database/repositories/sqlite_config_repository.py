"""
SQLite Config Repository Implementation
Config 리포지토리의 SQLite 구현체입니다.
"""

import sqlite3
from typing import List

from config.logging_config import LoggerMixin
from config.settings import settings
from domain.repositories.config_repository import ConfigRepository
from infrastructure.database.connection import DatabaseConnection
from shared.exceptions import DatabaseException


class SQLiteConfigRepository(ConfigRepository, LoggerMixin):
    """
    SQLite 기반 Config 리포지토리 구현

    Args:
        db_connection: 데이터베이스 연결
    """

    def __init__(self, db_connection: DatabaseConnection):
        self.db_conn = db_connection

    # 테마 관리

    def get_all_themes(self) -> List[str]:
        """모든 테마 키워드를 조회합니다."""
        try:
            query = "SELECT name FROM config_themes ORDER BY name"

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [row["name"] for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get all themes: {e}", exc_info=True)
            raise DatabaseException("get_all_themes", str(e))

    def add_theme(self, theme: str) -> None:
        """테마 키워드를 추가합니다."""
        try:
            query = "INSERT OR IGNORE INTO config_themes (name) VALUES (?)"

            conn = self.db_conn.get_connection()
            conn.execute(query, (theme,))
            conn.commit()

            self.logger.debug(f"Added theme: {theme}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add theme: {e}", exc_info=True)
            raise DatabaseException("add_theme", str(e))

    def remove_theme(self, theme: str) -> None:
        """테마 키워드를 삭제합니다."""
        try:
            query = "DELETE FROM config_themes WHERE name = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (theme,))
            conn.commit()

            self.logger.debug(f"Removed theme: {theme}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to remove theme: {e}", exc_info=True)
            raise DatabaseException("remove_theme", str(e))

    def theme_exists(self, theme: str) -> bool:
        """테마 키워드가 존재하는지 확인합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM config_themes WHERE name = ?"

            cursor = self.db_conn.execute_query(query, (theme,))
            row = cursor.fetchone()

            return row["count"] > 0

        except sqlite3.Error as e:
            self.logger.error(f"Failed to check theme existence: {e}", exc_info=True)
            raise DatabaseException("theme_exists", str(e))

    def count_themes(self) -> int:
        """테마 키워드 개수를 반환합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM config_themes"

            cursor = self.db_conn.execute_query(query)
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count themes: {e}", exc_info=True)
            raise DatabaseException("count_themes", str(e))

    # 제외 키워드 관리

    def get_all_exclusions(self) -> List[str]:
        """모든 제외 키워드를 조회합니다."""
        try:
            query = "SELECT keyword FROM config_exclusions ORDER BY keyword"

            cursor = self.db_conn.execute_query(query)
            rows = cursor.fetchall()

            return [row["keyword"] for row in rows]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get all exclusions: {e}", exc_info=True)
            raise DatabaseException("get_all_exclusions", str(e))

    def add_exclusion(self, exclusion: str) -> None:
        """제외 키워드를 추가합니다."""
        try:
            query = "INSERT OR IGNORE INTO config_exclusions (keyword) VALUES (?)"

            conn = self.db_conn.get_connection()
            conn.execute(query, (exclusion,))
            conn.commit()

            self.logger.debug(f"Added exclusion: {exclusion}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to add exclusion: {e}", exc_info=True)
            raise DatabaseException("add_exclusion", str(e))

    def remove_exclusion(self, exclusion: str) -> None:
        """제외 키워드를 삭제합니다."""
        try:
            query = "DELETE FROM config_exclusions WHERE keyword = ?"

            conn = self.db_conn.get_connection()
            conn.execute(query, (exclusion,))
            conn.commit()

            self.logger.debug(f"Removed exclusion: {exclusion}")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to remove exclusion: {e}", exc_info=True)
            raise DatabaseException("remove_exclusion", str(e))

    def exclusion_exists(self, exclusion: str) -> bool:
        """제외 키워드가 존재하는지 확인합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM config_exclusions WHERE keyword = ?"

            cursor = self.db_conn.execute_query(query, (exclusion,))
            row = cursor.fetchone()

            return row["count"] > 0

        except sqlite3.Error as e:
            self.logger.error(
                f"Failed to check exclusion existence: {e}", exc_info=True
            )
            raise DatabaseException("exclusion_exists", str(e))

    def count_exclusions(self) -> int:
        """제외 키워드 개수를 반환합니다."""
        try:
            query = "SELECT COUNT(*) as count FROM config_exclusions"

            cursor = self.db_conn.execute_query(query)
            row = cursor.fetchone()

            return row["count"]

        except sqlite3.Error as e:
            self.logger.error(f"Failed to count exclusions: {e}", exc_info=True)
            raise DatabaseException("count_exclusions", str(e))

    # 일괄 작업

    def set_themes(self, themes: List[str]) -> None:
        """테마 키워드를 일괄 설정합니다 (기존 데이터 삭제 후 추가)."""
        try:
            conn = self.db_conn.get_connection()

            # 트랜잭션 시작
            conn.execute("BEGIN")

            try:
                # 기존 데이터 삭제
                conn.execute("DELETE FROM config_themes")

                # 새 데이터 삽입
                if themes:
                    query = "INSERT INTO config_themes (name) VALUES (?)"
                    conn.executemany(query, [(theme,) for theme in themes])

                conn.commit()
                self.logger.info(f"Set {len(themes)} themes")

            except Exception as e:
                conn.rollback()
                raise e

        except sqlite3.Error as e:
            self.logger.error(f"Failed to set themes: {e}", exc_info=True)
            raise DatabaseException("set_themes", str(e))

    def set_exclusions(self, exclusions: List[str]) -> None:
        """제외 키워드를 일괄 설정합니다 (기존 데이터 삭제 후 추가)."""
        try:
            conn = self.db_conn.get_connection()

            # 트랜잭션 시작
            conn.execute("BEGIN")

            try:
                # 기존 데이터 삭제
                conn.execute("DELETE FROM config_exclusions")

                # 새 데이터 삽입
                if exclusions:
                    query = "INSERT INTO config_exclusions (keyword) VALUES (?)"
                    conn.executemany(query, [(exclusion,) for exclusion in exclusions])

                conn.commit()
                self.logger.info(f"Set {len(exclusions)} exclusions")

            except Exception as e:
                conn.rollback()
                raise e

        except sqlite3.Error as e:
            self.logger.error(f"Failed to set exclusions: {e}", exc_info=True)
            raise DatabaseException("set_exclusions", str(e))

    def clear_themes(self) -> None:
        """모든 테마 키워드를 삭제합니다."""
        try:
            query = "DELETE FROM config_themes"

            conn = self.db_conn.get_connection()
            conn.execute(query)
            conn.commit()

            self.logger.info("Cleared all themes")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to clear themes: {e}", exc_info=True)
            raise DatabaseException("clear_themes", str(e))

    def clear_exclusions(self) -> None:
        """모든 제외 키워드를 삭제합니다."""
        try:
            query = "DELETE FROM config_exclusions"

            conn = self.db_conn.get_connection()
            conn.execute(query)
            conn.commit()

            self.logger.info("Cleared all exclusions")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to clear exclusions: {e}", exc_info=True)
            raise DatabaseException("clear_exclusions", str(e))

    def reset_to_defaults(self) -> None:
        """설정을 기본값으로 리셋합니다."""
        try:
            self.logger.info("Resetting config to defaults")

            # 기본 테마와 제외 키워드 설정
            self.set_themes(settings.DEFAULT_THEMES)
            self.set_exclusions(settings.DEFAULT_EXCLUSIONS)

            self.logger.info("Config reset to defaults completed")

        except Exception as e:
            self.logger.error(f"Failed to reset to defaults: {e}", exc_info=True)
            raise DatabaseException("reset_to_defaults", str(e))

    # 설정 상태 확인

    def is_empty(self) -> bool:
        """설정이 비어있는지 확인합니다."""
        try:
            theme_count = self.count_themes()
            exclusion_count = self.count_exclusions()

            return theme_count == 0 and exclusion_count == 0

        except Exception as e:
            self.logger.error(f"Failed to check if empty: {e}", exc_info=True)
            return True

    def has_default_config(self) -> bool:
        """기본 설정이 로드되어 있는지 확인합니다."""
        try:
            # 테마와 제외 키워드가 하나라도 있으면 설정이 로드된 것으로 간주
            theme_count = self.count_themes()
            exclusion_count = self.count_exclusions()

            return theme_count > 0 or exclusion_count > 0

        except Exception as e:
            self.logger.error(f"Failed to check default config: {e}", exc_info=True)
            return False
