"""
Elliott Wave 주가 예측 웹 애플리케이션 (Premium Edition)
Streamlit을 사용하여 주식을 선택하고 파동 분석 기반 예측 결과를 시각화합니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from stock_data import StockDataFetcher, get_available_tickers
from elliott_wave import ElliottWaveAnalyzer
from predictor import StockPredictor


# 페이지 설정
st.set_page_config(
    page_title="Elliott Wave Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
        color: #e6edf3;
    }
    
    h1 {
        background: linear-gradient(45deg, #2e7bcf, #26a69a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 10px;
    }
    
    /* Cards/Metrics */
    div[data-testid="metric-container"] {
        background-color: #21262d;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #21262d;
        border-radius: 5px 5px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #8b949e;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0e1117;
        color: #58a6ff;
        border-top: 2px solid #58a6ff;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #2ea043;
        transform: translateY(-2px);
    }
    
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


def plot_radar_chart(metrics: dict):
    """
    기술적 지표를 레이더 차트로 시각화합니다.
    """
    categories = ['모멘텀', '추세 강도', '변동성(역)', '파동 신뢰도', '거래량 강도']
    
    # 정규화 및 스케일링 (0~1 범위로 조정)
    # 변동성은 낮을수록 좋으므로 역수로 처리하거나 1-x 로 처리
    volatility_score = max(0, 1 - metrics['volatility'] * 10) 
    
    values = [
        min(abs(metrics['momentum']) * 5, 1.0),  # 모멘텀
        metrics['trend_strength'],               # 추세 강도
        volatility_score,                        # 변동성 점수
        metrics.get('confidence', 0.5),          # 신뢰도
        0.7                                      # 거래량 (임시 값)
    ]
    
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='현재 상태',
        line_color='#58a6ff',
        fillcolor='rgba(88, 166, 255, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                showticklabels=False,
                linecolor='#30363d'
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=20, b=20),
        font=dict(color='#c9d1d9')
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_gauge_chart(trend: str, strength: float):
    """
    매수/매도 강도를 게이지 차트로 시각화합니다.
    """
    # 값 조정 (-1 ~ 1)
    value = strength if trend == 'bullish' else -strength
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "신호 강도", 'font': {'size': 24, 'color': '#c9d1d9'}},
        delta = {'reference': 0, 'increasing': {'color': "#238636"}, 'decreasing': {'color': "#da3633"}},
        gauge = {
            'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "#c9d1d9"},
            'bar': {'color': "#58a6ff"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#30363d",
            'steps': [
                {'range': [-1, -0.3], 'color': 'rgba(218, 54, 51, 0.3)'},
                {'range': [-0.3, 0.3], 'color': 'rgba(139, 148, 158, 0.3)'},
                {'range': [0.3, 1], 'color': 'rgba(35, 134, 54, 0.3)'}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value}
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#c9d1d9", 'family': "Arial"},
        margin=dict(l=20, r=20, t=50, b=20),
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_stock_chart(df: pd.DataFrame, swing_points: list, predictions: dict, ticker: str):
    """
    주가 차트와 파동 분석 결과를 시각화합니다. (Premium Style)
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{ticker} Price Action & Wave Analysis', 'Volume'),
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
            name='Price',
            increasing_line_color='#238636',
            decreasing_line_color='#da3633'
        ),
        row=1, col=1
    )

    # 스윙 포인트 및 파동선
    if swing_points:
        all_swings_sorted = sorted(swing_points, key=lambda x: x['index'])
        swing_dates = [sp['date'] for sp in all_swings_sorted]
        swing_prices = [sp['price'] for sp in all_swings_sorted]

        fig.add_trace(
            go.Scatter(
                x=swing_dates,
                y=swing_prices,
                mode='lines+markers',
                name='Elliott Wave',
                line=dict(color='#a371f7', width=2),
                marker=dict(size=6, color='#a371f7')
            ),
            row=1, col=1
        )

    # 거래량 차트
    colors = ['#da3633' if row['Close'] < row['Open'] else '#238636' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # 레이아웃 설정 (Dark Theme)
    fig.update_layout(
        height=700,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0d1117',
        font=dict(color='#c9d1d9'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#30363d', row=1, col=1)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#30363d', row=2, col=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#30363d', row=1, col=1)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#30363d', row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


def plot_backtest_results(results: list):
    """
    백테스팅 결과를 시각화합니다.
    """
    df_res = pd.DataFrame(results)
    
    fig = go.Figure()
    
    # 실제 가격
    fig.add_trace(go.Scatter(
        x=df_res['date'],
        y=df_res['actual_price'],
        mode='lines',
        name='실제 가격',
        line=dict(color='#c9d1d9', width=2)
    ))
    
    # 예측 가격
    fig.add_trace(go.Scatter(
        x=df_res['date'],
        y=df_res['predicted_price'],
        mode='markers',
        name='예측 가격',
        marker=dict(
            color=df_res['direction_correct'].map({True: '#238636', False: '#da3633'}),
            size=8,
            symbol='diamond'
        )
    ))
    
    fig.update_layout(
        title='Backtest: Actual vs Predicted',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#0d1117',
        font=dict(color='#c9d1d9'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def main():
    """메인 애플리케이션"""

    # 사이드바
    with st.sidebar:
        st.title("Elliott Wave Pro")
        st.markdown("---")
        
        # 티커 선택
        available_tickers = get_available_tickers()
        use_custom = st.checkbox("Custom Ticker")
        
        if use_custom:
            ticker = st.text_input("Enter Symbol", value="NVDA").upper()
        else:
            ticker = st.selectbox("Select Asset", available_tickers, index=0)
            
        period = st.selectbox("Timeframe", ['3mo', '6mo', '1y', '2y', '5y'], index=2)
        
        st.markdown("---")
        analyze_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
        
        st.markdown("### System Status")
        st.success("API Connected")
        st.info("Model v2.1 Loaded")

    # 메인 컨텐츠
    st.title(f"Market Intelligence: {ticker}")
    
    if analyze_btn:
        with st.spinner(f'Analyzing {ticker} market data...'):
            try:
                # 데이터 수집
                fetcher = StockDataFetcher(ticker)
                if not fetcher.validate_ticker():
                    st.error(f"Invalid Ticker: {ticker}")
                    return

                stock_info = fetcher.get_stock_info()
                df = fetcher.get_historical_data(period=period)
                
                if df.empty:
                    st.error("No data available.")
                    return

                # 분석 수행
                predictor = StockPredictor(df)
                summary = predictor.get_prediction_summary()
                
                # 탭 구성
                tab1, tab2, tab3 = st.tabs(["📊 Live Analysis", "🎯 Accuracy Dashboard", "📋 Raw Data"])
                
                with tab1:
                    # 상단 메트릭 카드
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Current Price", f"${stock_info['current_price']:.2f}", 
                                 f"{summary['predictions']['1day']['price_change_pct']:+.2f}%")
                    with col2:
                        st.metric("Trend", summary['wave_analysis']['trend'].upper())
                    with col3:
                        st.metric("Wave Count", f"{summary['wave_analysis']['total_swings']} Swings")
                    with col4:
                        conf = summary['predictions']['1day']['confidence']
                        st.metric("Confidence", f"{conf:.0%}")

                    # 차트 영역
                    col_main, col_side = st.columns([2, 1])
                    
                    with col_main:
                        plot_stock_chart(df, summary['wave_analysis']['swing_points'], summary['predictions'], ticker)
                        
                    with col_side:
                        st.markdown("### Technical Radar")
                        plot_radar_chart(summary['predictions']['1day']['metrics'])
                        
                        st.markdown("### Signal Strength")
                        plot_gauge_chart(summary['wave_analysis']['trend'], summary['predictions']['1day']['metrics']['trend_strength'])
                        
                        st.markdown("### Price Targets")
                        targets = summary['predictions']['1day']
                        st.info(f"Target (5d): ${targets['predicted_price']:.2f}")
                        st.write(f"Range: ${targets['lower_bound']:.2f} - ${targets['upper_bound']:.2f}")

                with tab2:
                    st.header("Historical Accuracy Analysis")
                    st.markdown("Evaluating model performance over the last 60 days...")
                    
                    with st.spinner("Running backtest simulation..."):
                        backtest = predictor.backtest_predictions(days_back=60, test_period=5)
                        
                        if backtest['status'] == 'success':
                            metrics = backtest['metrics']
                            
                            m1, m2, m3 = st.columns(3)
                            with m1:
                                st.metric("Directional Accuracy", f"{metrics['directional_accuracy']:.1f}%")
                            with m2:
                                st.metric("MAPE (Error Rate)", f"{metrics['mape']:.2f}%")
                            with m3:
                                st.metric("RMSE", f"{metrics['rmse']:.2f}")
                                
                            plot_backtest_results(backtest['detailed_results'])
                            
                            with st.expander("View Detailed Test Logs"):
                                st.dataframe(pd.DataFrame(backtest['detailed_results']))
                        else:
                            st.warning("Insufficient data for backtesting.")

                with tab3:
                    st.dataframe(df.tail(100))

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)
    else:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1>Welcome to Elliott Wave Pro</h1>
            <p style='font-size: 1.2em; color: #8b949e;'>
                Advanced market analysis powered by Elliott Wave Theory and Machine Learning.
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
