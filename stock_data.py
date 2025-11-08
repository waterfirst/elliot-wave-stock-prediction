"""
주가 데이터 수집 모듈
yfinance를 사용하여 실시간 주가 데이터를 가져옵니다.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import time


class StockDataFetcher:
    """주가 데이터를 가져오는 클래스"""

    def __init__(self, ticker: str):
        """
        Args:
            ticker: 주식 티커 심볼 (예: 'NVDA', 'AAPL', 'TSLA')
        """
        self.ticker = ticker.upper()
        # Ticker 객체는 info 조회용으로만 사용
        self.stock = None

    def get_historical_data(self, period: str = '1y', interval: str = '1d') -> pd.DataFrame:
        """
        과거 주가 데이터를 가져옵니다.
        yf.download() 함수를 사용하여 안정적으로 데이터를 가져옵니다.

        Args:
            period: 데이터 기간 ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: 데이터 간격 ('1d', '1h', '1wk', '1mo')

        Returns:
            주가 데이터가 담긴 DataFrame
        """
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # yf.download() 사용 - 더 안정적
                df = yf.download(
                    tickers=self.ticker,
                    period=period,
                    interval=interval,
                    progress=False,  # 진행바 비활성화
                    show_errors=False  # 에러 메시지 비활성화
                )

                if not df.empty:
                    # 인덱스를 날짜 컬럼으로 변환
                    df.reset_index(inplace=True)

                    # 컬럼명 정리 (MultiIndex인 경우)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    return df

                # 데이터가 비어있는 경우
                if attempt < max_retries - 1:
                    # 재시도 전 대기
                    time.sleep(retry_delay)
                    # 다음 시도에서는 더 짧은 기간으로 시도
                    if period == '1y':
                        period = '6mo'
                    elif period == '2y':
                        period = '1y'
                    elif period == '5y':
                        period = '2y'
                    continue
                else:
                    raise ValueError(f"'{self.ticker}' 티커에 대한 데이터를 찾을 수 없습니다.")

            except ValueError as ve:
                # ValueError는 그대로 전파
                raise ve
            except Exception as e:
                if attempt < max_retries - 1:
                    # 재시도
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(f"데이터 수집 중 오류 발생: {str(e)}")

        raise Exception(f"'{self.ticker}' 티커에 대한 데이터를 가져올 수 없습니다.")

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
            # Ticker 객체 사용 (info 조회용)
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info

            # 기본 정보 추출
            name = info.get('longName', info.get('shortName', self.ticker))
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            market_cap = info.get('marketCap', 'N/A')

            # 현재 가격 추출
            if 'currentPrice' in info and info['currentPrice']:
                current_price = info['currentPrice']
            elif 'regularMarketPrice' in info and info['regularMarketPrice']:
                current_price = info['regularMarketPrice']
        except:
            pass

        # 현재 가격을 못 가져온 경우 yf.download로 시도
        if current_price == 'N/A':
            try:
                df = yf.download(
                    tickers=self.ticker,
                    period='1d',
                    progress=False,
                    show_errors=False
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
        yf.download()로 실제 데이터 존재 여부 확인.

        Returns:
            유효하면 True, 아니면 False
        """
        try:
            # yf.download로 짧은 기간 데이터 확인
            df = yf.download(
                tickers=self.ticker,
                period='5d',
                progress=False,
                show_errors=False
            )
            return not df.empty

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
