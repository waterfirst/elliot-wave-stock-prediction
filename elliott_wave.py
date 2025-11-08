"""
Elliott Wave 분석 모듈
주가 데이터에서 파동 패턴을 식별하고 분석합니다.
"""

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from typing import List, Tuple, Dict


class ElliottWaveAnalyzer:
    """Elliott Wave 이론을 적용한 주가 분석 클래스"""

    # 피보나치 비율
    FIBONACCI_RATIOS = {
        'retracement': [0.236, 0.382, 0.5, 0.618, 0.786],
        'extension': [1.0, 1.272, 1.618, 2.0, 2.618]
    }

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: 주가 데이터 DataFrame (Open, High, Low, Close 컬럼 필요)
        """
        self.df = df.copy()
        self.peaks = []
        self.troughs = []
        self.waves = []

    def find_peaks_and_troughs(self, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        주가 데이터에서 고점(peaks)과 저점(troughs)을 찾습니다.

        Args:
            order: 극값을 찾을 때 비교할 주변 데이터 포인트 수

        Returns:
            (peaks_indices, troughs_indices) 튜플
        """
        # 고점 찾기
        peaks_idx = argrelextrema(self.df['High'].values, np.greater, order=order)[0]
        # 저점 찾기
        troughs_idx = argrelextrema(self.df['Low'].values, np.less, order=order)[0]

        self.peaks = peaks_idx
        self.troughs = troughs_idx

        return peaks_idx, troughs_idx

    def identify_swing_points(self) -> List[Dict]:
        """
        스윙 포인트를 시간 순서대로 정렬하여 반환합니다.

        Returns:
            스윙 포인트 정보 리스트
        """
        swing_points = []

        # 고점 추가
        for idx in self.peaks:
            swing_points.append({
                'index': idx,
                'date': self.df.iloc[idx]['Date'] if 'Date' in self.df.columns else idx,
                'price': self.df.iloc[idx]['High'],
                'type': 'peak'
            })

        # 저점 추가
        for idx in self.troughs:
            swing_points.append({
                'index': idx,
                'date': self.df.iloc[idx]['Date'] if 'Date' in self.df.columns else idx,
                'price': self.df.iloc[idx]['Low'],
                'type': 'trough'
            })

        # 시간 순서대로 정렬
        swing_points.sort(key=lambda x: x['index'])

        return swing_points

    def calculate_fibonacci_levels(self, start_price: float, end_price: float,
                                   level_type: str = 'retracement') -> Dict[str, float]:
        """
        피보나치 되돌림 또는 확장 레벨을 계산합니다.

        Args:
            start_price: 시작 가격
            end_price: 종료 가격
            level_type: 'retracement' 또는 'extension'

        Returns:
            피보나치 레벨 딕셔너리
        """
        diff = end_price - start_price
        levels = {}

        ratios = self.FIBONACCI_RATIOS[level_type]

        if level_type == 'retracement':
            for ratio in ratios:
                levels[f'{ratio:.3f}'] = end_price - (diff * ratio)
        else:  # extension
            for ratio in ratios:
                levels[f'{ratio:.3f}'] = start_price + (diff * ratio)

        return levels

    def detect_impulse_wave(self, swing_points: List[Dict], start_idx: int = 0) -> Dict:
        """
        임펄스 파동(5파동 구조)을 감지합니다.

        Args:
            swing_points: 스윙 포인트 리스트
            start_idx: 분석 시작 인덱스

        Returns:
            파동 정보 딕셔너리
        """
        if len(swing_points) - start_idx < 5:
            return None

        # 최근 5개의 주요 스윙 포인트 추출
        recent_swings = swing_points[start_idx:start_idx + 9]  # 5파동을 확인하려면 최소 9개 필요

        if len(recent_swings) < 5:
            return None

        # 상승 임펄스인지 하락 임펄스인지 판단
        is_uptrend = recent_swings[0]['type'] == 'trough'

        wave_structure = {
            'type': 'impulse',
            'direction': 'up' if is_uptrend else 'down',
            'waves': [],
            'start_date': recent_swings[0]['date'],
            'end_date': recent_swings[-1]['date'] if len(recent_swings) > 0 else None,
        }

        return wave_structure

    def analyze_current_wave(self) -> Dict:
        """
        현재 주가가 어떤 파동 단계에 있는지 분석합니다.

        Returns:
            현재 파동 분석 결과
        """
        # 고점과 저점 찾기
        self.find_peaks_and_troughs(order=5)

        # 스윙 포인트 식별
        swing_points = self.identify_swing_points()

        if len(swing_points) < 5:
            return {
                'status': 'insufficient_data',
                'message': '파동 분석을 위한 데이터가 부족합니다.',
                'swing_count': len(swing_points)
            }

        # 최근 스윙 포인트로 추세 판단
        recent_swings = swing_points[-5:]

        # 가격 움직임 방향 판단
        price_changes = []
        for i in range(1, len(recent_swings)):
            price_changes.append(recent_swings[i]['price'] - recent_swings[i-1]['price'])

        avg_change = np.mean(price_changes)
        trend = 'bullish' if avg_change > 0 else 'bearish'

        # 현재 가격
        current_price = self.df['Close'].iloc[-1]

        # 마지막 스윙 포인트
        last_swing = swing_points[-1]

        # 피보나치 레벨 계산 (최근 2개 스윙 포인트 기준)
        if len(swing_points) >= 2:
            fib_levels = self.calculate_fibonacci_levels(
                swing_points[-2]['price'],
                swing_points[-1]['price'],
                'retracement'
            )
        else:
            fib_levels = {}

        return {
            'status': 'success',
            'trend': trend,
            'current_price': current_price,
            'last_swing': last_swing,
            'swing_points': swing_points[-10:],  # 최근 10개만
            'fibonacci_levels': fib_levels,
            'total_swings': len(swing_points)
        }

    def predict_next_target(self) -> Dict:
        """
        다음 목표 가격을 예측합니다.

        Returns:
            예측 결과 딕셔너리
        """
        analysis = self.analyze_current_wave()

        if analysis['status'] != 'success':
            return analysis

        current_price = analysis['current_price']
        trend = analysis['trend']
        swing_points = analysis['swing_points']

        if len(swing_points) < 2:
            return {
                'status': 'insufficient_data',
                'message': '목표 가격 예측을 위한 데이터가 부족합니다.'
            }

        # 최근 2개 스윙 포인트로 파동 크기 계산
        last_swing = swing_points[-1]
        prev_swing = swing_points[-2]

        wave_size = abs(last_swing['price'] - prev_swing['price'])

        # 피보나치 확장을 사용한 목표 가격 계산
        if trend == 'bullish':
            # 상승 추세: 확장 레벨 적용
            targets = {
                'conservative': current_price + (wave_size * 0.618),
                'moderate': current_price + (wave_size * 1.0),
                'aggressive': current_price + (wave_size * 1.618)
            }
        else:
            # 하락 추세: 확장 레벨 적용
            targets = {
                'conservative': current_price - (wave_size * 0.618),
                'moderate': current_price - (wave_size * 1.0),
                'aggressive': current_price - (wave_size * 1.618)
            }

        return {
            'status': 'success',
            'current_price': current_price,
            'trend': trend,
            'targets': targets,
            'wave_size': wave_size,
            'confidence': self._calculate_confidence(swing_points)
        }

    def _calculate_confidence(self, swing_points: List[Dict]) -> float:
        """
        예측 신뢰도를 계산합니다 (0.0 ~ 1.0).

        Args:
            swing_points: 스윙 포인트 리스트

        Returns:
            신뢰도 점수
        """
        # 스윙 포인트가 많을수록 신뢰도 증가
        swing_confidence = min(len(swing_points) / 20, 1.0)

        # 가격 변동성 기반 신뢰도
        recent_prices = [sp['price'] for sp in swing_points[-5:]]
        if len(recent_prices) > 1:
            volatility = np.std(recent_prices) / np.mean(recent_prices)
            volatility_confidence = max(0, 1 - volatility)
        else:
            volatility_confidence = 0.5

        # 가중 평균
        confidence = (swing_confidence * 0.6) + (volatility_confidence * 0.4)

        return round(confidence, 2)
