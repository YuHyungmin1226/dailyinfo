# DailyInfo - 데이터 정보 대시보드

## 프로젝트 소개
DailyInfo는 다양한 실시간 정보를 한 곳에서 확인할 수 있는 Streamlit 기반 대시보드 애플리케이션입니다. 개선된 UI/UX와 데이터 시각화 기능을 제공합니다.

## 🚀 주요 기능

### 📊 대시보드 개요
- 전체 시스템 현황을 한눈에 확인
- 최근 업데이트 시간 표시 (한국 시간 기준)
- 메트릭 카드 형태의 직관적인 정보 제공

### 🎵 음악 차트
- **벅스 일간 차트**: TOP 100 실시간 확인
- 인터랙티브 차트 시각화
- 아티스트별 색상 구분
- 순위 범위 선택 (TOP 10/20/50/100)

### 📚 도서 정보
- **교보문고 베스트셀러**: TOP 100 확인
- 출판사별 통계 차트
- 저자별 통계 차트
- 순위 범위 선택 (TOP 10/20/50/100)
- 구조화된 데이터 표시

### 🌤️ 날씨 정보
- **서울 실시간 날씨**: OpenWeatherMap API 연동
- 기온, 습도, 바람 속도, 날씨 상태
- 직관적인 메트릭 카드 표시

### 📰 뉴스
- **Google 뉴스 실시간 헤드라인**: RSS 피드 기반
- 출처 및 발행일 정보 (한국 시간 기준)
- 클릭 가능한 링크 제공
- 출처별 통계 차트

### ⚙️ 설정
- 캐시 관리 (1-60분 설정 가능)
- API 키 설정
- 시스템 설정 관리

## 🛠️ 기술 스택

### Frontend
- **Streamlit**: 웹 애플리케이션 프레임워크
- **Plotly**: 인터랙티브 차트 및 시각화
- **CSS**: 커스텀 스타일링

### Backend
- **Python 3.8+**: 메인 프로그래밍 언어
- **Pandas**: 데이터 처리 및 분석
- **Requests**: HTTP 요청 처리
- **Aiohttp**: 비동기 HTTP 클라이언트
- **Pytz**: 시간대 처리

### 데이터 처리
- **BeautifulSoup4**: 웹 스크래핑
- **Selenium**: 동적 웹페이지 처리
- **NumPy**: 수치 계산

## 📦 설치 방법

### 1. 저장소 클론
```bash
git clone [repository-url]
cd dailyinfo
```

### 2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. API 키 설정

#### 로컬 실행 시
날씨 API를 사용하려면 OpenWeatherMap API 키가 필요합니다:

```bash
# .streamlit/secrets.toml 파일 생성
WEATHER_API_KEY = "your_openweathermap_api_key_here"
```

#### Streamlit Cloud 배포 시
1. [share.streamlit.io](https://share.streamlit.io)에 로그인
2. 프로젝트 선택 → Settings 탭
3. Secrets 섹션에 다음 내용 입력:
```toml
WEATHER_API_KEY = "your_openweathermap_api_key_here"
```

## 🚀 실행 방법
```bash
streamlit run dailyinfo.py
```

실행 후 웹 브라우저에서 `http://localhost:8501`로 접속하여 대시보드를 확인할 수 있습니다.

## 📖 사용법

### 1. 대시보드 탐색
- 왼쪽 사이드바에서 원하는 정보 카테고리를 선택
- 각 섹션별로 실시간 데이터 확인
- 인터랙티브 차트와 그래프 활용

### 2. 데이터 시각화
- 차트에 마우스 오버하여 상세 정보 확인
- 차트 확대/축소 및 이동 가능
- 데이터 테이블 정렬 및 필터링

### 3. 설정 관리
- 캐시 유지 시간 조정 (1-60분)
- API 키 설정
- 캐시 초기화

## 🔧 주요 개선사항

### 성능 최적화
- **캐싱 시스템**: 5분 기본 캐시로 API 호출 최소화
- **세션 상태 관리**: 사용자별 데이터 저장
- **비동기 처리**: 동시 데이터 로딩 지원
- **시간대 처리**: 한국 시간(UTC+9) 기준 통일

### UI/UX 개선
- **반응형 디자인**: 다양한 화면 크기 지원
- **직관적인 네비게이션**: 이모지와 아이콘 활용
- **로딩 상태 표시**: 사용자 피드백 제공

### 데이터 시각화
- **인터랙티브 차트**: Plotly 기반 차트
- **메트릭 카드**: 핵심 정보 강조 표시
- **구조화된 데이터**: 테이블 형태로 정리

### 에러 처리
- **강화된 예외 처리**: 구체적인 에러 메시지
- **Fallback 데이터**: API 실패 시 Mock 데이터 제공
- **사용자 친화적 메시지**: 명확한 안내

## 📝 주의사항

### 필수 요구사항
- Python 3.8 이상
- 인터넷 연결 필수
- 최소 4GB RAM 권장

### API 사용
- OpenWeatherMap API 키는 무료 계정으로도 사용 가능
- 일일 API 호출 제한 확인 필요
- 웹 스크래핑 시 해당 웹사이트의 이용약관 준수

### 성능 고려사항
- 캐시 설정으로 API 호출 최소화
- 대용량 데이터 처리 시 메모리 사용량 모니터링
- 동시 사용자 수에 따른 서버 리소스 관리

## 🤝 기여하기

### 버그 리포트
- GitHub Issues를 통해 버그 리포트
- 상세한 재현 단계와 환경 정보 포함

### 기능 제안
- 새로운 기능 아이디어 제안
- 사용 사례와 기대 효과 설명

### 코드 기여
- Fork 후 Pull Request 제출
- 코드 스타일 가이드 준수

## 📄 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원
- **이슈 트래커**: GitHub Issues
- **문서**: 이 README 파일 참조
- **커뮤니티**: GitHub Discussions

---

**DailyInfo** - 더 나은 정보 접근성을 위한 대시보드 🚀 