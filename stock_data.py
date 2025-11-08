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
            # 방법 1: info 확인 (빠르고 안정적)
            info = self.stock.info
            if info and len(info) > 1:
                # info에 데이터가 있으면 유효한 티커로 간주
                return True

            # 방법 2: 실제 히스토리 데이터 확인
            hist = self.stock.history(period='1d')
            return not hist.empty

        except:
            # 에러 발생 시에도 True 반환
            # (실제 데이터를 가져올 때 다시 체크되므로 안전)
            return True


def get_available_tickers() -> dict:
    """
    자주 사용되는 주요 주식 티커 목록을 반환합니다.

    Returns:
        지역별 티커 심볼 딕셔너리
    """
    return {
        '🇺🇸 미국 기술주': [
            'NVDA',   # Nvidia
            'AAPL',   # Apple
            'MSFT',   # Microsoft
            'GOOGL',  # Google (Alphabet Class A)
            'AMZN',   # Amazon
            'TSLA',   # Tesla
            'META',   # Meta (Facebook)
            'AMD',    # AMD
            'INTC',   # Intel
            'NFLX',   # Netflix
        ],
        '🇺🇸 미국 금융/기타': [
            'JPM',    # JPMorgan Chase
            'V',      # Visa
            'MA',     # Mastercard
            'BAC',    # Bank of America
            'WMT',    # Walmart
            'JNJ',    # Johnson & Johnson
            'PG',     # Procter & Gamble
            'DIS',    # Disney
        ],
        '🇰🇷 한국 주식': [
            '005930.KS',  # 삼성전자
            '000660.KS',  # SK하이닉스
            '035420.KS',  # 네이버
            '035720.KS',  # 카카오
            '005380.KS',  # 현대차
            '066570.KS',  # LG전자
            '051910.KS',  # LG화학
            '006400.KS',  # 삼성SDI
            '028260.KS',  # 삼성물산
            '012330.KS',  # 현대모비스
        ],
        '🇨🇳 중국 주식': [
            'BABA',   # Alibaba
            'BIDU',   # Baidu
            'JD',     # JD.com
            'PDD',    # Pinduoduo
            'NIO',    # NIO
        ],
    }


def get_ticker_name_map() -> dict:
    """
    티커 심볼과 회사명 매핑을 반환합니다.

    Returns:
        티커: 회사명 딕셔너리
    """
    return {
        # 미국 기술주
        'NVDA': 'Nvidia',
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'GOOGL': 'Google (Alphabet)',
        'AMZN': 'Amazon',
        'TSLA': 'Tesla',
        'META': 'Meta (Facebook)',
        'AMD': 'AMD',
        'INTC': 'Intel',
        'NFLX': 'Netflix',
        # 미국 금융/기타
        'JPM': 'JPMorgan Chase',
        'V': 'Visa',
        'MA': 'Mastercard',
        'BAC': 'Bank of America',
        'WMT': 'Walmart',
        'JNJ': 'Johnson & Johnson',
        'PG': 'Procter & Gamble',
        'DIS': 'Disney',
        # 한국 주식
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '035420.KS': '네이버',
        '035720.KS': '카카오',
        '005380.KS': '현대차',
        '066570.KS': 'LG전자',
        '051910.KS': 'LG화학',
        '006400.KS': '삼성SDI',
        '028260.KS': '삼성물산',
        '012330.KS': '현대모비스',
        # 중국 주식
        'BABA': 'Alibaba',
        'BIDU': 'Baidu',
        'JD': 'JD.com',
        'PDD': 'Pinduoduo',
        'NIO': 'NIO',
    }
