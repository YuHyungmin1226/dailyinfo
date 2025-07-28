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
    BUGS_CHART_URL = "https://music.bugs.co.kr/chart/track/realtime/total?wl_ref=M_contents_03_01"
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    ALADIN_BESTSELLER_URL = "https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=NowBest&BranchType=2&CID=0&page={}&cnt=100&SortOrder=1"
    
    # HTTP 헤더
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 서울 좌표
    SEOUL_LAT = 37.5665
    SEOUL_LON = 126.9780
    
    # 한국 시간대
    KOREA_TZ = pytz.timezone('Asia/Seoul')

class ChartRange(Enum):
    """차트 표시 범위"""
    TOP_10 = 10
    TOP_20 = 20
    TOP_50 = 50
    TOP_100 = 100

@dataclass
class WeatherData:
    """날씨 데이터 클래스"""
    temperature: float
    humidity: int
    description: str
    wind_speed: float
    wind_direction: int

@dataclass
class NewsData:
    """뉴스 데이터 클래스"""
    title: str
    link: str
    source: str
    published: str

@dataclass
class BookData:
    """도서 데이터 클래스"""
    rank: int
    title: str
    author: str
    publisher: str

class DataFetcher:
    """데이터 수집을 위한 클래스"""
    
    @staticmethod
    def get_bugs_chart() -> List[str]:
        """벅스 차트 데이터 크롤링"""
        try:
            response = requests.get(
                Constants.BUGS_CHART_URL, 
                headers=Constants.DEFAULT_HEADERS, 
                timeout=Constants.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            chart_data = DataFetcher._parse_bugs_chart(soup)
            
            if not chart_data:
                st.error("벅스 차트 데이터를 파싱할 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")
                return []
            
            return chart_data
            
        except requests.exceptions.RequestException as e:
            st.error(f"벅스 차트 웹사이트에 접속할 수 없습니다: {e}")
            return []
        except Exception as e:
            st.error(f"벅스 차트 데이터 수집 중 오류가 발생했습니다: {e}")
            return []
    
    @staticmethod
    def _parse_bugs_chart(soup: BeautifulSoup) -> List[str]:
        """벅스 차트 HTML 파싱"""
        chart_data = []
        
        # 차트 테이블 찾기
        table = soup.find('table', class_='list')
        
        if not table:
            st.warning("차트 테이블을 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")
            return chart_data
        
        rows = table.find_all('tr')[1:]  # 헤더 제외
        
        for row in rows:
            if len(chart_data) >= Constants.MAX_CHART_ITEMS:
                break
                
            cells = row.find_all('td')
            if len(cells) < 6:  # 최소 6개 셀이 필요
                continue
            
            chart_item = DataFetcher._extract_chart_item(cells, row)
            if chart_item:
                chart_data.append(chart_item)
        
        return chart_data
    
    @staticmethod
    def _extract_chart_item(cells: List, row) -> Optional[str]:
        """차트 항목 추출"""
        try:
            # 순위 추출 (ranking div에서)
            rank = "N/A"
            ranking_div = row.find('div', class_='ranking')
            if ranking_div:
                strong_tag = ranking_div.find('strong')
                if strong_tag:
                    rank = strong_tag.get_text(strip=True)
            
            # 곡명 추출 (앨범 셀에서 - 6번째 셀)
            song_title = cells[5].get_text(strip=True) if len(cells) > 5 else "N/A"
            
            # 아티스트 추출 (아티스트 링크에서)
            artist_name = "N/A"
            artist_link = row.find('a', href=re.compile(r'/artist/'))
            if artist_link:
                artist_name = artist_link.get_text(strip=True)
            
            if song_title and artist_name and song_title != "N/A" and artist_name != "N/A":
                return f"{rank}. {artist_name} - {song_title}"
            
        except Exception:
            pass
        
        return None
    


    @staticmethod
    def get_book_rankings() -> List[BookData]:
        """알라딘 실시간 베스트셀러 데이터 (100개)"""
        try:
            book_data = []
            
            # 두 페이지에서 각각 50개씩 가져오기
            for page in [1, 2]:
                url = Constants.ALADIN_BESTSELLER_URL.format(page)
                response = requests.get(url, headers=Constants.DEFAULT_HEADERS, timeout=Constants.REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                page_data = DataFetcher._parse_aladin_chart(soup, page)
                
                # 두 번째 페이지 데이터의 순위를 51-100으로 조정
                if page == 2:
                    for book in page_data:
                        book.rank = book.rank + 50
                
                book_data.extend(page_data)
            
            return book_data
            
        except requests.exceptions.RequestException as e:
            st.error(f"알라딘 웹사이트에 접속할 수 없습니다: {e}")
            return []
        except Exception as e:
            st.error(f"도서 순위 데이터 수집 중 오류가 발생했습니다: {e}")
            return []
    
    @staticmethod
    def _parse_aladin_chart(soup: BeautifulSoup, page: int = 1) -> List[BookData]:
        """알라딘 베스트셀러 HTML 파싱"""
        book_data = []
        
        try:
            # 1. ss_book_list 클래스를 가진 요소들에서 책 정보 추출
            book_lists = soup.find_all('div', class_='ss_book_list')
            
            if book_lists:
                for i, book_list in enumerate(book_lists[:50]):  # 최대 50개
                    book_list_text = book_list.get_text(strip=True)
                    
                    # 순위와 제목 패턴 찾기
                    # 패턴 1: 숫자 + 제목 (더 정확한 패턴)
                    pattern1 = r'(\d+)\.\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*\[|\s*$)'
                    matches1 = re.findall(pattern1, book_list_text)
                    
                    # 패턴 2: [국내도서] + 제목
                    pattern2 = r'\[국내도서\]([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외|\s*\[|\s*$)'
                    matches2 = re.findall(pattern2, book_list_text)
                    
                    if matches1:
                        for match in matches1:
                            rank = int(match[0])
                            title = match[1].strip()
                            
                            if len(title) > 3:  # 유효한 제목인지 확인
                                # 저자와 출판사 정보 추출 시도
                                author = "저자 정보 없음"
                                publisher = "출판사 정보 없음"
                                
                                # 저자 패턴 찾기
                                author_pattern = r'([가-힣\s]+?)\s*지음|([가-힣\s]+?)\s*저|([가-힣\s]+?)\s*편집'
                                author_matches = re.findall(author_pattern, book_list_text)
                                if author_matches:
                                    for author_match in author_matches:
                                        if any(author_match):
                                            author = next(a for a in author_match if a).strip()
                                            break
                                
                                # 출판사 패턴 찾기 (저자 다음에 나오는 경우)
                                publisher_pattern = r'([가-힣\s]+?)\s*\|\s*([가-힣\s]+?)\s*\|'
                                publisher_matches = re.findall(publisher_pattern, book_list_text)
                                if publisher_matches:
                                    publisher = publisher_matches[0][1].strip()
                                
                                # 중복 제거
                                existing_titles = [book.title for book in book_data]
                                if title not in existing_titles:
                                    book_data.append(BookData(rank, title, author, publisher))
                                break  # 첫 번째 매치만 사용
                
                elif matches2:
                    # 패턴2로 찾은 경우 순위는 인덱스 기반으로 설정
                    for i, match in enumerate(matches2):
                        rank = i + 1
                        title = match.strip()
                        
                        if len(title) > 3:  # 유효한 제목인지 확인
                            # 저자와 출판사 정보 추출 시도
                            author = "저자 정보 없음"
                            publisher = "출판사 정보 없음"
                            
                            # 저자 패턴 찾기
                            author_pattern = r'([가-힣\s]+?)\s*지음|([가-힣\s]+?)\s*저|([가-힣\s]+?)\s*편집'
                            author_matches = re.findall(author_pattern, book_list_text)
                            if author_matches:
                                for author_match in author_matches:
                                    if any(author_match):
                                        author = next(a for a in author_match if a).strip()
                                        break
                            
                            # 출판사 패턴 찾기 (저자 다음에 나오는 경우)
                            publisher_pattern = r'([가-힣\s]+?)\s*\|\s*([가-힣\s]+?)\s*\|'
                            publisher_matches = re.findall(publisher_pattern, book_list_text)
                            if publisher_matches:
                                publisher = publisher_matches[0][1].strip()
                            
                            # 중복 제거
                            existing_titles = [book.title for book in book_data]
                            if title not in existing_titles:
                                book_data.append(BookData(rank, title, author, publisher))
                            break  # 첫 번째 매치만 사용
            
            # 2. 책 상품 링크에서 제목 추출
            if not book_data:
                book_links = soup.find_all('a', href=lambda x: x and 'wproduct.aspx' in x)
                
                for i, link in enumerate(book_links[:50]):
                    link_text = link.get_text(strip=True)
                    if len(link_text) > 5 and not link_text.startswith('http'):
                        # 순위는 인덱스 기반으로 설정
                        rank = i + 1
                        title = link_text
                        
                        # 저자와 출판사는 기본값으로 설정
                        author = "저자 정보 없음"
                        publisher = "출판사 정보 없음"
                        
                        # 중복 제거
                        existing_titles = [book.title for book in book_data]
                        if title not in existing_titles:
                            book_data.append(BookData(rank, title, author, publisher))
            
            # 3. 전체 텍스트에서 패턴 매칭으로 데이터 추출 시도
            if not book_data:
                all_text = soup.get_text()
                
                # 알라딘 베스트셀러 패턴으로 책 정보 추출 시도
                patterns = [
                    r'(\d+)\.\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
                    r'(\d+)\s*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
                    r'순위\s*(\d+)[^가-힣]*([가-힣\s]+?)(?:\s+지음|\s+저|\s+편집|\s+글|\s+그림|\s+외)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, all_text)
                    if matches:
                        for match in matches[:50]:  # 최대 50개
                            rank = int(match[0])
                            title = match[1].strip()
                            
                            if len(title) > 3:  # 유효한 제목인지 확인
                                # 저자와 출판사는 기본값으로 설정
                                author = "저자 정보 없음"
                                publisher = "출판사 정보 없음"
                                
                                # 중복 제거
                                existing_titles = [book.title for book in book_data]
                                if title not in existing_titles:
                                    book_data.append(BookData(rank, title, author, publisher))
                        break
            
            # 순위별로 정렬
            book_data.sort(key=lambda x: x.rank)
            
            # 성공적으로 데이터를 파싱한 경우 세션에 저장
            if book_data:
                st.session_state.last_successful_book_data = book_data.copy()
                st.session_state.last_successful_book_update = time.time()
                return book_data
            
            # 파싱 실패 시 빈 리스트 반환
            return []
            
        except Exception as e:
            st.error(f"알라딘 차트 파싱 중 오류: {e}")
            return []

    @staticmethod
    def get_weather_info() -> Optional[WeatherData]:
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
            
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': Constants.SEOUL_LAT,
                'lon': Constants.SEOUL_LON,
                'appid': weather_api_key,
                'units': 'metric',
                'lang': 'kr'
            }
            
            response = requests.get(url, params=params, timeout=Constants.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                return WeatherData(
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
                            
                            published = korea_time.strftime("%Y-%m-%d %H:%M")
                        except:
                            published = "최근"
                    
                    # 중복 제거를 위해 이미 추가된 제목인지 확인
                    existing_titles = [news.title for news in news_data]
                    if title not in existing_titles:
                        news_data.append(NewsData(title, link, source, published))
            
            return news_data[:20]  # 상위 20개 뉴스만 반환
            
        except requests.exceptions.RequestException as e:
            st.error(f"Google 뉴스 RSS 피드에 접속할 수 없습니다: {e}")
            return []
        except Exception as e:
            st.error(f"뉴스 데이터를 파싱할 수 없습니다: {e}")
            return []

class DataProcessor:
    """데이터 처리 및 시각화 클래스"""
    
    @staticmethod
    def create_chart_dataframe(data: List[str]) -> pd.DataFrame:
        """차트 데이터를 DataFrame으로 변환"""
        df_data = []
        
        for item in data:
            chart_item = DataProcessor._parse_chart_item(item)
            if chart_item:
                df_data.append(chart_item)
        
        return pd.DataFrame(df_data)
    
    @staticmethod
    def _parse_chart_item(item: str) -> Optional[Dict]:
        """차트 항목 파싱"""
        try:
            if " - " not in item:
                return None
                
            rank, song_info = item.split(". ", 1)
            if " - " not in song_info:
                return None
                
            artist, title = song_info.split(" - ", 1)
            
            return {
                "순위": int(rank),
                "아티스트": artist,
                "곡명": title
            }
        except Exception:
            return None

    @staticmethod
    def create_weather_display(weather_data: WeatherData) -> None:
        """날씨 정보 표시"""
        if not weather_data:
            return
            
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("기온", f"{weather_data.temperature}°C")
        with col2:
            st.metric("습도", f"{weather_data.humidity}%")
        with col3:
            st.metric("바람", f"{weather_data.wind_speed} m/s")
        with col4:
            st.metric("날씨", weather_data.description)

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
        if 'last_successful_book_data' not in st.session_state:
            st.session_state.last_successful_book_data = []
        if 'last_successful_book_update' not in st.session_state:
            st.session_state.last_successful_book_update = None
    
    @staticmethod
    def create_sidebar() -> str:
        """사이드바 생성"""
        st.sidebar.title("📋 메뉴")
        menu = st.sidebar.selectbox(
            "보고 싶은 정보를 선택하세요",
            [
                "🏠 대시보드 개요",
                "🎵 벅스 일간 차트", 
                "📚 도서 순위",
                "🌤️ 날씨 정보",
                "📰 뉴스",
                "⚙️ 설정"
            ]
        )
        return menu

class PageHandlers:
    """페이지 핸들러 클래스"""
    
    @staticmethod
    def show_dashboard_overview():
        """대시보드 개요 페이지"""
        st.header("📊 대시보드 개요")
        st.caption("🕒 모든 시간은 한국 시간(UTC+9) 기준으로 표시됩니다.")
        
        # 메트릭 카드들
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🎵 음악 차트</h3>
                <p>벅스 실시간 차트 TOP 100</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>📚 도서 정보</h3>
                <p>베스트셀러 순위</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🌤️ 날씨 정보</h3>
                <p>서울 실시간 날씨</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>📰 뉴스 정보</h3>
                <p>Google 뉴스 실시간 헤드라인</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 최근 업데이트 정보
        st.subheader("🕒 최근 업데이트 (한국 시간)")
        if st.session_state.last_update:
            for key, timestamp in st.session_state.last_update.items():
                # UTC 타임스탬프를 한국 시간으로 변환
                utc_time = datetime.utcfromtimestamp(timestamp)
                utc_tz = pytz.UTC
                utc_time = utc_tz.localize(utc_time)
                korea_time = utc_time.astimezone(Constants.KOREA_TZ)
                update_time = korea_time.strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**{key}**: {update_time}")

    @staticmethod
    def show_bugs_chart():
        """벅스 차트 페이지"""
        st.header("🎵 벅스 일간 차트 TOP 100")
        
        # 데이터 출처 정보
        st.info("📡 실시간 벅스 차트 데이터를 크롤링하여 제공합니다.")
        
        data = CacheManager.get_cached_data("bugs_chart", DataFetcher.get_bugs_chart)
        
        if data:
            # 표시할 순위 범위 선택
            col1, col2 = st.columns([1, 3])
            with col1:
                display_range = st.selectbox(
                    "표시할 순위 범위",
                    ["TOP 10", "TOP 20", "TOP 50", "TOP 100"],
                    index=0
                )
            
            # 선택된 범위에 따라 데이터 필터링
            range_map = {f"TOP {v.value}": v.value for v in ChartRange}
            display_count = range_map[display_range]
            filtered_data = data[:display_count]
            
            # 데이터프레임으로 변환하여 표시
            df = DataProcessor.create_chart_dataframe(filtered_data)
            
            if not df.empty:
                # 데이터 테이블 표시
                st.subheader(f"📋 {display_range} 차트")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # 차트 시각화
                st.subheader("📊 차트 시각화")
                fig = px.bar(df, x="곡명", y="순위", 
                            title=f"벅스 차트 {display_range}",
                            color="아티스트",
                            height=600)
                fig.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 아티스트별 통계
                st.subheader("🎤 아티스트별 통계")
                artist_stats = df['아티스트'].value_counts()
                fig_pie = px.pie(
                    values=artist_stats.values, 
                    names=artist_stats.index,
                    title="아티스트별 TOP 100 진입 곡 수"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("데이터를 표시할 수 없습니다.")

    @staticmethod
    def show_book_rankings():
        """도서 순위 페이지"""
        st.header("📚 알라딘 베스트셀러 TOP 100")
        
        # 데이터 출처 정보
        st.info("📡 알라딘 베스트셀러 데이터를 실시간으로 크롤링하여 제공합니다.")
        
        data = CacheManager.get_cached_data("book_rankings", DataFetcher.get_book_rankings)
        
        # 실시간 데이터가 없고 최근 성공한 데이터가 있는 경우
        if not data and st.session_state.last_successful_book_data:
            st.warning("⚠️ 실시간 데이터를 가져올 수 없어 최근에 성공한 데이터를 표시합니다.")
            
            # 최근 성공한 데이터의 업데이트 시간 표시
            if st.session_state.last_successful_book_update:
                utc_time = datetime.utcfromtimestamp(st.session_state.last_successful_book_update)
                utc_tz = pytz.UTC
                utc_time = utc_tz.localize(utc_time)
                korea_time = utc_time.astimezone(Constants.KOREA_TZ)
                update_time = korea_time.strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"📅 마지막 성공한 데이터 업데이트: {update_time} (한국 시간)")
            
            data = st.session_state.last_successful_book_data
        
        if data:
            # 표시할 순위 범위 선택
            col1, col2 = st.columns([1, 3])
            with col1:
                display_range = st.selectbox(
                    "표시할 순위 범위",
                    ["TOP 10", "TOP 20", "TOP 50", "TOP 100"],
                    index=0
                )
            
            # 선택된 범위에 따라 데이터 필터링
            range_map = {f"TOP {v.value}": v.value for v in ChartRange}
            display_count = range_map[display_range]
            filtered_data = data[:display_count]
            
            # BookData를 딕셔너리로 변환
            book_dicts = [
                {"rank": book.rank, "title": book.title, "author": book.author, "publisher": book.publisher}
                for book in filtered_data
            ]
            df = pd.DataFrame(book_dicts)
            
            if not df.empty:
                # 데이터 테이블 표시
                st.subheader(f"📋 {display_range} 베스트셀러")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # 차트 시각화
                st.subheader("📊 차트 시각화")
                fig = px.bar(df, x="title", y="rank", 
                            title=f"알라딘 베스트셀러 {display_range}",
                            color="publisher",
                            height=600)
                fig.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 출판사별 통계
                st.subheader("🏢 출판사별 통계")
                publisher_stats = df['publisher'].value_counts()
                fig_pie = px.pie(
                    values=publisher_stats.values, 
                    names=publisher_stats.index,
                    title=f"출판사별 {display_range} 베스트셀러 분포"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # 저자별 통계
                st.subheader("✍️ 저자별 통계")
                author_stats = df['author'].value_counts()
                fig_author = px.bar(
                    x=author_stats.index,
                    y=author_stats.values,
                    title=f"저자별 {display_range} 베스트셀러 수",
                    labels={'x': '저자', 'y': '베스트셀러 수'}
                )
                fig_author.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_author, use_container_width=True)
            else:
                st.write("데이터를 표시할 수 없습니다.")

    @staticmethod
    def show_weather_info():
        """날씨 정보 페이지"""
        st.header("🌤️ 서울 날씨 정보")
        
        weather_data = CacheManager.get_cached_data("weather_info", DataFetcher.get_weather_info)
        
        if weather_data:
            DataProcessor.create_weather_display(weather_data)
            
            # 날씨 설명
            st.subheader("📝 날씨 상세 정보")
            st.write(f"현재 서울의 날씨는 **{weather_data.description}**입니다.")
            st.write(f"기온: {weather_data.temperature}°C, 습도: {weather_data.humidity}%")
            st.write(f"바람: {weather_data.wind_speed} m/s")

    @staticmethod
    def show_news():
        """뉴스 페이지"""
        st.header("📰 Google 뉴스 실시간 헤드라인")
        st.caption("🕒 모든 시간은 한국 시간(UTC+9) 기준으로 표시됩니다.")
        
        # 데이터 출처 정보
        st.info("📡 Google 뉴스 RSS 피드에서 실시간으로 최신 뉴스를 가져옵니다.")
        
        news_data = CacheManager.get_cached_data("news", DataFetcher.get_news)
        
        if news_data:
            # 표시할 뉴스 개수 선택
            col1, col2 = st.columns([1, 3])
            with col1:
                display_count = st.selectbox(
                    "표시할 뉴스 개수",
                    ["5개", "10개", "15개", "20개"],
                    index=1
                )
            
            # 선택된 개수에 따라 데이터 필터링
            count_map = {"5개": 5, "10개": 10, "15개": 15, "20개": 20}
            display_num = count_map[display_count]
            filtered_news = news_data[:display_num]
            
            # 뉴스 목록 표시
            st.subheader(f"📋 최신 뉴스 {display_count}")
            
            for i, news in enumerate(filtered_news, 1):
                with st.container():
                    # 뉴스 카드 스타일
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 16px;
                        margin: 8px 0;
                        background-color: #f8f9fa;
                    ">
                        <h4 style="margin: 0 0 8px 0; color: #1f2937;">{i}. {news.title}</h4>
                        <p style="margin: 4px 0; color: #6b7280; font-size: 14px;">
                            📰 <strong>{news.source}</strong> | 📅 {news.published}
                        </p>
                        <a href="{news.link}" target="_blank" style="
                            color: #3b82f6;
                            text-decoration: none;
                            font-weight: 500;
                        ">🔗 기사 보기</a>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 뉴스 통계
            st.subheader("📊 뉴스 통계")
            
            # 출처별 뉴스 수
            source_stats = {}
            for news in filtered_news:
                source = news.source
                source_stats[source] = source_stats.get(source, 0) + 1
            
            if source_stats:
                fig = px.pie(
                    values=list(source_stats.values()),
                    names=list(source_stats.keys()),
                    title=f"출처별 {display_count} 뉴스 분포"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 출처별 뉴스 수 테이블
                st.subheader("📈 출처별 뉴스 수")
                source_df = pd.DataFrame([
                    {"출처": source, "뉴스 수": count}
                    for source, count in source_stats.items()
                ])
                st.dataframe(source_df, use_container_width=True, hide_index=True)
        else:
            st.warning("뉴스 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")

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
        "🏠 대시보드 개요": PageHandlers.show_dashboard_overview,
        "🎵 벅스 일간 차트": PageHandlers.show_bugs_chart,
        "📚 도서 순위": PageHandlers.show_book_rankings,
        "🌤️ 날씨 정보": PageHandlers.show_weather_info,
        "📰 뉴스": PageHandlers.show_news,
        "⚙️ 설정": PageHandlers.show_settings
    }
    
    handler = menu_handlers.get(menu)
    if handler:
        handler()

if __name__ == "__main__":
    main() 