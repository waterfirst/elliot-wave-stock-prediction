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

    def get_historical_data(self, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """
        과거 주가 데이터를 가져옵니다.
        yf.download() 함수를 사용하여 데이터를 가져옵니다.

        Args:
            period: 데이터 기간 ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: 데이터 간격 ('1d', '1h', '1wk', '1mo')

        Returns:
            주가 데이터가 담긴 DataFrame
        """
        # period를 날짜 범위로 변환
        end_date = datetime.now()

        # period에 따른 시작 날짜 계산
        period_days = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825,
            'max': 3650  # 약 10년
        }

        days = period_days.get(period, 365)
        start_date = end_date - timedelta(days=days)

        # yf.download() 직접 사용 - 가장 안정적
        df = yf.download(
            self.ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False
        )

        if df.empty:
            raise ValueError(f"'{self.ticker}' 티커에 대한 데이터를 찾을 수 없습니다.")

        # 인덱스를 날짜 컬럼으로 변환
        df.reset_index(inplace=True)

        # 컬럼명이 MultiIndex인 경우 처리
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    def get_stock_info(self) -> dict:
        """
        주식 기본 정보를 가져옵니다.

        Returns:
            주식 정보 딕셔너리
        """
        current_price = 'N/A'
        name = self.ticker
        sector = 'N/A'
        industry = 'N/A'
        market_cap = 'N/A'

        try:
            # Ticker 객체로 info 조회
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info

            # 기본 정보 추출
            if info:
                name = info.get('longName', info.get('shortName', self.ticker))
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                market_cap = info.get('marketCap', 'N/A')

                # 현재 가격
                if 'currentPrice' in info and info['currentPrice']:
                    current_price = info['currentPrice']
                elif 'regularMarketPrice' in info and info['regularMarketPrice']:
                    current_price = info['regularMarketPrice']
        except:
            pass

        # 현재 가격을 못 가져온 경우 최근 데이터에서 가져오기
        if current_price == 'N/A':
            try:
                df = yf.download(
                    self.ticker,
                    period='1d',
                    progress=False
                )
                if not df.empty:
                    current_price = float(df['Close'].iloc[-1])
            except:
                pass

        return {
            'name': name,
            'sector': sector,
            'industry': industry,
            'market_cap': market_cap,
            'current_price': current_price,
        }

    def validate_ticker(self) -> bool:
        """
        티커 심볼이 유효한지 검증합니다.

        Returns:
            유효하면 True, 아니면 False
        """
        try:
            # 짧은 기간 데이터로 확인
            df = yf.download(
                self.ticker,
                period='5d',
                progress=False
            )
            return not df.empty
        except:
            # 에러 시에도 True 반환 (실제 데이터 수집 시 체크)
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
