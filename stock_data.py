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
            ticker: 주식 티커 심볼 (예: "Nvidia": "NVDA", "Apple": "AAPL", "Tesla": "TSLA")
        """
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)

    def get_historical_data(self, period: str = '1y', interval: str = '1d', retry: int = 3) -> pd.DataFrame:
        """
        과거 주가 데이터를 가져옵니다.

        Args:
            period: 데이터 기간 ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval: 데이터 간격 ('1d', '1h', '1wk', '1mo')
            retry: 재시도 횟수 (기본값: 3)

        Returns:
            주가 데이터가 담긴 DataFrame
        """
        last_error = None
        for attempt in range(retry):
            try:
                # yf.download를 사용하여 더 안정적으로 데이터 가져오기
                df = yf.download(
                    self.ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    timeout=10
                )

                # MultiIndex 처리 (yf.download는 여러 티커를 다운로드할 때 MultiIndex 반환)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)

                if df.empty:
                    # Ticker 객체로 재시도
                    df = self.stock.history(period=period, interval=interval, timeout=10)

                if df.empty:
                    raise ValueError(f"'{self.ticker}' 티커에 대한 데이터를 찾을 수 없습니다.")

                # 인덱스를 날짜 컬럼으로 변환
                if isinstance(df.index, pd.DatetimeIndex):
                    df.reset_index(inplace=True)
                elif 'Date' not in df.columns:
                    df.reset_index(inplace=True)

                return df
            except Exception as e:
                last_error = e
                if attempt < retry - 1:
                    time.sleep(1)  # 재시도 전 대기
                else:
                    raise Exception(f"데이터 수집 중 오류 발생 (재시도 {retry}회 실패): {str(e)}")
        
        raise Exception(f"데이터 수집 중 오류 발생: {str(last_error)}")

    def get_stock_info(self) -> dict:
        """
        주식 기본 정보를 가져옵니다.
        Streamlit Cloud 환경에서도 안정적으로 작동하도록 개선되었습니다.

        Returns:
            주식 정보 딕셔너리
        """
        try:
            # info 속성 시도
            info = self.stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            # current_price가 없으면 최근 데이터에서 가져오기
            if not current_price:
                try:
                    df = yf.download(self.ticker, period='1d', progress=False, timeout=10)
                    # MultiIndex 처리
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)
                    if not df.empty and 'Close' in df.columns:
                        current_price = float(df['Close'].iloc[-1])
                except:
                    pass
            
            return {
                'name': info.get('longName') or info.get('shortName', self.ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'current_price': current_price if current_price else 'N/A',
            }
        except Exception as e:
            # info 실패 시 최소한의 정보라도 가져오기
            try:
                df = yf.download(self.ticker, period='1d', progress=False, timeout=10)
                # MultiIndex 처리
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                current_price = None
                if not df.empty and 'Close' in df.columns:
                    current_price = float(df['Close'].iloc[-1])
            except:
                current_price = None
            
            return {
                'name': self.ticker,
                'sector': 'N/A',
                'industry': 'N/A',
                'market_cap': 'N/A',
                'current_price': current_price if current_price else 'N/A',
            }

    def validate_ticker(self) -> bool:
        """
        티커 심볼이 유효한지 검증합니다.
        Streamlit Cloud 환경에서도 안정적으로 작동하도록 history() 메서드를 우선 사용합니다.

        Returns:
            유효하면 True, 아니면 False
        """
        try:
            # 1. history() 메서드 시도 (가장 안정적)
            try:
                df = self.stock.history(period='5d', timeout=10)
                if not df.empty and len(df) > 0:
                    return True
            except:
                pass

            # 2. yf.download() 시도 (백업)
            try:
                df = yf.download(
                    self.ticker,
                    period='5d',
                    interval='1d',
                    progress=False,
                    timeout=10
                )
                
                # MultiIndex 처리
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                    
                if not df.empty and len(df) > 0:
                    # 가격 컬럼 확인
                    if 'Close' in df.columns or 'Open' in df.columns:
                        return True
            except:
                pass

            # 3. info 속성 확인 (마지막 수단)
            # 데이터 다운로드가 실패해도 info가 있으면 유효한 티커일 수 있음
            try:
                info = self.stock.info
                if info and ('symbol' in info or 'regularMarketPrice' in info):
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            # 에러 발생 시 False 반환
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
    ]
