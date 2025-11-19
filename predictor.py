"""
주가 예측 모듈
Elliott Wave 분석과 기술적 지표를 결합하여 미래 주가를 예측합니다.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from elliott_wave import ElliottWaveAnalyzer


class StockPredictor:
    """주가 예측 클래스"""

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: 주가 데이터 DataFrame
        """
        self.df = df.copy()
        self.elliott_analyzer = ElliottWaveAnalyzer(df)

    def calculate_momentum(self, window: int = 14) -> float:
        """
        가격 모멘텀을 계산합니다.

        Args:
            window: 계산 윈도우

        Returns:
            모멘텀 값
        """
        if len(self.df) < window:
            window = len(self.df)

        recent_prices = self.df['Close'].tail(window).values
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]

        return momentum

    def calculate_trend_strength(self) -> float:
        """
        추세 강도를 계산합니다 (0.0 ~ 1.0).

        Returns:
            추세 강도
        """
        # 이동평균선 계산
        if len(self.df) < 50:
            return 0.5

        self.df['MA20'] = self.df['Close'].rolling(window=20).mean()
        self.df['MA50'] = self.df['Close'].rolling(window=50).mean()

        current_price = self.df['Close'].iloc[-1]
        ma20 = self.df['MA20'].iloc[-1]
        ma50 = self.df['MA50'].iloc[-1]

        # 가격이 이동평균 위에 있는지 확인
        above_ma20 = 1 if current_price > ma20 else 0
        above_ma50 = 1 if current_price > ma50 else 0
        ma_alignment = 1 if ma20 > ma50 else 0

        strength = (above_ma20 + above_ma50 + ma_alignment) / 3

        return strength

    def calculate_volatility(self, window: int = 20) -> float:
        """
        가격 변동성을 계산합니다.

        Args:
            window: 계산 윈도우

        Returns:
            변동성 (표준편차 / 평균)
        """
        if len(self.df) < window:
            window = len(self.df)

        recent_prices = self.df['Close'].tail(window).values
        volatility = np.std(recent_prices) / np.mean(recent_prices)

        return volatility

    def predict_price(self, days: int = 1) -> Dict:
        """
        특정 일수 후의 주가를 예측합니다.

        Args:
            days: 예측할 일수 (1, 5, 10, 30)

        Returns:
            예측 결과 딕셔너리
        """
        # Elliott Wave 분석
        wave_prediction = self.elliott_analyzer.predict_next_target()

        if wave_prediction['status'] != 'success':
            return wave_prediction

        current_price = wave_prediction['current_price']
        trend = wave_prediction['trend']
        targets = wave_prediction['targets']

        # 기술적 지표 계산
        momentum = self.calculate_momentum()
        trend_strength = self.calculate_trend_strength()
        volatility = self.calculate_volatility()

        # 일수별 가중치 조정
        time_weight = self._calculate_time_weight(days)

        # 예측 가격 계산
        if trend == 'bullish':
            # 상승 추세
            base_target = targets['moderate']
            adjustment = (base_target - current_price) * time_weight * trend_strength
            predicted_price = current_price + adjustment

            # 신뢰 구간 계산
            uncertainty = volatility * np.sqrt(days) * current_price
            lower_bound = max(current_price * 0.7, predicted_price - uncertainty)
            upper_bound = predicted_price + uncertainty

        else:
            # 하락 추세
            base_target = targets['moderate']
            adjustment = (current_price - base_target) * time_weight * trend_strength
            predicted_price = current_price - adjustment

            # 신뢰 구간 계산
            uncertainty = volatility * np.sqrt(days) * current_price
            lower_bound = predicted_price - uncertainty
            upper_bound = min(current_price * 1.3, predicted_price + uncertainty)

        # 예측 날짜 계산
        last_date = self.df['Date'].iloc[-1] if 'Date' in self.df.columns else datetime.now()

        # last_date가 Timestamp인 경우 datetime으로 변환
        if isinstance(last_date, pd.Timestamp):
            last_date = last_date.to_pydatetime()

        # 주말 제외한 영업일 계산
        prediction_date = self._add_business_days(last_date, days)

        # 가격 변화율 계산
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price) * 100

        return {
            'status': 'success',
            'days': days,
            'current_price': round(current_price, 2),
            'predicted_price': round(predicted_price, 2),
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'price_change': round(price_change, 2),
            'price_change_pct': round(price_change_pct, 2),
            'prediction_date': prediction_date.strftime('%Y-%m-%d'),
            'trend': trend,
            'confidence': wave_prediction['confidence'],
            'metrics': {
                'momentum': round(momentum, 4),
                'trend_strength': round(trend_strength, 2),
                'volatility': round(volatility, 4)
            }
        }

    def predict_multiple_periods(self, periods: List[int] = [1, 5, 10, 30]) -> Dict:
        """
        여러 기간에 대한 예측을 수행합니다.

        Args:
            periods: 예측할 기간 리스트

        Returns:
            기간별 예측 결과 딕셔너리
        """
        predictions = {}

        for days in periods:
            predictions[f'{days}day'] = self.predict_price(days)

        return predictions

    def _calculate_time_weight(self, days: int) -> float:
        """
        예측 일수에 따른 가중치를 계산합니다.

        Args:
            days: 예측 일수

        Returns:
            가중치 (0.0 ~ 1.0)
        """
        # 로그 스케일로 시간 가중치 계산
        # 1일: ~0.3, 5일: ~0.5, 10일: ~0.7, 30일: ~1.0
        weight = np.log1p(days) / np.log1p(30)

        return min(weight, 1.0)

    def _add_business_days(self, start_date: datetime, days: int) -> datetime:
        """
        시작일로부터 영업일을 더합니다.

        Args:
            start_date: 시작 날짜
            days: 더할 영업일 수

        Returns:
            계산된 날짜
        """
        current_date = start_date
        days_added = 0

        while days_added < days:
            current_date += timedelta(days=1)
            # 주말(토요일=5, 일요일=6) 제외
            if current_date.weekday() < 5:
                days_added += 1

        return current_date

    def get_prediction_summary(self) -> Dict:
        """
        전체 예측 요약을 반환합니다.

        Returns:
            예측 요약 딕셔너리
        """
        # 다중 기간 예측
        predictions = self.predict_multiple_periods([1, 5, 10, 30])

        # Elliott Wave 분석
        wave_analysis = self.elliott_analyzer.analyze_current_wave()

        current_price = self.df['Close'].iloc[-1]

        summary = {
            'current_price': round(current_price, 2),
            'predictions': predictions,
            'wave_analysis': wave_analysis,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return summary

    def backtest_predictions(self, days_back: int = 60, test_period: int = 5) -> Dict:
        """
        과거 데이터를 바탕으로 예측 정확도를 테스트합니다.

        Args:
            days_back: 며칠 전부터 테스트할지 (테스트 범위)
            test_period: 예측할 미래 기간 (예: 5일 후 예측 테스트)

        Returns:
            백테스팅 결과 딕셔너리
        """
        results = []
        
        # 테스트 가능한 데이터 범위 확인
        if len(self.df) < days_back + test_period + 50: # 최소 데이터 요구량
            return {'status': 'insufficient_data'}

        # 과거 시점으로 돌아가서 예측 수행
        # 최근 데이터는 정답지(Actual)로 사용해야 하므로, days_back 이전부터 시작
        start_idx = len(self.df) - days_back - test_period
        end_idx = len(self.df) - test_period

        for i in range(start_idx, end_idx, 2): # 2일 간격으로 테스트 (성능 최적화)
            # 과거 시점의 데이터로 슬라이싱
            past_df = self.df.iloc[:i+1].copy()
            
            # 해당 시점의 실제 미래 가격 (정답)
            actual_future_price = self.df['Close'].iloc[i + test_period]
            actual_current_price = self.df['Close'].iloc[i]
            
            # 예측기 생성 및 예측
            past_predictor = StockPredictor(past_df)
            prediction = past_predictor.predict_price(days=test_period)
            
            if prediction['status'] == 'success':
                predicted_price = prediction['predicted_price']
                
                # 방향성 정확도 확인
                predicted_direction = 1 if predicted_price > actual_current_price else -1
                actual_direction = 1 if actual_future_price > actual_current_price else -1
                is_direction_correct = predicted_direction == actual_direction
                
                # 오차율 계산
                error_pct = abs(predicted_price - actual_future_price) / actual_future_price * 100
                
                results.append({
                    'date': past_df['Date'].iloc[-1],
                    'actual_price': actual_future_price,
                    'predicted_price': predicted_price,
                    'direction_correct': is_direction_correct,
                    'error_pct': error_pct,
                    'confidence': prediction['confidence']
                })

        if not results:
            return {'status': 'no_results'}

        # 종합 메트릭 계산
        df_results = pd.DataFrame(results)
        
        accuracy_metrics = {
            'directional_accuracy': df_results['direction_correct'].mean() * 100,
            'mape': df_results['error_pct'].mean(), # Mean Absolute Percentage Error
            'rmse': np.sqrt(np.mean((df_results['predicted_price'] - df_results['actual_price'])**2)),
            'avg_confidence': df_results['confidence'].mean(),
            'total_tests': len(results)
        }

        return {
            'status': 'success',
            'metrics': accuracy_metrics,
            'detailed_results': results
        }
