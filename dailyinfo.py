"""
DailyInfo - 데이터 정보 대시보드
실시간 음악 차트, 날씨, 뉴스 정보를 제공하는 Streamlit 애플리케이션
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import pytz
import pandas as pd
import plotly.express as px
from typing import List, Dict, Optional, Tuple
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from enum import Enum

# 상수 정의
class Constants:
    """애플리케이션 상수"""
    CACHE_DURATION = 300  # 5분 캐시
    REQUEST_TIMEOUT = 10  # 요청 타임아웃 (초)
    MAX_CHART_ITEMS = 100  # 최대 차트 항목 수
    
    # URL
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    NEIS_BASE_URL = "https://open.neis.go.kr/hub"
    
    # NEIS API 엔드포인트
    NEIS_SCHOOL_INFO = f"{NEIS_BASE_URL}/schoolInfo"
    NEIS_MEAL_INFO = f"{NEIS_BASE_URL}/mealServiceDietInfo"
    NEIS_HIS_TIMETABLE = f"{NEIS_BASE_URL}/hisTimetable"  # 고등학교
    NEIS_MIS_TIMETABLE = f"{NEIS_BASE_URL}/misTimetable"  # 중학교
    NEIS_ELS_TIMETABLE = f"{NEIS_BASE_URL}/elsTimetable"  # 초등학교
    NEIS_SCHOOL_SCHEDULE = f"{NEIS_BASE_URL}/SchoolSchedule"  # 학사일정
    
    # 지역 정보 (교육청 코드)
    REGIONS = {
        "서울특별시": "B10",
        "부산광역시": "C10",
        "대구광역시": "D10",
        "인천광역시": "E10",
        "광주광역시": "F10",
        "대전광역시": "G10",
        "울산광역시": "H10",
        "세종특별자치시": "I10",
        "경기도": "J10",
        "강원도": "K10",
        "충청북도": "M10",
        "충청남도": "N10",
        "전라북도": "P10",
        "전라남도": "Q10",
        "경상북도": "R10",
        "경상남도": "S10",
        "제주특별자치도": "T10"
    }
    
    # HTTP 헤더
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 주요 도시 좌표
    CITIES = {
        "서울": {"lat": 37.5665, "lon": 126.9780, "name": "서울"},
        "부산": {"lat": 35.1796, "lon": 129.0756, "name": "부산"},
        "대구": {"lat": 35.8714, "lon": 128.6014, "name": "대구"},
        "인천": {"lat": 37.4563, "lon": 126.7052, "name": "인천"},
        "광주": {"lat": 35.1595, "lon": 126.8526, "name": "광주"},
        "대전": {"lat": 36.3504, "lon": 127.3845, "name": "대전"},
        "울산": {"lat": 35.5384, "lon": 129.3114, "name": "울산"},
        "세종": {"lat": 36.4800, "lon": 127.2890, "name": "세종"},
        "수원": {"lat": 37.2636, "lon": 127.0286, "name": "수원"},
        "고양": {"lat": 37.6584, "lon": 126.8320, "name": "고양"},
        "용인": {"lat": 37.2411, "lon": 127.1776, "name": "용인"},
        "창원": {"lat": 35.2278, "lon": 128.6817, "name": "창원"},
        "포항": {"lat": 36.0320, "lon": 129.3650, "name": "포항"},
        "전주": {"lat": 35.8242, "lon": 127.1480, "name": "전주"},
        "청주": {"lat": 36.6424, "lon": 127.4890, "name": "청주"},
        "춘천": {"lat": 37.8813, "lon": 127.7300, "name": "춘천"},
        "강릉": {"lat": 37.7519, "lon": 128.8760, "name": "강릉"},
        "제주": {"lat": 33.4996, "lon": 126.5312, "name": "제주"}
    }
    
    # 서울 좌표 (기본값)
    SEOUL_LAT = 37.5665
    SEOUL_LON = 126.9780
    
    # 한국 시간대
    KOREA_TZ = pytz.timezone('Asia/Seoul')

@dataclass
class WeatherData:
    """날씨 데이터 클래스"""
    city: str
    temperature: float
    humidity: int
    description: str
    wind_speed: float
    wind_direction: int

@dataclass
class SchoolData:
    """학교 데이터 클래스"""
    school_code: str
    school_name: str
    school_level: str
    address: str
    phone: str
    fax: str
    homepage: str

@dataclass
class MealData:
    """급식 데이터 클래스"""
    date: str
    meal_type: str
    menu: str
    nutrition_info: str
    day_name: str = ""  # 요일 정보

@dataclass
class TimetableData:
    """시간표 데이터 클래스"""
    date: str
    period: int
    subject: str
    teacher: str
    classroom: str
    day_name: str = ""  # 요일 정보

@dataclass
class SchoolScheduleData:
    """학사일정 데이터 클래스"""
    date: str
    event_name: str
    event_type: str
    event_content: str
    day_name: str = ""  # 요일 정보

@dataclass
class NewsData:
    """뉴스 데이터 클래스"""
    title: str
    link: str
    source: str
    published: str

class DataFetcher:
    """데이터 수집을 위한 클래스"""
    
    @staticmethod
    def get_weather_info(city_name: str = "서울") -> Optional[WeatherData]:
        """날씨 정보 수집"""
        try:
            # Streamlit secrets에서 먼저 시도, 없으면 환경 변수에서 시도
            weather_api_key = st.secrets.get("WEATHER_API_KEY", "")
            if not weather_api_key:
                import os
                weather_api_key = os.environ.get("WEATHER_API_KEY", "")
            
            if not weather_api_key or weather_api_key == "your_api_key_here":
                st.error("OpenWeatherMap API 키가 설정되지 않았습니다. Streamlit Cloud의 Settings > Secrets에서 WEATHER_API_KEY를 설정해주세요.")
                return None
            
            # 선택된 도시의 좌표 가져오기
            if city_name not in Constants.CITIES:
                st.error(f"지원하지 않는 도시입니다: {city_name}")
                return None
            
            city_data = Constants.CITIES[city_name]
            
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': city_data["lat"],
                'lon': city_data["lon"],
                'appid': weather_api_key,
                'units': 'metric',
                'lang': 'kr'
            }
            
            response = requests.get(url, params=params, timeout=Constants.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                return WeatherData(
                    city=city_data["name"],
                    temperature=data["main"]["temp"],
                    humidity=data["main"]["humidity"],
                    description=data["weather"][0]["description"],
                    wind_speed=data["wind"]["speed"],
                    wind_direction=data["wind"]["deg"]
                )
            else:
                st.error(f"날씨 정보를 불러올 수 없습니다. (상태 코드: {response.status_code})")
                return None
                
        except Exception as e:
            st.error(f"날씨 정보를 불러올 수 없습니다: {e}")
            return None

    @staticmethod
    def get_news() -> List[NewsData]:
        """Google 뉴스 RSS 피드에서 뉴스 데이터 가져오기"""
        try:
            import xml.etree.ElementTree as ET
            from datetime import datetime
            
            # Google 뉴스 RSS 피드 요청
            response = requests.get(Constants.GOOGLE_NEWS_RSS_URL, 
                                  headers=Constants.DEFAULT_HEADERS, 
                                  timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            
            news_data = []
            
            # RSS 피드에서 뉴스 항목 추출
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                
                if title_elem is not None and link_elem is not None:
                    title = title_elem.text.strip()
                    link = link_elem.text.strip()
                    
                    # 제목이 너무 짧거나 비어있으면 건너뛰기
                    if len(title) < 5:
                        continue
                    
                    # 출처 추출 (제목에서 마지막 괄호 부분)
                    source = "Google 뉴스"
                    if " - " in title:
                        title_parts = title.split(" - ")
                        if len(title_parts) >= 2:
                            title = " - ".join(title_parts[:-1])
                            source = title_parts[-1]
                    
                    # 날짜 파싱
                    published = "최근"
                    if pub_date_elem is not None:
                        try:
                            # RFC 822 형식의 날짜를 파싱 (UTC 기준)
                            date_str = pub_date_elem.text.strip()
                            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                            
                            # UTC를 한국 시간으로 변환
                            utc_tz = pytz.UTC
                            utc_time = utc_tz.localize(date_obj)
                            korea_time = utc_time.astimezone(Constants.KOREA_TZ)
                            
                            # 한국 시간으로 포맷팅
                            published = korea_time.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            published = "최근"
                    
                    news_data.append(NewsData(title, link, source, published))
            
            return news_data[:20]  # 최대 20개만 반환
            
        except Exception as e:
            st.error(f"뉴스 데이터를 불러올 수 없습니다: {e}")
            return []

    @staticmethod
    def get_schools(region_code: str, school_name: str = "") -> List[SchoolData]:
        """학교 목록 조회"""
        try:
            params = {
                'KEY': 'c4ef97602ca54adc9e4cd49648b247f6',  # 테스트용 API 키
                'Type': 'json',
                'ATPT_OFCDC_SC_CODE': region_code
            }
            
            if school_name:
                params['SCHUL_NM'] = school_name
            
            response = requests.get(Constants.NEIS_SCHOOL_INFO, params=params, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if 'schoolInfo' not in data:
                return []
            
            schools = []
            school_list = data['schoolInfo'][1]['row']
            
            for school in school_list:
                schools.append(SchoolData(
                    school_code=school.get('SD_SCHUL_CODE', ''),
                    school_name=school.get('SCHUL_NM', ''),
                    school_level=school.get('SCHUL_KND_SC_NM', ''),
                    address=school.get('ORG_RDNMA', ''),
                    phone=school.get('ORG_TELNO', ''),
                    fax=school.get('ORG_FAXNO', ''),
                    homepage=school.get('HMPG_ADRES', '')
                ))
            
            return schools
            
        except Exception as e:
            st.error(f"학교 정보를 불러올 수 없습니다: {e}")
            return []

    @staticmethod
    def get_meals(school_code: str, date: str, region_code: str = 'B10') -> List[MealData]:
        """급식 정보 조회"""
        try:
            params = {
                'KEY': 'c4ef97602ca54adc9e4cd49648b247f6',  # 테스트용 API 키
                'Type': 'json',
                'ATPT_OFCDC_SC_CODE': region_code,  # 선택된 지역의 교육청 코드 사용
                'SD_SCHUL_CODE': school_code,
                'MLSV_YMD': date
            }
            
            response = requests.get(Constants.NEIS_MEAL_INFO, params=params, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # RESULT 키가 있으면 데이터가 없는 경우
            if 'RESULT' in data:
                result = data['RESULT']
                if result.get('CODE') == 'INFO-200':
                    return []  # 데이터가 없음 (방학, 주말, 공휴일 등)
            
            if 'mealServiceDietInfo' not in data:
                return []
            
            meals = []
            meal_list = data['mealServiceDietInfo'][1]['row']
            
            for meal in meal_list:
                meals.append(MealData(
                    date=meal.get('MLSV_YMD', ''),
                    meal_type=meal.get('MMEAL_SC_NM', ''),
                    menu=meal.get('DDISH_NM', ''),
                    nutrition_info=meal.get('CAL_INFO', '')
                ))
            
            return meals
            
        except Exception as e:
            st.error(f"급식 정보를 불러올 수 없습니다: {e}")
            return []

    @staticmethod
    def get_timetable(school_code: str, grade: str, class_num: str, date: str, region_code: str = 'B10', school_level: str = "고등학교") -> List[TimetableData]:
        """시간표 정보 조회"""
        try:
            # 학교 종류에 따라 다른 API 사용
            api_url = Constants.NEIS_HIS_TIMETABLE
            
            if school_level == "중학교":
                api_url = Constants.NEIS_MIS_TIMETABLE
            elif school_level == "초등학교":
                api_url = Constants.NEIS_ELS_TIMETABLE
            
            params = {
                'KEY': 'c4ef97602ca54adc9e4cd49648b247f6',  # 테스트용 API 키
                'Type': 'json',
                'ATPT_OFCDC_SC_CODE': region_code,  # 선택된 지역의 교육청 코드 사용
                'SD_SCHUL_CODE': school_code,
                'GRADE': grade,
                'CLASS_NM': class_num,
                'TI_FROM_YMD': date,
                'TI_TO_YMD': date
            }
            
            response = requests.get(api_url, params=params, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # RESULT 키가 있으면 데이터가 없는 경우
            if 'RESULT' in data:
                result = data['RESULT']
                if result.get('CODE') == 'INFO-200':
                    return []  # 데이터가 없음 (방학, 주말, 공휴일 등)
            
            if 'hisTimetable' not in data and 'misTimetable' not in data and 'elsTimetable' not in data:
                return []
            
            timetable = []
            timetable_key = 'hisTimetable' if school_level == "고등학교" else 'misTimetable' if school_level == "중학교" else 'elsTimetable'
            timetable_list = data[timetable_key][1]['row']
            
            for item in timetable_list:
                timetable.append(TimetableData(
                    date=item.get('ALL_TI_YMD', ''),
                    period=int(item.get('PERIO', 0)),
                    subject=item.get('ITRT_CNTNT', ''),
                    teacher=item.get('TEACHER_NM', ''),
                    classroom=item.get('CLASS_NM', '')
                ))
            
            return timetable
            
        except Exception as e:
            st.error(f"시간표 정보를 불러올 수 없습니다: {e}")
            return []

    @staticmethod
    def get_school_schedule(school_code: str, from_date: str, to_date: str, region_code: str = 'B10') -> List[SchoolScheduleData]:
        """학사일정 정보 조회"""
        try:
            params = {
                'KEY': 'c4ef97602ca54adc9e4cd49648b247f6',  # 테스트용 API 키
                'Type': 'json',
                'ATPT_OFCDC_SC_CODE': region_code,  # 선택된 지역의 교육청 코드 사용
                'SD_SCHUL_CODE': school_code,
                'AA_FROM_YMD': from_date,  # 시작일
                'AA_TO_YMD': to_date       # 종료일
            }
            
            response = requests.get(Constants.NEIS_SCHOOL_SCHEDULE, params=params, timeout=Constants.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # RESULT 키가 있으면 데이터가 없는 경우
            if 'RESULT' in data:
                result = data['RESULT']
                if result.get('CODE') == 'INFO-200':
                    return []  # 데이터가 없음
                elif result.get('CODE') == 'ERROR-300':
                    st.error("필수 값이 누락되었습니다. 요청인자를 확인해주세요.")
                    return []
            
            if 'SchoolSchedule' not in data:
                return []
            
            schedules = []
            schedule_list = data['SchoolSchedule'][1]['row']
            
            for schedule in schedule_list:
                schedules.append(SchoolScheduleData(
                    date=schedule.get('AA_YMD', ''),
                    event_name=schedule.get('EVENT_NM', ''),
                    event_type=schedule.get('EVENT_CNTNT', ''),
                    event_content=schedule.get('ONE_GRADE_EVENT_YN', '')  # 전체 학년 이벤트 여부
                ))
            
            return schedules
            
        except Exception as e:
            st.error(f"학사일정 정보를 불러올 수 없습니다: {e}")
            return []

class DataProcessor:
    """데이터 처리 및 시각화 클래스"""
    
    @staticmethod
    def create_weather_display(weather_data: WeatherData) -> None:
        """날씨 정보 표시"""
        st.subheader(f"🌤️ {weather_data.city} 날씨 정보")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ 기온", f"{weather_data.temperature:.1f}°C")
        
        with col2:
            st.metric("💧 습도", f"{weather_data.humidity}%")
        
        with col3:
            st.metric("💨 풍속", f"{weather_data.wind_speed:.1f} m/s")
        
        with col4:
            # 바람 방향
            directions = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]
            direction_index = int((weather_data.wind_direction + 22.5) / 45) % 8
            wind_direction = directions[direction_index]
            st.metric("🧭 풍향", f"{wind_direction}")
        
        # 날씨 설명
        st.info(f"📝 날씨 상태: {weather_data.description}")

class CacheManager:
    """캐시 관리 클래스"""
    
    @staticmethod
    def get_cached_data(key: str, fetcher_func, *args):
        """캐시된 데이터 반환 또는 새로 수집"""
        current_time = time.time()
        
        # 캐시 확인
        if (key in st.session_state.data_cache and 
            key in st.session_state.last_update and
            current_time - st.session_state.last_update[key] < Constants.CACHE_DURATION):
            return st.session_state.data_cache[key]
        
        # 새 데이터 수집
        with st.spinner(f"{key} 데이터를 수집하는 중..."):
            data = fetcher_func(*args)
            st.session_state.data_cache[key] = data
            st.session_state.last_update[key] = current_time
        
        return data
    
    @staticmethod
    def clear_cache():
        """캐시 초기화"""
        st.session_state.data_cache.clear()
        st.session_state.last_update.clear()

class UIComponents:
    """UI 컴포넌트 클래스"""
    
    @staticmethod
    def setup_page():
        """페이지 설정"""
        st.set_page_config(
            page_title="DailyInfo - 데이터 정보 대시보드",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS 스타일 추가
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #1f77b4;
            }
            .loading-spinner {
                text-align: center;
                padding: 2rem;
            }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def initialize_session_state():
        """세션 상태 초기화"""
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}
        if 'last_update' not in st.session_state:
            st.session_state.last_update = {}
        
        # 학교 정보 세션 상태 초기화
        if 'selected_region' not in st.session_state:
            st.session_state.selected_region = "서울특별시"
        if 'school_search' not in st.session_state:
            st.session_state.school_search = ""
        if 'selected_school_idx' not in st.session_state:
            st.session_state.selected_school_idx = None
        if 'selected_grade' not in st.session_state:
            st.session_state.selected_grade = "1"
        if 'selected_class' not in st.session_state:
            st.session_state.selected_class = "1"
        if 'selected_week_idx' not in st.session_state:
            st.session_state.selected_week_idx = None  # 브라우저 재시작 시 오늘 주간으로 설정

    
    @staticmethod
    def create_sidebar() -> str:
        """사이드바 생성"""
        with st.sidebar:
            # 클릭 가능한 타이틀 (새로고침 기능)
            if st.button("📊 DailyInfo", key="sidebar_title_button", use_container_width=True):
                st.rerun()
            
            st.markdown("---")
            
            # 메뉴 선택
            menu = st.selectbox(
                "메뉴 선택",
                ["🌤️ 날씨 정보", "📰 뉴스", "🏫 학교 정보", "⚙️ 설정"]
            )
            
            st.markdown("---")
            st.markdown("### 📡 데이터 출처")
            st.markdown("- **학교 정보**: NEIS Open API")
            st.markdown("- **급식/시간표/학사일정**: NEIS Open API")
            st.markdown("- **날씨 정보**: OpenWeatherMap API")
            st.markdown("- **뉴스**: Google 뉴스 RSS")
            
            st.markdown("---")
            st.markdown("### 🔄 업데이트 주기")
            st.markdown("모든 데이터는 **5분마다** 자동으로 갱신됩니다.")
            
            return menu

class PageHandlers:
    """페이지 핸들러 클래스"""
    


    @staticmethod
    def show_weather_info():
        """날씨 정보 페이지"""
        st.header("🌤️ 날씨 정보")
        
        # 도시 선택
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_city = st.selectbox(
                "도시 선택",
                list(Constants.CITIES.keys()),
                index=0
            )
        
        # 선택된 도시의 날씨 정보 가져오기
        weather_data = CacheManager.get_cached_data(
            f"weather_{selected_city}", 
            DataFetcher.get_weather_info, 
            selected_city
        )
        
        if weather_data:
            DataProcessor.create_weather_display(weather_data)
            
            # 추가 정보
            st.markdown("---")
            st.subheader("📊 날씨 상세 정보")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**도시**: {weather_data.city}")
                st.write(f"**기온**: {weather_data.temperature:.1f}°C")
                st.write(f"**습도**: {weather_data.humidity}%")
            
            with col2:
                st.write(f"**풍속**: {weather_data.wind_speed:.1f} m/s")
                st.write(f"**풍향**: {weather_data.wind_direction}°")
                st.write(f"**날씨**: {weather_data.description}")
        else:
            st.error("날씨 정보를 불러올 수 없습니다.")

    @staticmethod
    def show_news():
        """뉴스 페이지"""
        st.header("📰 뉴스")
        
        # 데이터 출처 정보
        st.info("📡 Google 뉴스 RSS 피드를 통해 실시간 뉴스를 제공합니다.")
        
        news_data = CacheManager.get_cached_data("news", DataFetcher.get_news)
        
        if news_data:
            # 뉴스 목록 표시
            for i, news in enumerate(news_data, 1):
                with st.container():
                    st.markdown(f"**{i}. [{news.title}]({news.link})**")
                    st.caption(f"출처: {news.source} | 발행: {news.published}")
                    st.markdown("---")
            
            # 뉴스 소스별 통계
            st.subheader("📊 뉴스 소스별 통계")
            source_counts = {}
            for news in news_data:
                source_counts[news.source] = source_counts.get(news.source, 0) + 1
            
            if source_counts:
                fig = px.pie(
                    values=list(source_counts.values()),
                    names=list(source_counts.keys()),
                    title="뉴스 소스별 분포"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("뉴스 데이터를 불러올 수 없습니다.")

    @staticmethod
    def show_school_info():
        """학교 정보 페이지"""
        st.header("🏫 학교 정보")
        
        # 1. 지역 선택
        col1, col2 = st.columns(2)
        with col1:
            selected_region = st.selectbox(
                "지역 선택",
                list(Constants.REGIONS.keys()),
                index=list(Constants.REGIONS.keys()).index(st.session_state.selected_region),
                key="region_selectbox"
            )
            st.session_state.selected_region = selected_region
        
        # 2. 학교 검색
        with col2:
            school_search = st.text_input(
                "학교명 검색 (키워드 입력)",
                value=st.session_state.school_search,
                key="school_search_input"
            )
            st.session_state.school_search = school_search
        
        # 3. 학교 목록 조회
        if selected_region:
            region_code = Constants.REGIONS[selected_region]
            schools = CacheManager.get_cached_data(
                f"schools_{region_code}_{school_search}", 
                DataFetcher.get_schools, 
                region_code, 
                school_search
            )
            
            if schools:
                # 4. 학교 선택
                school_names = [f"{school.school_name} ({school.school_level})" for school in schools]
                
                # 이전에 선택된 학교가 현재 목록에 있는지 확인
                default_school_idx = 0
                if st.session_state.selected_school_idx is not None:
                    if st.session_state.selected_school_idx < len(school_names):
                        default_school_idx = st.session_state.selected_school_idx
                
                selected_school_idx = st.selectbox(
                    "학교 선택",
                    range(len(school_names)),
                    index=default_school_idx,
                    format_func=lambda x: school_names[x],
                    key="school_selectbox"
                )
                st.session_state.selected_school_idx = selected_school_idx
                
                if selected_school_idx is not None:
                    selected_school = schools[selected_school_idx]
                    
                    # 학교 기본 정보 표시
                    st.subheader(f"🏫 {selected_school.school_name}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**학교 종류**: {selected_school.school_level}")
                        st.write(f"**주소**: {selected_school.address}")
                        st.write(f"**전화번호**: {selected_school.phone}")
                    
                    with col2:
                        st.write(f"**팩스**: {selected_school.fax}")
                        st.write(f"**홈페이지**: {selected_school.homepage}")
                    
                    st.markdown("---")
                    
                    # 5. 학년/반/기간 선택 및 정보 표시
                    st.subheader("📋 정보 조회 설정")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        grade = st.selectbox(
                            "학년", 
                            ["1", "2", "3", "4", "5", "6"], 
                            index=["1", "2", "3", "4", "5", "6"].index(st.session_state.selected_grade),
                            key="grade_selectbox"
                        )
                        st.session_state.selected_grade = grade
                    
                    with col2:
                        class_num = st.selectbox(
                            "반", 
                            [str(i) for i in range(1, 21)], 
                            index=int(st.session_state.selected_class) - 1,
                            key="class_selectbox"
                        )
                        st.session_state.selected_class = class_num
                    
                    with col3:
                        # 주간 기간 선택 (1년 기간, 오늘 기준)
                        from datetime import datetime, timedelta
                        today = datetime.now()
                        monday = today - timedelta(days=today.weekday())
                        
                        week_options = []
                        # 이전 26주 ~ 다음 26주 (약 1년)
                        for i in range(-26, 27):
                            week_start = monday + timedelta(weeks=i)
                            week_end = week_start + timedelta(days=4)
                            week_options.append({
                                'start': week_start.strftime('%Y%m%d'),
                                'end': week_end.strftime('%Y%m%d'),
                                'label': f"{week_start.strftime('%Y년 %m월 %d일')} ~ {week_end.strftime('%m월 %d일')} ({week_start.strftime('%Y')}년)"
                            })
                        
                        # 오늘을 포함하는 주의 인덱스 (항상 26)
                        today_week_idx = 26
                        
                        # 세션 상태에서 주간 인덱스 가져오기 (없으면 오늘 주간)
                        current_week_idx = st.session_state.selected_week_idx if st.session_state.selected_week_idx is not None else today_week_idx
                        
                        selected_week_idx = st.selectbox(
                            "주간 선택",
                            range(len(week_options)),
                            index=current_week_idx,
                            format_func=lambda x: week_options[x]['label'],
                            key="week_selectbox"
                        )
                        st.session_state.selected_week_idx = selected_week_idx
                    
                    # 선택된 정보가 있으면 즉시 결과 표시
                    if selected_week_idx is not None:
                        selected_week = week_options[selected_week_idx]
                        
                        st.markdown("---")
                        
                        # 결과를 탭으로 구분하여 표시
                        tab1, tab2, tab3, tab4 = st.tabs(["🍽️ 급식 정보", "📚 시간표 정보", "📅 학사일정", "👨‍🏫 내 수업 정보"])
                        
                        with tab1:
                            st.subheader("🍽️ 급식 정보")
                            
                            # 주간 전체 급식 정보 조회
                            all_meals = []
                            from datetime import datetime, timedelta
                            
                            # 주의 시작일부터 5일간 조회 (월~금)
                            start_date = datetime.strptime(selected_week['start'], '%Y%m%d')
                            for i in range(5):
                                current_date = start_date + timedelta(days=i)
                                date_str = current_date.strftime('%Y%m%d')
                                day_name = current_date.strftime('%A')  # 요일
                                
                                daily_meals = DataFetcher.get_meals(selected_school.school_code, date_str, region_code)
                                if daily_meals:
                                    for meal in daily_meals:
                                        meal.date = date_str
                                        meal.day_name = day_name
                                        all_meals.append(meal)
                            
                            if all_meals:
                                # 날짜별로 그룹화하여 표시
                                current_date = None
                                for meal in all_meals:
                                    if meal.date != current_date:
                                        current_date = meal.date
                                        date_obj = datetime.strptime(meal.date, '%Y%m%d')
                                        st.markdown(f"### 📅 {date_obj.strftime('%Y년 %m월 %d일')} ({meal.day_name})")
                                    
                                    with st.container():
                                        st.markdown(f"""
                                        <div style="
                                            border: 1px solid #e0e0e0;
                                            border-radius: 8px;
                                            padding: 16px;
                                            margin: 8px 0;
                                            background-color: #f8f9fa;
                                        ">
                                            <h4 style="margin: 0 0 8px 0; color: #1f2937;">🍽️ {meal.meal_type}</h4>
                                            <p style="margin: 4px 0; color: #374151;">{meal.menu}</p>
                                            {f'<p style="margin: 4px 0; color: #6b7280; font-size: 14px;">📊 영양정보: {meal.nutrition_info}</p>' if meal.nutrition_info else ''}
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.warning("🍽️ 해당 주의 급식 정보가 없습니다.")
                                st.info("💡 방학, 주말, 공휴일에는 급식 정보가 제공되지 않습니다.")
                        
                        with tab2:
                            st.subheader("📚 시간표 정보")
                            
                            # 주간 전체 시간표 정보 조회
                            all_timetables = []
                            
                            # 주의 시작일부터 5일간 조회 (월~금)
                            start_date = datetime.strptime(selected_week['start'], '%Y%m%d')
                            for i in range(5):
                                current_date = start_date + timedelta(days=i)
                                date_str = current_date.strftime('%Y%m%d')
                                day_name = current_date.strftime('%A')  # 요일
                                
                                daily_timetable = DataFetcher.get_timetable(
                                    selected_school.school_code, 
                                    grade, 
                                    class_num, 
                                    date_str,
                                    region_code,
                                    selected_school.school_level
                                )
                                if daily_timetable:
                                    for item in daily_timetable:
                                        item.date = date_str
                                        item.day_name = day_name
                                        all_timetables.append(item)
                            
                            if all_timetables:
                                # 날짜별로 그룹화하여 표시 (급식 정보와 동일한 형태)
                                from collections import defaultdict
                                
                                # 날짜별로 시간표 데이터 그룹화
                                date_timetables = defaultdict(list)
                                for item in all_timetables:
                                    date_timetables[item.date].append(item)
                                
                                # 날짜별로 정렬하여 표시
                                sorted_dates = sorted(date_timetables.keys())
                                for date in sorted_dates:
                                    date_obj = datetime.strptime(date, '%Y%m%d')
                                    day_name = date_obj.strftime('%A')
                                    
                                    st.markdown(f"### 📅 {date_obj.strftime('%Y년 %m월 %d일')} ({day_name})")
                                    
                                    # 해당 날짜의 시간표 데이터
                                    timetable_items = date_timetables[date]
                                    timetable_items.sort(key=lambda x: x.period)
                                    
                                    # 테이블 데이터 준비
                                    table_data = []
                                    for item in timetable_items:
                                        table_data.append({
                                            "교시": f"{item.period}교시",
                                            "과목": item.subject,
                                            "담당교사": item.teacher if item.teacher else "-"
                                        })
                                    
                                    # Streamlit 테이블로 표시
                                    if table_data:
                                        df = pd.DataFrame(table_data)
                                        st.dataframe(
                                            df,
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                "교시": st.column_config.TextColumn("교시", width="medium"),
                                                "과목": st.column_config.TextColumn("과목", width="large"),
                                                "담당교사": st.column_config.TextColumn("담당교사", width="medium")
                                            }
                                        )
                                    else:
                                        st.info("해당 날짜의 시간표 정보가 없습니다.")
                                    
                                    st.markdown("---")
                            else:
                                st.warning("📚 해당 주의 시간표 정보가 없습니다.")
                                st.info("💡 방학, 주말, 공휴일에는 시간표 정보가 제공되지 않습니다.")
                        
                        with tab3:
                            st.subheader("📅 학사일정")
                            
                            # 주간 전체 학사일정 정보 조회
                            all_schedules = []
                            
                            # 주의 시작일부터 5일간 조회 (월~금)
                            start_date = datetime.strptime(selected_week['start'], '%Y%m%d')
                            end_date = start_date + timedelta(days=4)
                            
                            # 학사일정은 주간 단위로 조회
                            from_date_str = start_date.strftime('%Y%m%d')
                            to_date_str = end_date.strftime('%Y%m%d')
                            
                            daily_schedules = DataFetcher.get_school_schedule(
                                selected_school.school_code, 
                                from_date_str, 
                                to_date_str,
                                region_code
                            )
                            
                            if daily_schedules:
                                # 날짜별로 그룹화하여 표시
                                from collections import defaultdict
                                
                                # 날짜별로 학사일정 데이터 그룹화
                                date_schedules = defaultdict(list)
                                for item in daily_schedules:
                                    date_schedules[item.date].append(item)
                                
                                # 날짜별로 정렬하여 표시
                                sorted_dates = sorted(date_schedules.keys())
                                for date in sorted_dates:
                                    date_obj = datetime.strptime(date, '%Y%m%d')
                                    day_name = date_obj.strftime('%A')
                                    
                                    st.markdown(f"### 📅 {date_obj.strftime('%Y년 %m월 %d일')} ({day_name})")
                                    
                                    # 해당 날짜의 학사일정 데이터
                                    schedule_items = date_schedules[date]
                                    
                                    for item in schedule_items:
                                        with st.container():
                                            st.markdown(f"""
                                            <div style="
                                                border: 1px solid #e0e0e0;
                                                border-radius: 8px;
                                                padding: 16px;
                                                margin: 8px 0;
                                                background-color: #f0f8ff;
                                                border-left: 4px solid #1e90ff;
                                            ">
                                                <h4 style="margin: 0 0 8px 0; color: #1f2937;">📅 {item.event_name}</h4>
                                                <p style="margin: 4px 0; color: #374151;">{item.event_type}</p>
                                                {f'<p style="margin: 4px 0; color: #6b7280; font-size: 14px;">📋 전체학년 이벤트: {"예" if item.event_content == "Y" else "아니오"}</p>' if item.event_content else ''}
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    st.markdown("---")
                            else:
                                st.warning("📅 해당 주의 학사일정이 없습니다.")
                                st.info("💡 방학, 주말, 공휴일에는 학사일정이 제공되지 않거나 등록된 일정이 없습니다.")
                        
                        with tab4:
                            st.subheader("👨‍🏫 내 수업 정보")
                            
                            # 수업 검색 조건 입력
                            st.markdown("### 📝 수업 검색 조건")
                            st.info("💡 과목명, 학년, 반을 입력하면 해당 조건에 맞는 시간표 정보를 검색하여 주간 단위로 표시합니다.")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                search_subject = st.text_input("과목명", key="search_subject_input_tab4", placeholder="예: 수학, 국어")
                            with col2:
                                search_grade = st.selectbox("학년", ["전체", "1학년", "2학년", "3학년", "4학년", "5학년", "6학년"], key="search_grade_input_tab4")
                            with col3:
                                search_class = st.selectbox("반", ["전체", "1반", "2반", "3반", "4반", "5반", "6반", "7반", "8반", "9반", "10반"], key="search_class_input_tab4")
                            
                            # 검색 버튼
                            search_clicked = st.button("🔍 수업 검색", key="search_classes_btn_tab4", type="primary")
                            
                            st.markdown("---")
                            
                            # 검색 결과 표시
                            if search_clicked and selected_school:
                                st.markdown("### 📊 내 수업 시간표")
                                
                                # 선택된 주의 날짜 범위 계산 (다른 탭과 동일한 방식 사용)
                                selected_week_idx = st.session_state.get('selected_week_idx', 26)  # 기본값을 26으로 설정
                                
                                # week_options와 동일한 방식으로 주간 계산
                                today = datetime.now(Constants.KOREA_TZ)
                                monday = today - timedelta(days=today.weekday())
                                week_start = monday + timedelta(weeks=selected_week_idx - 26)  # 26을 빼서 올바른 주차 계산
                                
                                # 해당 주의 모든 날짜 (월~금)
                                week_dates = []
                                for i in range(5):  # 월~금
                                    date = week_start + timedelta(days=i)
                                    week_dates.append(date.strftime('%Y%m%d'))
                                
                                # 데이터 검색 및 재구성 시작 메시지
                                with st.spinner("🔍 데이터를 검색 및 재구성중입니다..."):
                                    # 각 날짜별로 시간표 데이터 가져오기
                                    all_timetable_data = []
                                    
                                    # 검색할 학년과 반 목록 결정 (학교급에 따른 학년 범위 제한)
                                    if search_grade == "전체":
                                        if selected_school.school_level in ["중학교", "고등학교"]:
                                            grades_to_search = ["1학년", "2학년", "3학년"]
                                        else:  # 초등학교
                                            grades_to_search = ["1학년", "2학년", "3학년", "4학년", "5학년", "6학년"]
                                    else:
                                        grades_to_search = [search_grade]
                                    
                                    if search_class == "전체":
                                        classes_to_search = ["1반", "2반", "3반", "4반", "5반", "6반", "7반", "8반", "9반", "10반"]
                                    else:
                                        classes_to_search = [search_class]
                                    
                                    # API 호출 실패 추적을 위한 변수
                                    api_failures = {}  # {class_num: failure_count}
                                    
                                    # 모든 조합으로 시간표 데이터 가져오기
                                    for date in week_dates:
                                        for grade in grades_to_search:
                                            for class_num in classes_to_search:
                                                # 연속 3회 실패한 반은 건너뛰기
                                                if class_num in api_failures and api_failures[class_num] >= 3:
                                                    continue
                                                
                                                try:
                                                    # 시간표 데이터 가져오기
                                                    timetable_data = DataFetcher.get_timetable(
                                                        selected_school.school_code,
                                                        grade,
                                                        class_num,
                                                        date,
                                                        region_code,
                                                        selected_school.school_level
                                                    )
                                                    
                                                    # API 호출 성공 시 실패 카운트 초기화
                                                    if class_num in api_failures:
                                                        api_failures[class_num] = 0
                                                    
                                                    # 과목명 필터링 (대소문자 구분 없이, 부분 문자열 매칭)
                                                    if search_subject:
                                                        filtered_data = [item for item in timetable_data if search_subject.lower() in item.subject.lower()]
                                                        # 디버깅: 필터링 결과 로그
                                                        if timetable_data and not filtered_data:
                                                            st.warning(f"⚠️ {date} {grade} {class_num}: '{search_subject}' 과목을 찾을 수 없습니다. (사용 가능한 과목: {', '.join([item.subject for item in timetable_data])})")
                                                    else:
                                                        filtered_data = timetable_data
                                                    
                                                    all_timetable_data.extend(filtered_data)
                                                    
                                                except Exception as e:
                                                    # API 호출 실패 시 카운트 증가
                                                    if class_num not in api_failures:
                                                        api_failures[class_num] = 0
                                                    api_failures[class_num] += 1
                                                    
                                                    # 실패 로그 (디버깅용)
                                                    st.warning(f"⚠️ {grade} {class_num} 시간표 조회 실패 (실패 횟수: {api_failures[class_num]})")
                                
                                # 데이터 검색 및 재구성 완료 메시지
                                st.success("✅ 테이블을 불러오는데 성공했습니다.")
                                
                                if all_timetable_data:
                                    # 중복 제거: 동일한 날짜, 교시, 과목의 데이터는 하나만 유지
                                    unique_data = {}
                                    for item in all_timetable_data:
                                        key = (item.date, item.period, item.subject)
                                        if key not in unique_data:
                                            unique_data[key] = item
                                    
                                    # 날짜별로 데이터 그룹화
                                    date_groups = {}
                                    for item in unique_data.values():
                                        if item.date not in date_groups:
                                            date_groups[item.date] = []
                                        date_groups[item.date].append(item)
                                    
                                    # 날짜별로 정렬하여 표시
                                    for date in sorted(date_groups.keys()):
                                        date_obj = datetime.strptime(date, '%Y%m%d')
                                        day_name = date_obj.strftime('%A')
                                        day_korean = {
                                            'Monday': '월요일',
                                            'Tuesday': '화요일', 
                                            'Wednesday': '수요일',
                                            'Thursday': '목요일',
                                            'Friday': '금요일'
                                        }.get(day_name, day_name)
                                        
                                        # 해당 날짜의 수업들을 교시별로 정렬
                                        day_classes = sorted(date_groups[date], key=lambda x: x.period)
                                        
                                        st.markdown(f"""
                                        <div style="
                                            border: 1px solid #e5e7eb;
                                            border-radius: 8px;
                                            padding: 16px;
                                            margin: 16px 0;
                                            background-color: #f9fafb;
                                        ">
                                            <h3 style="margin: 0 0 12px 0; color: #1f2937; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;">
                                                📅 {date_obj.strftime('%Y년 %m월 %d일')} ({day_korean})
                                            </h3>
                                        """, unsafe_allow_html=True)
                                        
                                        if day_classes:
                                            for item in day_classes:
                                                st.markdown(f"""
                                                <div style="
                                                    border: 1px solid #28a745;
                                                    border-radius: 6px;
                                                    padding: 12px;
                                                    margin: 8px 0;
                                                    background-color: #d4edda;
                                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                                ">
                                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                                        <span style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">
                                                            {item.period}교시
                                                        </span>
                                                        <span style="color: #6b7280; font-size: 14px;">
                                                            {item.teacher} | {item.classroom}
                                                        </span>
                                                    </div>
                                                    <h4 style="margin: 0; color: #1f2937; font-size: 16px;">
                                                        📚 {item.subject}
                                                    </h4>
                                                </div>
                                                """, unsafe_allow_html=True)
                                        else:
                                            st.info("📚 해당 날짜에 수업이 없습니다.")
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)
                                    
                                    # 검색 조건 표시
                                    st.markdown("---")
                                    st.markdown("### 📋 검색 조건")
                                    search_conditions = []
                                    if search_subject:
                                        search_conditions.append(f"과목: {search_subject}")
                                    if search_grade != "전체":
                                        search_conditions.append(f"학년: {search_grade}")
                                    if search_class != "전체":
                                        search_conditions.append(f"반: {search_class}")
                                    
                                    if search_conditions:
                                        st.info(f"🔍 검색 조건: {' | '.join(search_conditions)}")
                                    else:
                                        st.info("🔍 검색 조건: 전체")
                                    
                                    # 디버깅 정보 표시
                                    st.markdown("### 🔍 검색 결과 통계")
                                    st.info(f"📊 총 {len(all_timetable_data)}개의 수업 데이터를 찾았습니다.")
                                    st.info(f"📊 중복 제거 후 {len(unique_data)}개의 고유 수업이 있습니다.")
                                    
                                    # 필터링 전 원본 데이터 통계 (디버깅용)
                                    if all_timetable_data:
                                        all_subjects = list(set([item.subject for item in all_timetable_data]))
                                        st.info(f"📚 필터링 전 모든 과목: {', '.join(all_subjects)}")
                                    
                                    # API 호출 실패 정보 표시
                                    if api_failures:
                                        failed_classes = [f"{class_num} (실패 {count}회)" for class_num, count in api_failures.items() if count >= 3]
                                        if failed_classes:
                                            st.warning(f"⚠️ 연속 3회 이상 실패한 반: {', '.join(failed_classes)}")
                                    
                                    # 검색된 과목 목록 표시
                                    if unique_data:
                                        subjects_found = list(set([item.subject for item in unique_data.values()]))
                                        st.info(f"📚 검색된 과목: {', '.join(subjects_found)}")
                                    
                                    # 검색 조건 상세 정보
                                    st.markdown("### 📋 검색 조건 상세")
                                    st.info(f"🏫 학교: {selected_school.school_name} ({selected_school.school_level})")
                                    st.info(f"📅 검색 주차: {selected_week}")
                                    st.info(f"📅 검색 날짜들: {', '.join(week_dates)}")
                                    st.info(f"🔍 검색 학년: {', '.join(grades_to_search)}")
                                    st.info(f"🔍 검색 반: {', '.join(classes_to_search)}")
                                        
                                else:
                                    st.warning("📚 해당 조건에 맞는 수업이 없습니다.")
                                    st.info("💡 다른 조건으로 검색해보세요.")
                            elif search_clicked:
                                st.warning("🏫 학교를 먼저 선택해주세요.")
                            else:
                                st.info("🔍 위에서 검색 조건을 입력하고 '수업 검색' 버튼을 클릭하세요.")
            else:
                st.warning("해당 지역에서 학교를 찾을 수 없습니다.")
        else:
            st.info("지역을 선택해주세요.")

    @staticmethod
    def show_settings():
        """설정 페이지"""
        st.header("⚙️ 설정")
        
        st.subheader("캐시 설정")
        cache_duration = st.slider("캐시 유지 시간 (분)", 1, 60, 5)
        st.write(f"현재 캐시 유지 시간: {cache_duration}분")
        
        if st.button("캐시 초기화"):
            CacheManager.clear_cache()
            st.success("캐시가 초기화되었습니다.")
        
        st.subheader("API 설정")
        weather_api_key = st.text_input("OpenWeatherMap API 키", type="password")
        if weather_api_key:
            st.success("API 키가 설정되었습니다.")

def main():
    """메인 함수"""
    # UI 설정
    UIComponents.setup_page()
    UIComponents.initialize_session_state()
    
    # 헤더
    st.markdown('<h1 class="main-header">📊 DailyInfo - 데이터 정보 대시보드</h1>', unsafe_allow_html=True)
    
    # 사이드바 및 메뉴 처리
    menu = UIComponents.create_sidebar()
    
    # 메뉴별 처리
    menu_handlers = {
        "🌤️ 날씨 정보": PageHandlers.show_weather_info,
        "📰 뉴스": PageHandlers.show_news,
        "🏫 학교 정보": PageHandlers.show_school_info,
        "⚙️ 설정": PageHandlers.show_settings
    }
    
    handler = menu_handlers.get(menu)
    if handler:
        handler()

if __name__ == "__main__":
    main() 