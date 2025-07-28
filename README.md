# 📊 DailyInfo - 일일 정보 수집 및 대시보드

일일 정보를 자동으로 수집하고 웹 대시보드로 제공하는 Python 애플리케이션입니다.

## ✨ 주요 기능

### 📈 데이터 수집
- **음원 차트**: 멜론, 벅스 일간 차트 TOP 100
- **도서 순위**: 알라딘 베스트셀러 TOP 50
- **주식 정보**: 일일 주식 추천 및 분석
- **뉴스**: 구글 뉴스 최신 기사
- **날씨**: 서울 날씨 정보

### 🌐 웹 대시보드
- **Streamlit 기반**: 직관적인 웹 인터페이스
- **실시간 업데이트**: 최신 정보 자동 수집
- **반응형 디자인**: 모바일/데스크톱 호환

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/YuHyungmin1226/dailyinfo.git
cd dailyinfo
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
streamlit run streamlit_dashboard.py
```

### 4. 브라우저에서 접속
```
http://localhost:8501
```

## 📁 파일 구조

```
dailyinfo/
├── streamlit_dashboard.py      # 메인 웹 대시보드
├── daily_info.py              # 일일 정보 수집기 (13KB, 327줄)
├── melon_daily_chart.py       # 멜론 차트 수집
├── bugs_daily_chart.py        # 벅스 차트 수집
├── book_rank.py              # 도서 베스트셀러 수집
├── daily_stock_recommendation.py  # 주식 추천 시스템
├── NewsPost.py               # 뉴스 수집
├── NewsAlert.py              # 뉴스 알림
├── Weather_review_auto.py    # 날씨 정보 수집
├── requirements.txt          # Python 의존성
├── README.md                # 프로젝트 문서
└── README_ORIGINAL.md       # 원본 README
```

## 🎯 사용 방법

### 웹 대시보드
1. **멜론 일간 차트**: TOP 100 곡 목록
2. **벅스 일간 차트**: TOP 100 곡 목록
3. **도서 순위**: 알라딘 베스트셀러 TOP 50
4. **날씨 정보**: 서울 현재 날씨
5. **뉴스**: 구글 뉴스 최신 10건

### 개별 모듈 실행
```bash
# 일일 정보 수집기
python daily_info.py

# 멜론 차트 수집
python melon_daily_chart.py

# 벅스 차트 수집
python bugs_daily_chart.py

# 도서 순위 수집
python book_rank.py

# 주식 추천
python daily_stock_recommendation.py

# 뉴스 수집
python NewsPost.py

# 날씨 정보
python Weather_review_auto.py
```

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.7+
- **웹 스크래핑**: requests, beautifulsoup4
- **스케줄링**: schedule
- **텍스트 처리**: textblob

## 📊 데이터 소스

- **멜론**: https://www.melon.com
- **벅스**: https://music.bugs.co.kr
- **알라딘**: https://www.aladin.co.kr
- **구글 뉴스**: https://news.google.com
- **OpenWeatherMap**: 날씨 API

## 🔧 커스터마이징

### 새로운 데이터 소스 추가
`streamlit_dashboard.py`에 새로운 메뉴 항목과 함수를 추가할 수 있습니다.

### 스케줄링 설정
`daily_info.py`에서 자동 수집 주기를 조정할 수 있습니다.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자

**YuHyungmin1226** - [GitHub](https://github.com/YuHyungmin1226)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요! 