"""
주가 데이터 수집 모듈
yfinance를 사용하여 실시간 주가 데이터를 가져옵니다.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class StockDataFetcher:
    """주가 데이터를 가져오는 클래스"""

    def __init__(self, ticker: str):
        """
        Args:
            ticker: 주식 티커 심볼 (예: 'NVDA', 'AAPL', 'TSLA')
        """
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)

    def get_historical_data(self, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """
        과거 주가 데이터를 가져옵니다.

        Args:
            period: 데이터 기간 ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: 데이터 간격 ('1d', '1h', '1wk', '1mo')

        Returns:
            주가 데이터가 담긴 DataFrame
        """
        try:
            df = self.stock.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"'{self.ticker}' 티커에 대한 데이터를 찾을 수 없습니다.")

            # 인덱스를 날짜 컬럼으로 변환
            df.reset_index(inplace=True)

            return df
        except Exception as e:
            raise Exception(f"데이터 수집 중 오류 발생: {str(e)}")

    def get_stock_info(self) -> dict:
        """
        주식 기본 정보를 가져옵니다.

        Returns:
            주식 정보 딕셔너리
        """
        try:
            info = self.stock.info
            return {
                'name': info.get('longName', self.ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': info.get('currentPrice', 'N/A'),
            }
        except Exception as e:
            return {
                'name': self.ticker,
                'sector': 'N/A',
                'industry': 'N/A',
                'market_cap': 'N/A',
                'current_price': 'N/A',
            }

    def validate_ticker(self) -> bool:
        """
        티커 심볼이 유효한지 검증합니다.

        Returns:
            유효하면 True, 아니면 False
        """
        try:
            info = self.stock.info
            return 'regularMarketPrice' in info or 'currentPrice' in info
        except:
            return False


def get_available_tickers() -> list:
    """
    자주 사용되는 주요 기술주 티커 목록을 반환합니다.

    Returns:
        티커 심볼 리스트
    """
    return [
        'NVDA',   # Nvidia
        'AAPL',   # Apple
        'MSFT',   # Microsoft
        'GOOGL',  # Google
        'AMZN',   # Amazon
        'TSLA',   # Tesla
        'META',   # Meta
        'AMD',    # AMD
        'INTC',   # Intel
        'NFLX',   # Netflix
        'CSCO',   # Cisco
        'ADBE',   # Adobe
        'CRM',    # Salesforce
        'ORCL',   # Oracle
        'IBM',    # IBM
    ]
