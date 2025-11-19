# Implementation Plan - Premium UI & Advanced Analytics Upgrade

## Goal Description
Upgrade the existing Streamlit application to have a "Premium" financial terminal aesthetic. Introduce a new "Backtesting & Accuracy" module to evaluate how well the Elliott Wave predictions perform across multiple stocks. Add diverse visualizations like Radar charts and Accuracy trends.

## User Review Required
> [!IMPORTANT]
> This update will significantly change the visual appearance of the application.
> It also introduces heavy computation for the "Accuracy Analysis" as it needs to fetch historical data and run predictions for multiple past dates.

## Proposed Changes

### 1. UI/UX Overhaul (Premium Design)
*   **Theme**: Dark mode with Gold/Blue accents.
*   **Components**: Custom CSS for cards, metrics, and headers.
*   **Layout**: Use Tabs to separate "Live Analysis" and "Accuracy Dashboard".

### 2. Backend Logic (Accuracy Metrics)
#### [MODIFY] [predictor.py](file:///d:/python/elliot_wave_theory/chumul/predictor.py)
*   Add `backtest_predictions(days_back, test_period)` method.
*   Calculate metrics:
    *   **Directional Accuracy**: % of time the trend direction was correct.
    *   **Target Hit Rate**: % of time the price reached the predicted target.
    *   **MAPE**: Mean Absolute Percentage Error of the price prediction.

### 3. Frontend Implementation
#### [MODIFY] [app.py](file:///d:/python/elliot_wave_theory/chumul/app.py)
*   **Inject Custom CSS**: For fonts, gradients, and spacing.
*   **New Tab: Dashboard**:
    *   Radar Chart: Showing 'Momentum', 'Trend', 'Volatility', 'Wave Confidence', 'Volume'.
    *   Gauge Chart: Overall "Buy/Sell" signal strength.
*   **New Tab: Backtest/Accuracy**:
    *   Select multiple stocks to compare.
    *   Show a leaderboard of which stocks follow Elliott Wave theory best.
    *   Visual comparison of Predicted vs Actual prices over the last 30-60 days.

## Verification Plan

### Automated Tests
*   None (Visual & Logic verification via App).

### Manual Verification
1.  **UI Check**: Verify the dark theme, custom fonts, and "Premium" feel.
2.  **Live Analysis**: Check if the standard analysis still works.
3.  **Backtest**: Run the accuracy check on 'NVDA' and 'AAPL'. Verify it generates metrics (Accuracy %, MAPE).
4.  **Visuals**: Check if the Radar chart and Backtest charts render correctly.
