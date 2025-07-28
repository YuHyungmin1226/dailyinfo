import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
from typing import List, Dict, Optional
import asyncio
import aiohttp

# 페이지 설정
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

# 세션 상태 초기화
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = {}

# 설정
CACHE_DURATION = 300  # 5분 캐시
WEATHER_API_KEY = st.secrets.get("WEATHER_API_KEY", "your_api_key_here")

class DataFetcher:
    """데이터 수집을 위한 클래스"""
    
    @staticmethod
    def get_bugs_chart() -> List[str]:
        """벅스 차트 데이터 (Mock) - 100위까지"""
        try:
            mock_data = [
                "1. NewJeans - Ditto",
                "2. IVE - After LIKE",
                "3. LE SSERAFIM - ANTIFRAGILE",
                "4. aespa - Girls",
                "5. BLACKPINK - Pink Venom",
                "6. NewJeans - Hype Boy",
                "7. IVE - Love Dive",
                "8. LE SSERAFIM - FEARLESS",
                "9. aespa - Next Level",
                "10. BLACKPINK - How You Like That",
                "11. NewJeans - Attention",
                "12. IVE - Eleven",
                "13. LE SSERAFIM - Blue Flame",
                "14. aespa - Savage",
                "15. BLACKPINK - Lovesick Girls",
                "16. NewJeans - Cookie",
                "17. IVE - Take It",
                "18. LE SSERAFIM - The Great Mermaid",
                "19. aespa - Dreams Come True",
                "20. BLACKPINK - Ice Cream",
                "21. Red Velvet - Feel My Rhythm",
                "22. TWICE - Talk that Talk",
                "23. ITZY - Sneakers",
                "24. STAYC - Beautiful Monster",
                "25. (G)I-DLE - Nxde",
                "26. Red Velvet - Birthday",
                "27. TWICE - Set Me Free",
                "28. ITZY - Boys Like You",
                "29. STAYC - Teddy Bear",
                "30. (G)I-DLE - Queencard",
                "31. Red Velvet - Psycho",
                "32. TWICE - Moonlight Sunrise",
                "33. ITZY - Cheshire",
                "34. STAYC - Poppy",
                "35. (G)I-DLE - My Bag",
                "36. Red Velvet - FMR",
                "37. TWICE - The Feels",
                "38. ITZY - Voltage",
                "39. STAYC - Young Luv",
                "40. (G)I-DLE - Tomboy",
                "41. Red Velvet - Queendom",
                "42. TWICE - Scientist",
                "43. ITZY - Loco",
                "44. STAYC - Stereotype",
                "45. (G)I-DLE - Hwaa",
                "46. Red Velvet - Russian Roulette",
                "47. TWICE - Alcohol-Free",
                "48. ITZY - Mafia In The Morning",
                "49. STAYC - ASAP",
                "50. (G)I-DLE - Dumdi Dumdi",
                "51. Red Velvet - Bad Boy",
                "52. TWICE - More & More",
                "53. ITZY - Wannabe",
                "54. STAYC - So Bad",
                "55. (G)I-DLE - Oh my god",
                "56. Red Velvet - Peek-A-Boo",
                "57. TWICE - Fancy",
                "58. ITZY - Dalla Dalla",
                "59. STAYC - Like This",
                "60. (G)I-DLE - Lion",
                "61. Red Velvet - Red Flavor",
                "62. TWICE - TT",
                "63. ITZY - Icy",
                "64. STAYC - Run2U",
                "65. (G)I-DLE - Uh-Oh",
                "66. Red Velvet - Power Up",
                "67. TWICE - What is Love?",
                "68. ITZY - Not Shy",
                "69. STAYC - Complex",
                "70. (G)I-DLE - Senorita",
                "71. Red Velvet - Rookie",
                "72. TWICE - Likey",
                "73. ITZY - In the morning",
                "74. STAYC - Same Same",
                "75. (G)I-DLE - Latata",
                "76. Red Velvet - Dumb Dumb",
                "77. TWICE - Signal",
                "78. ITZY - MITM",
                "79. STAYC - So What",
                "80. (G)I-DLE - Hann",
                "81. Red Velvet - Ice Cream Cake",
                "82. TWICE - Knock Knock",
                "83. ITZY - Swipe",
                "84. STAYC - I'll Be There",
                "85. (G)I-DLE - Blow Your Mind",
                "86. Red Velvet - Automatic",
                "87. TWICE - Heart Shaker",
                "88. ITZY - Twenty",
                "89. STAYC - Love Fool",
                "90. (G)I-DLE - Give Me Your",
                "91. Red Velvet - Be Natural",
                "92. TWICE - Like Ooh-Ahh",
                "93. ITZY - Cherry",
                "94. STAYC - Butterfly",
                "95. (G)I-DLE - Maze",
                "96. Red Velvet - Happiness",
                "97. TWICE - Cheer Up",
                "98. ITZY - Want It?",
                "99. STAYC - So Bad",
                "100. (G)I-DLE - Dollar"
            ]
            return mock_data
        except Exception as e:
            st.error(f"벅스 차트 데이터 수집 실패: {e}")
            return []

    @staticmethod
    def get_book_rankings() -> List[Dict]:
        """도서 순위 데이터 (Mock)"""
        try:
            mock_data = [
                {"rank": 1, "title": "어떻게 하면 좋을까요?", "author": "김철수", "publisher": "행복출판사"},
                {"rank": 2, "title": "성공하는 방법", "author": "이영희", "publisher": "성공출판사"},
                {"rank": 3, "title": "프로그래밍 기초", "author": "박개발", "publisher": "코딩출판사"},
                {"rank": 4, "title": "요리 레시피", "author": "최요리", "publisher": "맛있는출판사"},
                {"rank": 5, "title": "여행 가이드", "author": "정여행", "publisher": "여행출판사"}
            ]
            return mock_data
        except Exception as e:
            st.error(f"도서 순위 데이터 수집 실패: {e}")
            return []

    @staticmethod
    def get_weather_info() -> Dict:
        """날씨 정보 (OpenWeatherMap API 사용)"""
        try:
            # 서울 좌표
            lat, lon = 37.5665, 126.9780
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "wind_direction": data["wind"]["deg"]
                }
            else:
                # Mock 데이터 반환
                return {
                    "temperature": 22,
                    "humidity": 65,
                    "description": "맑음",
                    "wind_speed": 3.2,
                    "wind_direction": 180
                }
        except Exception as e:
            st.error(f"날씨 정보 수집 실패: {e}")
            return {}

    @staticmethod
    def get_news() -> List[Dict]:
        """뉴스 데이터 (Mock)"""
        try:
            mock_data = [
                {
                    "title": "AI 기술 발전으로 새로운 가능성 열려",
                    "link": "https://example.com/news1",
                    "source": "테크뉴스",
                    "published": "2024-01-15"
                },
                {
                    "title": "환경 보호를 위한 새로운 정책 발표",
                    "link": "https://example.com/news2",
                    "source": "환경일보",
                    "published": "2024-01-15"
                },
                {
                    "title": "경제 회복 신호 포착",
                    "link": "https://example.com/news3",
                    "source": "경제신문",
                    "published": "2024-01-15"
                }
            ]
            return mock_data
        except Exception as e:
            st.error(f"뉴스 데이터 수집 실패: {e}")
            return []

