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

    def get_duplicate_stock_statistics(self) -> Dict:
        """전체 ETF에서 중복 종목 통계를 반환합니다."""
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()

            # 최신 날짜 조회
            cursor.execute("SELECT MAX(date) FROM data_etf_holdings")
            latest_date = cursor.fetchone()[0]

            if not latest_date:
                return {"date": None, "stocks": []}

            # 중복 종목 통계 조회
            query = """
                SELECT 
                    s.ticker,
                    s.name,
                    COUNT(DISTINCT h.etf_ticker) as etf_count,
                    GROUP_CONCAT(DISTINCT e.name) as etf_names,
                    SUM(h.amount) as total_amount,
                    AVG(h.weight) as avg_weight
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                JOIN data_etfs e ON h.etf_ticker = e.ticker
                WHERE h.date = ?
                GROUP BY s.ticker, s.name
                HAVING etf_count > 1
                ORDER BY etf_count DESC, total_amount DESC
                LIMIT 100
            """
            cursor.execute(query, (latest_date,))

            stocks = []
            for row in cursor.fetchall():
                stocks.append(
                    {
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "etf_count": row["etf_count"],
                        "etf_names": row["etf_names"].split(",")
                        if row["etf_names"]
                        else [],
                        "total_amount": row["total_amount"],
                        "avg_weight": round(row["avg_weight"], 2),
                    }
                )

            return {"date": latest_date, "stocks": stocks}

    def get_amount_ranking_statistics(self) -> Dict:
        """전체 ETF에서 종목별 총 평가금액 통계를 반환합니다."""
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()

            # 최신 날짜 조회
            cursor.execute("SELECT MAX(date) FROM data_etf_holdings")
            latest_date = cursor.fetchone()[0]

            if not latest_date:
                return {"date": None, "stocks": []}

            # 평가금액 순위 조회
            query = """
                SELECT 
                    s.ticker,
                    s.name,
                    SUM(h.amount) as total_amount,
                    COUNT(DISTINCT h.etf_ticker) as etf_count,
                    AVG(h.weight) as avg_weight,
                    MAX(h.weight) as max_weight
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                WHERE h.date = ?
                GROUP BY s.ticker, s.name
                HAVING total_amount > 0
                ORDER BY total_amount DESC
                LIMIT 100
            """
            cursor.execute(query, (latest_date,))

            stocks = []
            for row in cursor.fetchall():
                stocks.append(
                    {
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "total_amount": row["total_amount"],
                        "etf_count": row["etf_count"],
                        "avg_weight": round(row["avg_weight"], 2),
                        "max_weight": round(row["max_weight"], 2),
                    }
                )

            return {"date": latest_date, "stocks": stocks}

    def get_theme_duplicate_stock_statistics(self, theme: str) -> Dict:
        """특정 테마 ETF들에서 중복 종목 통계를 반환합니다."""
        conn = self.db_manager.get_connection()
        with conn:
            cursor = conn.cursor()

            # 최신 날짜 조회
            cursor.execute("SELECT MAX(date) FROM data_etf_holdings")
            latest_date = cursor.fetchone()[0]

            if not latest_date:
                return {"date": None, "theme": theme, "stocks": []}

            # 테마에 해당하는 ETF 목록 조회
            cursor.execute(
                "SELECT ticker, name FROM data_etfs WHERE name LIKE ?", (f"%{theme}%",)
            )
            theme_etfs = cursor.fetchall()

            if not theme_etfs:
                return {"date": latest_date, "theme": theme, "stocks": []}

            etf_tickers = [etf["ticker"] for etf in theme_etfs]
            placeholders = ",".join(["?" for _ in etf_tickers])

            # 중복 종목 통계 조회
            query = f"""
                SELECT 
                    s.ticker,
                    s.name,
                    COUNT(DISTINCT h.etf_ticker) as etf_count,
                    GROUP_CONCAT(DISTINCT e.name) as etf_names,
                    SUM(h.amount) as total_amount,
                    AVG(h.weight) as avg_weight
                FROM data_etf_holdings h
                JOIN data_stocks s ON h.stock_ticker = s.ticker
                JOIN data_etfs e ON h.etf_ticker = e.ticker
                WHERE h.date = ? AND h.etf_ticker IN ({placeholders})
                GROUP BY s.ticker, s.name
                HAVING etf_count > 1
                ORDER BY etf_count DESC, total_amount DESC
                LIMIT 100
            """
            cursor.execute(query, [latest_date] + etf_tickers)

            stocks = []
            for row in cursor.fetchall():
                stocks.append(
                    {
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "etf_count": row["etf_count"],
                        "etf_names": row["etf_names"].split(",")
                        if row["etf_names"]
                        else [],
                        "total_amount": row["total_amount"],
                        "avg_weight": round(row["avg_weight"], 2),
                    }
                )

            return {"date": latest_date, "theme": theme, "stocks": stocks}
