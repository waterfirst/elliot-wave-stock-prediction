@echo off
echo Elliott Wave 주가 예측 시스템 시작...
echo.

REM 가상환경 확인
if not exist "venv\" (
    echo 가상환경이 없습니다. 생성 중...
    python -m venv venv
)

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM 패키지 설치
echo 필요한 패키지 설치 중...
pip install -q -r requirements.txt

REM Streamlit 앱 실행
echo.
echo 애플리케이션을 시작합니다...
echo 브라우저에서 http://localhost:8501 을 확인하세요.
echo.

streamlit run app.py
