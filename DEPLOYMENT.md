# 🚀 Streamlit Cloud 배포 가이드

## 📋 사전 준비

1. Streamlit Cloud 계정 생성: https://streamlit.io/cloud
2. GitHub 계정 연동

## ⚠️ OAuth 액세스 제한 에러 해결

### 에러 메시지
```
You are not authorized to perform the requested action: Although you appear to have
the correct authorization credentials, the `waterfirst-suji` organization has enabled
OAuth App access restrictions...
```

### 해결 방법

#### 방법 1: 조직에서 Streamlit OAuth 앱 승인 (권장)

**조직 관리자인 경우:**

1. GitHub 조직 설정으로 이동:
   ```
   https://github.com/organizations/waterfirst-suji/settings/oauth_application_policy
   ```

2. "Third-party access" 탭 클릭

3. "Streamlit" 찾기 또는 pending requests 확인

4. **"Grant"** 또는 **"Approve"** 클릭하여 Streamlit 승인

**조직 관리자가 아닌 경우:**

1. 조직 관리자에게 연락하여 Streamlit OAuth 앱 승인 요청

2. 또는 아래 "방법 2" 사용

#### 방법 2: 개인 계정으로 Fork

1. GitHub에서 이 저장소를 개인 계정으로 fork:
   - 저장소 페이지에서 "Fork" 버튼 클릭
   - 개인 계정 선택

2. Streamlit Cloud에서 fork된 저장소 사용

#### 방법 3: Public Repository로 변경

1. 조직 저장소를 public으로 변경:
   ```
   Settings → Danger Zone → Change visibility → Make public
   ```

2. Public 저장소는 OAuth 제한 없이 배포 가능

## 🎯 Streamlit Cloud 배포 단계

### 1. Streamlit Cloud 로그인

https://share.streamlit.io/ 방문

### 2. 새 앱 배포

1. **"New app"** 클릭

2. 저장소 정보 입력:
   - **Repository**: `waterfirst-suji/chumul` 또는 fork한 저장소
   - **Branch**: `claude/elliott-wave-stock-predictor-011CUuzChdMbCYLsKAiFKUtz`
   - **Main file path**: `app.py`

3. **Advanced settings** (선택사항):
   - Python version: `3.9` 또는 `3.10`
   - Secrets: 필요한 경우 API 키 등 추가

4. **"Deploy!"** 클릭

### 3. 배포 완료

- 배포는 약 2-5분 소요
- 완료되면 공개 URL 제공 (예: `https://your-app.streamlit.app`)

## 🔧 배포 후 문제 해결

### 패키지 설치 에러

requirements.txt의 패키지 버전 확인:
```bash
streamlit==1.29.0
yfinance==0.2.33
pandas==2.1.4
numpy==1.26.2
plotly==5.18.0
scipy==1.11.4
scikit-learn==1.3.2
ta==0.11.0
```

### 메모리 부족 에러

- Streamlit Cloud 무료 티어는 1GB RAM 제한
- 데이터 기간을 줄이거나 캐싱 최적화 필요

### 앱이 느린 경우

데이터 캐싱 추가 (이미 구현됨):
```python
@st.cache_data
def load_data(ticker, period):
    # ...
```

## 📱 배포된 앱 관리

### 앱 업데이트

1. GitHub에 새 코드 push
2. Streamlit Cloud가 자동으로 재배포

### 앱 중지/삭제

1. Streamlit Cloud 대시보드
2. 앱 선택 → Settings → Delete

### 로그 확인

1. 앱 페이지에서 "Manage app" 클릭
2. "Logs" 탭에서 에러 확인

## 🌐 공개 URL 공유

배포 완료 후:
- 공개 URL: `https://[your-app-name].streamlit.app`
- 누구나 접속 가능
- 사용량 제한: 무료 티어는 일일 사용량 제한 있음

## 💡 팁

1. **Branch 이름 단순화**
   - 메인 브랜치로 병합 후 배포 권장
   - 긴 branch 이름은 URL에 영향

2. **Secrets 관리**
   - API 키는 절대 코드에 포함 금지
   - Streamlit Cloud의 Secrets 기능 사용

3. **성능 최적화**
   - `@st.cache_data` 데코레이터 활용
   - 불필요한 데이터 로딩 최소화

4. **에러 처리**
   - try-except 블록으로 안정성 향상
   - 사용자 친화적 에러 메시지

## 📞 지원

- Streamlit 문서: https://docs.streamlit.io/
- 커뮤니티 포럼: https://discuss.streamlit.io/
- GitHub Issues: 저장소 이슈 페이지