class DataProcessor:
    """데이터 처리 및 시각화 클래스"""
    
    @staticmethod
    def create_chart_dataframe(data: List[str], title: str) -> pd.DataFrame:
        """차트 데이터를 DataFrame으로 변환"""
        df_data = []
        for i, item in enumerate(data, 1):
            if " - " in item:
                rank, song_info = item.split(". ", 1)
                if " - " in song_info:
                    artist, title = song_info.split(" - ", 1)
                    df_data.append({
                        "순위": int(rank),
                        "아티스트": artist,
                        "곡명": title
                    })
        return pd.DataFrame(df_data)

    @staticmethod
    def create_weather_display(weather_data: Dict) -> None:
        """날씨 정보 표시"""
        if not weather_data:
            return
            
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("기온", f"{weather_data.get('temperature', 0)}°C")
        with col2:
            st.metric("습도", f"{weather_data.get('humidity', 0)}%")
        with col3:
            st.metric("바람", f"{weather_data.get('wind_speed', 0)} m/s")
        with col4:
            st.metric("날씨", weather_data.get('description', '알 수 없음'))

def get_cached_data(key: str, fetcher_func, *args):
    """캐시된 데이터 반환 또는 새로 수집"""
    current_time = time.time()
    
    # 캐시 확인
    if (key in st.session_state.data_cache and 
        key in st.session_state.last_update and
        current_time - st.session_state.last_update[key] < CACHE_DURATION):
        return st.session_state.data_cache[key]
    
    # 새 데이터 수집
    with st.spinner(f"{key} 데이터를 수집하는 중..."):
        data = fetcher_func(*args)
        st.session_state.data_cache[key] = data
        st.session_state.last_update[key] = current_time
    
    return data

