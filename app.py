"""
Elliott Wave 주가 예측 웹 애플리케이션
Streamlit을 사용하여 주식을 선택하고 파동 분석 기반 예측 결과를 시각화합니다.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from stock_data import StockDataFetcher, get_available_tickers, get_ticker_name_map
from elliott_wave import ElliottWaveAnalyzer
from predictor import StockPredictor


# 페이지 설정
st.set_page_config(
    page_title="Elliott Wave 주가 예측",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


def plot_stock_chart(df: pd.DataFrame, swing_points: list, predictions: dict, ticker: str):
    """
    주가 차트와 파동 분석 결과를 시각화합니다.

    Args:
        df: 주가 데이터
        swing_points: 스윙 포인트 리스트
        predictions: 예측 결과
        ticker: 티커 심볼
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{ticker} 주가 차트 및 Elliott Wave 분석', '거래량'),
        row_heights=[0.7, 0.3]
    )

    # 캔들스틱 차트
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='주가',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )

    # 스윙 포인트 표시
    if swing_points:
        peak_dates = [sp['date'] for sp in swing_points if sp['type'] == 'peak']
        peak_prices = [sp['price'] for sp in swing_points if sp['type'] == 'peak']

        trough_dates = [sp['date'] for sp in swing_points if sp['type'] == 'trough']
        trough_prices = [sp['price'] for sp in swing_points if sp['type'] == 'trough']

        # 고점 표시
        fig.add_trace(
            go.Scatter(
                x=peak_dates,
                y=peak_prices,
                mode='markers',
                name='고점 (Peak)',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ),
            row=1, col=1
        )

        # 저점 표시
        fig.add_trace(
            go.Scatter(
                x=trough_dates,
                y=trough_prices,
                mode='markers',
                name='저점 (Trough)',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ),
            row=1, col=1
        )

        # 파동 연결선
        all_swings_sorted = sorted(swing_points, key=lambda x: x['index'])
        swing_dates = [sp['date'] for sp in all_swings_sorted]
        swing_prices = [sp['price'] for sp in all_swings_sorted]

        fig.add_trace(
            go.Scatter(
                x=swing_dates,
                y=swing_prices,
                mode='lines',
                name='파동 패턴',
                line=dict(color='purple', width=2, dash='dot')
            ),
            row=1, col=1
        )

    # 거래량 차트
    colors = ['red' if row['Close'] < row['Open'] else 'green' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='거래량',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # 레이아웃 설정
    fig.update_layout(
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="날짜", row=2, col=1)
    fig.update_yaxes(title_text="주가 ($)", row=1, col=1)
    fig.update_yaxes(title_text="거래량", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


def plot_predictions(predictions: dict, current_price: float):
    """
    예측 결과를 시각화합니다.

    Args:
        predictions: 예측 결과
        current_price: 현재 가격
    """
    # 예측 데이터 준비
    days = []
    predicted_prices = []
    lower_bounds = []
    upper_bounds = []

    for key in ['1day', '5day', '10day', '30day']:
        if key in predictions and predictions[key]['status'] == 'success':
            pred = predictions[key]
            days.append(pred['days'])
            predicted_prices.append(pred['predicted_price'])
            lower_bounds.append(pred['lower_bound'])
            upper_bounds.append(pred['upper_bound'])

    # 현재 가격 추가
    days.insert(0, 0)
    predicted_prices.insert(0, current_price)
    lower_bounds.insert(0, current_price)
    upper_bounds.insert(0, current_price)

    # 차트 생성
    fig = go.Figure()

    # 예측 가격
    fig.add_trace(
        go.Scatter(
            x=days,
            y=predicted_prices,
            mode='lines+markers',
            name='예측 가격',
            line=dict(color='blue', width=3),
            marker=dict(size=10)
        )
    )

    # 신뢰 구간
    fig.add_trace(
        go.Scatter(
            x=days + days[::-1],
            y=upper_bounds + lower_bounds[::-1],
            fill='toself',
            fillcolor='rgba(0, 100, 255, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='신뢰 구간',
            hoverinfo='skip'
        )
    )

    fig.update_layout(
        title='기간별 주가 예측',
        xaxis_title='일수',
        yaxis_title='예측 가격 ($)',
        height=400,
        hovermode='x'
    )

    st.plotly_chart(fig, use_container_width=True)


def display_prediction_table(predictions: dict):
    """
    예측 결과를 테이블로 표시합니다.

    Args:
        predictions: 예측 결과
    """
    data = []

    for key in ['1day', '5day', '10day', '30day']:
        if key in predictions and predictions[key]['status'] == 'success':
            pred = predictions[key]
            data.append({
                '예측 기간': f"{pred['days']}일",
                '예측일': pred['prediction_date'],
                '현재 가격': f"${pred['current_price']:.2f}",
                '예측 가격': f"${pred['predicted_price']:.2f}",
                '하한가': f"${pred['lower_bound']:.2f}",
                '상한가': f"${pred['upper_bound']:.2f}",
                '변화율': f"{pred['price_change_pct']:+.2f}%",
                '추세': '상승' if pred['trend'] == 'bullish' else '하락',
                '신뢰도': f"{pred['confidence']:.0%}"
            })

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """메인 애플리케이션"""

    # 타이틀
    st.title("📈 Elliott Wave 주가 예측 시스템")
    st.markdown("""
    이 애플리케이션은 **Elliott Wave 이론**을 활용하여 주식 가격을 예측합니다.
    원하는 주식을 선택하고 1일, 5일, 10일, 30일 후의 예상 가격을 확인하세요.
    """)

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")

        # 티커 선택
        available_tickers = get_available_tickers()
        ticker_name_map = get_ticker_name_map()

        # 사용자 정의 티커 입력 옵션
        use_custom = st.checkbox("사용자 정의 티커 입력")

        if use_custom:
            ticker = st.text_input("티커 심볼 입력", value="NVDA").upper()
        else:
            # 카테고리 선택
            category = st.selectbox(
                "카테고리 선택",
                list(available_tickers.keys()),
                index=0
            )

            # 선택된 카테고리의 티커 목록
            tickers_in_category = available_tickers[category]

            # 티커를 이름과 함께 표시
            ticker_options = [
                f"{ticker_name_map.get(t, t)} ({t})"
                for t in tickers_in_category
            ]

            # 티커 선택
            selected_option = st.selectbox(
                "주식 선택",
                ticker_options,
                index=0
            )

            # 괄호 안의 티커 심볼 추출
            ticker = selected_option.split('(')[-1].strip(')')

        # 데이터 기간 선택
        period = st.selectbox(
            "데이터 기간",
            ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
            index=3
        )

        # 분석 버튼
        analyze_button = st.button("📊 분석 시작", type="primary", use_container_width=True)

        st.markdown("---")
        st.markdown("""
        ### 📖 사용법
        1. 분석할 주식을 선택하세요
        2. 데이터 기간을 설정하세요
        3. '분석 시작' 버튼을 클릭하세요

        ### ℹ️ Elliott Wave 이론
        - **임펄스 파동**: 5개의 파동으로 구성된 추세
        - **조정 파동**: 3개의 파동으로 구성된 조정
        - **피보나치 비율**: 되돌림 및 확장 레벨
        """)

    # 메인 컨텐츠
    if analyze_button:
        with st.spinner(f'{ticker} 데이터를 가져오는 중...'):
            try:
                # 데이터 수집
                fetcher = StockDataFetcher(ticker)

                # 티커 유효성 검증
                if not fetcher.validate_ticker():
                    st.error(f"❌ '{ticker}'는 유효하지 않은 티커 심볼입니다. 다시 확인해주세요.")
                    return

                # 주식 정보
                stock_info = fetcher.get_stock_info()

                # 과거 데이터
                df = fetcher.get_historical_data(period=period)

                if df.empty:
                    st.error("데이터를 가져올 수 없습니다.")
                    return

                # 주식 정보 표시
                st.header(f"🏢 {stock_info['name']} ({ticker})")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("현재 가격", f"${stock_info['current_price']:.2f}")

                with col2:
                    st.metric("섹터", stock_info['sector'])

                with col3:
                    st.metric("산업", stock_info['industry'])

                with col4:
                    if stock_info['market_cap'] != 'N/A':
                        market_cap_b = stock_info['market_cap'] / 1e9
                        st.metric("시가총액", f"${market_cap_b:.1f}B")

                st.markdown("---")

                # Elliott Wave 분석
                with st.spinner('Elliott Wave 분석 중...'):
                    predictor = StockPredictor(df)
                    summary = predictor.get_prediction_summary()

                # 예측 결과
                st.header("🔮 예측 결과")

                if summary['predictions']['1day']['status'] == 'success':
                    # 예측 테이블
                    display_prediction_table(summary['predictions'])

                    # 예측 차트
                    plot_predictions(summary['predictions'], summary['current_price'])

                    # 상세 분석
                    st.markdown("---")
                    st.header("📊 상세 분석")

                    # Wave 분석 정보
                    wave_analysis = summary['wave_analysis']

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("파동 분석")
                        st.write(f"**추세**: {wave_analysis['trend'].upper()}")
                        st.write(f"**현재 가격**: ${wave_analysis['current_price']:.2f}")
                        st.write(f"**식별된 스윙 포인트**: {wave_analysis['total_swings']}개")

                    with col2:
                        st.subheader("기술적 지표")
                        metrics = summary['predictions']['1day']['metrics']
                        st.write(f"**모멘텀**: {metrics['momentum']:.4f}")
                        st.write(f"**추세 강도**: {metrics['trend_strength']:.2f}")
                        st.write(f"**변동성**: {metrics['volatility']:.4f}")

                    # 피보나치 레벨
                    if wave_analysis['fibonacci_levels']:
                        st.subheader("피보나치 되돌림 레벨")
                        fib_data = []
                        for level, price in wave_analysis['fibonacci_levels'].items():
                            fib_data.append({
                                '레벨': level,
                                '가격': f"${price:.2f}"
                            })
                        st.dataframe(pd.DataFrame(fib_data), hide_index=True)

                    # 주가 차트
                    st.markdown("---")
                    st.header("📈 주가 차트 및 파동 패턴")
                    plot_stock_chart(
                        df,
                        wave_analysis['swing_points'],
                        summary['predictions'],
                        ticker
                    )

                    # 면책조항
                    st.markdown("---")
                    st.warning("""
                    ⚠️ **면책조항**: 이 예측은 Elliott Wave 이론과 기술적 분석에 기반한 참고 자료일 뿐이며,
                    투자 조언이 아닙니다. 실제 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
                    """)

                else:
                    st.error("예측을 생성할 수 없습니다. 데이터가 부족하거나 분석이 불가능합니다.")

            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

    else:
        # 초기 화면
        st.info("👈 왼쪽 사이드바에서 주식을 선택하고 '분석 시작' 버튼을 클릭하세요.")

        # 샘플 정보
        st.markdown("""
        ## 💡 주요 기능

        - **실시간 주가 데이터**: Yahoo Finance API를 통한 실시간 데이터 수집
        - **Elliott Wave 분석**: 자동 파동 패턴 인식 및 분석
        - **다기간 예측**: 1일, 5일, 10일, 30일 후 가격 예측
        - **시각화**: 인터랙티브 차트로 파동 패턴 확인
        - **신뢰 구간**: 예측의 불확실성을 고려한 상한/하한가 제공

        ## 📚 Elliott Wave 이론이란?

        Ralph Nelson Elliott이 개발한 기술적 분석 방법으로, 주가의 움직임이
        투자자 심리에 따라 반복적인 파동 패턴을 형성한다는 이론입니다.

        - **임펄스 파동(5파)**: 주 추세 방향으로 움직이는 파동
        - **조정 파동(3파)**: 주 추세 반대 방향으로 움직이는 파동
        - **피보나치 비율**: 파동의 크기와 되돌림을 예측하는 데 사용
        """)


if __name__ == "__main__":
    main()
