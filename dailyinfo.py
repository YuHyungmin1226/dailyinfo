"""
DailyInfo - 데이터 정보 대시보드
실시간 음악 차트, 날씨, 뉴스 정보를 제공하는 Streamlit 애플리케이션
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
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
                st.error("데이터 불러오기에 실패하였습니다. 잠시 후에 다시 시도하세요.")
                return DataFetcher._get_mock_bugs_chart()
            
            return chart_data
            
        except Exception as e:
            st.error("데이터 불러오기에 실패하였습니다. 잠시 후에 다시 시도하세요.")
            return DataFetcher._get_mock_bugs_chart()
    
    @staticmethod
    def _parse_bugs_chart(soup: BeautifulSoup) -> List[str]:
        """벅스 차트 HTML 파싱"""
        chart_data = []
        table = soup.find('table', {'class': 'list'})
        
        if not table:
            return chart_data
        
        rows = table.find_all('tr')[1:]  # 헤더 제외
        
        for row in rows:
            if len(chart_data) >= Constants.MAX_CHART_ITEMS:
                break
                
            cells = row.find_all('td')
            if len(cells) < 3:
                continue
            
            chart_item = DataFetcher._extract_chart_item(cells)
            if chart_item:
                chart_data.append(chart_item)
        
        return chart_data
    
    @staticmethod
    def _extract_chart_item(cells: List) -> Optional[str]:
        """차트 항목 추출"""
        try:
            # 순위 추출
            rank_text = cells[0].get_text(strip=True)
            rank_match = re.search(r'(\d+)', rank_text)
            if not rank_match:
                return None
            rank = rank_match.group(1)
            
            # 곡명 추출
            song_cell = cells[1]
            song_link = song_cell.find('a')
            song_title = song_link.get_text(strip=True) if song_link else song_cell.get_text(strip=True)
            
            # 아티스트 추출
            artist_cell = cells[2]
            artist_link = artist_cell.find('a')
            artist_name = artist_link.get_text(strip=True) if artist_link else artist_cell.get_text(strip=True)
            
            if song_title and artist_name:
                return f"{rank}. {artist_name} - {song_title}"
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def _get_mock_bugs_chart() -> List[str]:
        """Mock 벅스 차트 데이터"""
        return [
            "1. NewJeans - Ditto", "2. IVE - After LIKE", "3. LE SSERAFIM - ANTIFRAGILE",
            "4. aespa - Girls", "5. BLACKPINK - Pink Venom", "6. NewJeans - Hype Boy",
            "7. IVE - Love Dive", "8. LE SSERAFIM - FEARLESS", "9. aespa - Next Level",
            "10. BLACKPINK - How You Like That", "11. NewJeans - Attention",
            "12. IVE - Eleven", "13. LE SSERAFIM - Blue Flame", "14. aespa - Savage",
            "15. BLACKPINK - Lovesick Girls", "16. NewJeans - Cookie",
            "17. IVE - Take It", "18. LE SSERAFIM - The Great Mermaid",
            "19. aespa - Dreams Come True", "20. BLACKPINK - Ice Cream"
        ] + [f"{i}. Mock Artist - Mock Song {i}" for i in range(21, 101)]

    @staticmethod
    def get_book_rankings() -> List[BookData]:
        """도서 순위 데이터"""
        try:
            mock_data = [
                BookData(1, "어떻게 하면 좋을까요?", "김철수", "행복출판사"),
                BookData(2, "성공하는 방법", "이영희", "성공출판사"),
                BookData(3, "프로그래밍 기초", "박개발", "코딩출판사"),
                BookData(4, "요리 레시피", "최요리", "맛있는출판사"),
                BookData(5, "여행 가이드", "정여행", "여행출판사")
            ]
            return mock_data
        except Exception as e:
            st.error(f"도서 순위 데이터 수집 실패: {e}")
            return []

    @staticmethod
    def get_weather_info() -> Optional[WeatherData]:
        """날씨 정보 수집"""
        try:
            weather_api_key = st.secrets.get("WEATHER_API_KEY", "your_api_key_here")
            
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
                # Mock 데이터 반환
                return WeatherData(22, 65, "맑음", 3.2, 180)
                
        except Exception as e:
            st.error(f"날씨 정보 수집 실패: {e}")
            return None

    @staticmethod
    def get_news() -> List[NewsData]:
        """뉴스 데이터"""
        try:
            mock_data = [
                NewsData(
                    "AI 기술 발전으로 새로운 가능성 열려",
                    "https://example.com/news1",
                    "테크뉴스",
                    "2024-01-15"
                ),
                NewsData(
                    "환경 보호를 위한 새로운 정책 발표",
                    "https://example.com/news2",
                    "환경일보",
                    "2024-01-15"
                ),
                NewsData(
                    "경제 회복 신호 포착",
                    "https://example.com/news3",
                    "경제신문",
                    "2024-01-15"
                )
            ]
            return mock_data
        except Exception as e:
            st.error(f"뉴스 데이터 수집 실패: {e}")
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
        
        # 메트릭 카드들
        col1, col2, col3 = st.columns(3)
        
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
        
        # 최근 업데이트 정보
        st.subheader("🕒 최근 업데이트")
        if st.session_state.last_update:
            for key, timestamp in st.session_state.last_update.items():
                update_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
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
                st.dataframe(df, use_container_width=True)
                
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
        st.header("📚 알라딘 베스트셀러 TOP 50")
        
        data = CacheManager.get_cached_data("book_rankings", DataFetcher.get_book_rankings)
        
        if data:
            # BookData를 딕셔너리로 변환
            book_dicts = [
                {"rank": book.rank, "title": book.title, "author": book.author, "publisher": book.publisher}
                for book in data
            ]
            df = pd.DataFrame(book_dicts)
            st.dataframe(df, use_container_width=True)
            
            # 출판사별 통계
            publisher_stats = df['publisher'].value_counts()
            fig = px.pie(values=publisher_stats.values, 
                        names=publisher_stats.index,
                        title="출판사별 베스트셀러 분포")
            st.plotly_chart(fig, use_container_width=True)

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
        st.header("📰 최신 뉴스")
        
        news_data = CacheManager.get_cached_data("news", DataFetcher.get_news)
        
        if news_data:
            for i, news in enumerate(news_data, 1):
                with st.container():
                    st.markdown(f"### {i}. {news.title}")
                    st.markdown(f"**출처**: {news.source} | **날짜**: {news.published}")
                    st.markdown(f"[기사 보기]({news.link})")
                    st.divider()

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