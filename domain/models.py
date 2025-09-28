from dataclasses import dataclass


@dataclass
class Stock:
    """주식 정보를 나타내는 데이터 클래스"""

    ticker: str
    name: str

    def to_dict(self):
        return {"ticker": self.ticker, "name": self.name}


@dataclass
class ETF:
    """ETF 정보를 나타내는 데이터 클래스"""

    ticker: str
    name: str

    def to_dict(self):
        return {"ticker": self.ticker, "name": self.name}


@dataclass
class ETFHolding:
    """ETF의 특정 날짜 보유 종목 정보를 나타내는 데이터 클래스"""

    etf_ticker: str
    stock_ticker: str
    date: str
    weight: float
    stock_name: str = ""  # Join을 통해 채워질 필드

    def to_dict(self):
        return {
            "etf_ticker": self.etf_ticker,
            "stock_ticker": self.stock_ticker,
            "stock_name": self.stock_name,
            "date": self.date,
            "weight": self.weight,
        }
