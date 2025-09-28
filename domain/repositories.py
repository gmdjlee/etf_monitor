from typing import Dict, List, Optional

from database.database_manager import DatabaseManager

from domain.models import ETF, ETFHolding, Stock


# --- 설정 리포지토리 ---
class ConfigRepository:
    """설정 데이터(테마, 제외 키워드)에 대한 DB 작업을 처리합니다."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_themes(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM config_themes ORDER BY name")
            return [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]

    def add_theme(self, name: str):
        conn = self.db_manager.get_connection()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO config_themes (name) VALUES (?)", (name,)
            )

    def delete_theme(self, theme_id: int):
        conn = self.db_manager.get_connection()
        with conn:
            conn.execute("DELETE FROM config_themes WHERE id = ?", (theme_id,))

    def get_exclusions(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, keyword FROM config_exclusions ORDER BY keyword")
            return [
                {"id": row["id"], "keyword": row["keyword"]}
                for row in cursor.fetchall()
            ]

    def add_exclusion(self, keyword: str):
        conn = self.db_manager.get_connection()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO config_exclusions (keyword) VALUES (?)",
                (keyword,),
            )

    def delete_exclusion(self, exclusion_id: int):
        conn = self.db_manager.get_connection()
        with conn:
            conn.execute("DELETE FROM config_exclusions WHERE id = ?", (exclusion_id,))


# --- 데이터 리포지토리 ---
class StockRepository:
    """주식 데이터에 대한 DB 작업을 처리합니다."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def bulk_insert_stocks(self, stocks: List[Stock]):
        conn = self.db_manager.get_connection()
        stock_data = [(s.ticker, s.name) for s in stocks]
        with conn:
            conn.executemany(
                "INSERT OR IGNORE INTO data_stocks (ticker, name) VALUES (?, ?)",
                stock_data,
            )


class EtfRepository:
    """ETF 및 보유 종목 데이터에 대한 DB 작업을 처리합니다."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def add_etf(self, etf: ETF):
        conn = self.db_manager.get_connection()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO data_etfs (ticker, name) VALUES (?, ?)",
                (etf.ticker, etf.name),
            )

    def get_all_etfs(self) -> List[ETF]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticker, name FROM data_etfs ORDER BY name")
            return [ETF(row["ticker"], row["name"]) for row in cursor.fetchall()]

    def bulk_insert_holdings(self, holdings: List[ETFHolding]):
        conn = self.db_manager.get_connection()
        holding_data = [
            (h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount) for h in holdings
        ]
        with conn:
            conn.executemany(
                "INSERT OR IGNORE INTO data_etf_holdings (etf_ticker, stock_ticker, date, weight, amount) VALUES (?, ?, ?, ?, ?)",
                holding_data,
            )

    def get_latest_date(self) -> Optional[str]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(date) FROM data_etf_holdings")
            result = cursor.fetchone()
            return result[0] if result and result[0] else None

    def get_etf_holdings_by_date(self, etf_ticker: str, date: str) -> List[ETFHolding]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT h.etf_ticker, h.stock_ticker, h.date, h.weight, h.amount, s.name as stock_name
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.etf_ticker = ? AND h.date = ?
            """
            cursor.execute(query, (etf_ticker, date))
            results = []
            for row in cursor.fetchall():
                results.append(
                    ETFHolding(
                        etf_ticker=row["etf_ticker"],
                        stock_ticker=row["stock_ticker"],
                        date=row["date"],
                        weight=row["weight"],
                        amount=row["amount"],
                        stock_name=row["stock_name"],
                    )
                )
            return results

    def get_available_dates_for_etf(self, etf_ticker: str) -> List[str]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT date FROM data_etf_holdings WHERE etf_ticker = ? ORDER BY date DESC",
                (etf_ticker,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_stock_weight_history(
        self, etf_ticker: str, stock_ticker: str
    ) -> List[Dict]:
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()
            query = """
                SELECT date, weight, amount
                FROM data_etf_holdings
                WHERE etf_ticker = ? AND stock_ticker = ?
                ORDER BY date ASC
            """
            cursor.execute(query, (etf_ticker, stock_ticker))
            return [
                {"date": row["date"], "weight": row["weight"], "amount": row["amount"]}
                for row in cursor.fetchall()
            ]