def main():
    # 헤더
    st.markdown('<h1 class="main-header">📊 DailyInfo - 데이터 정보 대시보드</h1>', unsafe_allow_html=True)
    
    # 사이드바
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
    
    # 메뉴별 처리
    if menu == "🏠 대시보드 개요":
        show_dashboard_overview()
    elif menu == "🎵 벅스 일간 차트":
        show_bugs_chart()
    elif menu == "📚 도서 순위":
        show_book_rankings()
    elif menu == "🌤️ 날씨 정보":
        show_weather_info()
    elif menu == "📰 뉴스":
        show_news()
    elif menu == "⚙️ 설정":
        show_settings()

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

def show_bugs_chart():
    """벅스 차트 페이지"""
    st.header("🎵 벅스 일간 차트 TOP 100")
    
    data = get_cached_data("bugs_chart", DataFetcher.get_bugs_chart)
    
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
        range_map = {"TOP 10": 10, "TOP 20": 20, "TOP 50": 50, "TOP 100": 100}
        display_count = range_map[display_range]
        filtered_data = data[:display_count]
        
        # 데이터프레임으로 변환하여 표시
        df = DataProcessor.create_chart_dataframe(filtered_data, "벅스 차트")
        
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

def show_book_rankings():
    """도서 순위 페이지"""
    st.header("📚 알라딘 베스트셀러 TOP 50")
    
    data = get_cached_data("book_rankings", DataFetcher.get_book_rankings)
    
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # 출판사별 통계
        publisher_stats = df['publisher'].value_counts()
        fig = px.pie(values=publisher_stats.values, 
                    names=publisher_stats.index,
                    title="출판사별 베스트셀러 분포")
        st.plotly_chart(fig, use_container_width=True)

def show_weather_info():
    """날씨 정보 페이지"""
    st.header("🌤️ 서울 날씨 정보")
    
    weather_data = get_cached_data("weather_info", DataFetcher.get_weather_info)
    
    if weather_data:
        DataProcessor.create_weather_display(weather_data)
        
        # 날씨 설명
        st.subheader("📝 날씨 상세 정보")
        st.write(f"현재 서울의 날씨는 **{weather_data.get('description', '알 수 없음')}**입니다.")
        st.write(f"기온: {weather_data.get('temperature', 0)}°C, 습도: {weather_data.get('humidity', 0)}%")
        st.write(f"바람: {weather_data.get('wind_speed', 0)} m/s")

def show_news():
    """뉴스 페이지"""
    st.header("📰 최신 뉴스")
    
    news_data = get_cached_data("news", DataFetcher.get_news)
    
    if news_data:
        for i, news in enumerate(news_data, 1):
            with st.container():
                st.markdown(f"### {i}. {news['title']}")
                st.markdown(f"**출처**: {news['source']} | **날짜**: {news['published']}")
                st.markdown(f"[기사 보기]({news['link']})")
                st.divider()

def show_settings():
    """설정 페이지"""
    st.header("⚙️ 설정")
    
    st.subheader("캐시 설정")
    cache_duration = st.slider("캐시 유지 시간 (분)", 1, 60, 5)
    st.write(f"현재 캐시 유지 시간: {cache_duration}분")
    
    if st.button("캐시 초기화"):
        st.session_state.data_cache.clear()
        st.session_state.last_update.clear()
        st.success("캐시가 초기화되었습니다.")
    
    st.subheader("API 설정")
    weather_api_key = st.text_input("OpenWeatherMap API 키", type="password")
    if weather_api_key:
        st.success("API 키가 설정되었습니다.")

if __name__ == "__main__":
    main() 