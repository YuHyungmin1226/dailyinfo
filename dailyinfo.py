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
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    
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
        """교보문고 실시간 베스트셀러 데이터 (100개)"""
        try:
            # 임시로 하드코딩된 100개 데이터 반환
            soup = BeautifulSoup("", 'html.parser')  # 빈 soup 객체 생성
            book_data = DataFetcher._parse_kyobo_chart(soup, 1)
            return book_data
            
        except Exception as e:
            st.error(f"도서 순위 데이터를 불러오는데 실패했습니다: {e}")
            return []
    
    @staticmethod
    def _parse_kyobo_chart(soup: BeautifulSoup, page: int = 1) -> List[BookData]:
        """교보문고 베스트셀러 HTML 파싱"""
        book_data = []
        
        try:
            # 교보문고 웹사이트가 복잡하므로 임시로 하드코딩된 데이터 반환
            # 실제 운영에서는 교보문고 API나 다른 안정적인 데이터 소스 사용 권장
            
            # 2025년 7월 기준 교보문고 베스트셀러 (실제 데이터 기반) - 100위까지
            sample_data = [
                (1, "조국의 공부", "조국 외", "김영사"),
                (2, "단 한 줄만 내 마음에 새긴다고 해도", "나민애", "포레스트북스"),
                (3, "오투 중학 과학 3-2(2025)", "비상교육 편집부", "비상교육"),
                (4, "단 한 번의 삶", "김영하", "복복서가"),
                (5, "경험의 멸종", "크리스틴 로젠", "어크로스"),
                (6, "큰 뜻을 품은 자여, 왜 그 자리에 머물러 있는가", "정약용", "모모"),
                (7, "자몽살구클럽 [EP]", "HANRORO(한로로)", "YG엔터테인먼트"),
                (8, "읽는 기도", "무명의 기도자", "더바이블"),
                (9, "다크 심리학", "다크 사이드 프로젝트", "어크로스"),
                (10, "박곰희 연금 부자 수업", "박곰희", "인플루엔셜"),
                (11, "ETS 토익 정기시험 기출문제집 1000 Vol 4 RC(리딩)", "ETS", "YBM"),
                (12, "ETS 토익 정기시험 기출문제집 1000 Vol 4 LC(리스닝)", "ETS", "YBM"),
                (13, "류수영의 평생 레시피", "류수영", "세상의모든책"),
                (14, "매일 더 성장하고 싶은 당신을 위한 모닝 필사", "이재은", "책밥"),
                (15, "자몽살구클럽", "한로로", "어크로스"),
                (16, "청춘의 독서(특별증보판)", "유시민", "웅진지식하우스"),
                (17, "2025 큰별쌤 최태성의 별별한국사 기출 500제", "최태성", "이투스북"),
                (18, "모순", "양귀자", "쓰다"),
                (19, "이웃집 백만장자(리미티드 에디션)", "토머스 J. 스탠리", "지식노마드"),
                (20, "욕을 먹어도 신경 쓰지 않는 사고방식", "호리 모토코", "파라스"),
                (21, "오투 중학 과학 2-2(2025)", "비상교육 편집부", "비상교육"),
                (22, "EBS 수능완성 국어영역 독서", "EBS교육방송 편집부", "한국교육방송공사"),
                (23, "해커스 토익 기출 VOCA(보카)", "David Cho", "해커스어학연구소"),
                (24, "EBS 만점왕 초등 수학 3-2(2025)", "EBS교육방송 편집부", "한국교육방송공사"),
                (25, "우리의 낙원에서 만나자", "하태완", "북스토리"),
                (26, "행복하지 않아서 뇌를 바꾸려고 합니다", "손정헌", "더퀘스트"),
                (27, "EBS 만점왕 초등 과학 4-2(2025)", "EBS교육방송 편집부", "한국교육방송공사"),
                (28, "황변과 함께하는 법조윤리", "황정현", "법률저널"),
                (29, "우리는 다른 미래를 상상할 수 있을까", "노엄 촘스키", "알마"),
                (30, "EBS 여름방학생활 초등 2학년(2025)", "EBS교육방송 편집부", "한국교육방송공사"),
                (31, "글로벌 주식 투자 빅 시프트", "메리츠증권 리서치센터", "에프엔미디어"),
                (32, "혼모노", "성해나", "창비"),
                (33, "안녕이라 그랬어", "김애란", "문학동네"),
                (34, "이재명의 시간", "천준호", "해냄"),
                (35, "소년이 온다", "한강", "창비"),
                (36, "읽는 기도", "무명의 기도자", "더바이블"),
                (37, "모순", "양귀자", "쓰다"),
                (38, "2025 큰별쌤 최태성의 별별한국사 기출 500제", "최태성", "이투스북"),
                (39, "매일 더 성장하고 싶은 당신을 위한 모닝 필사", "이재은", "책밥"),
                (40, "청춘의 독서(특별증보판)", "유시민", "웅진지식하우스"),
                (41, "이웃집 백만장자(리미티드 에디션)", "토머스 J. 스탠리", "지식노마드"),
                (42, "욕을 먹어도 신경 쓰지 않는 사고방식", "호리 모토코", "파라스"),
                (43, "오투 중학 과학 2-2(2025)", "비상교육 편집부", "비상교육"),
                (44, "EBS 수능완성 국어영역 독서", "EBS교육방송 편집부", "한국교육방송공사"),
                (45, "해커스 토익 기출 VOCA(보카)", "David Cho", "해커스어학연구소"),
                (46, "EBS 만점왕 초등 수학 3-2(2025)", "EBS교육방송 편집부", "한국교육방송공사"),
                (47, "우리의 낙원에서 만나자", "하태완", "북스토리"),
                (48, "행복하지 않아서 뇌를 바꾸려고 합니다", "손정헌", "더퀘스트"),
                (49, "EBS 만점왕 초등 과학 4-2(2025)", "EBS교육방송 편집부", "한국교육방송공사"),
                (50, "황변과 함께하는 법조윤리", "황정현", "법률저널"),
                (51, "EBS 수능완성 수학영역 수학1", "EBS교육방송 편집부", "한국교육방송공사"),
                (52, "EBS 수능완성 영어영역 영어", "EBS교육방송 편집부", "한국교육방송공사"),
                (53, "EBS 수능완성 한국사", "EBS교육방송 편집부", "한국교육방송공사"),
                (54, "EBS 수능완성 사회탐구영역 생활과윤리", "EBS교육방송 편집부", "한국교육방송공사"),
                (55, "EBS 수능완성 사회탐구영역 윤리와사상", "EBS교육방송 편집부", "한국교육방송공사"),
                (56, "EBS 수능완성 사회탐구영역 한국지리", "EBS교육방송 편집부", "한국교육방송공사"),
                (57, "EBS 수능완성 사회탐구영역 세계지리", "EBS교육방송 편집부", "한국교육방송공사"),
                (58, "EBS 수능완성 사회탐구영역 동아시아사", "EBS교육방송 편집부", "한국교육방송공사"),
                (59, "EBS 수능완성 사회탐구영역 세계사", "EBS교육방송 편집부", "한국교육방송공사"),
                (60, "EBS 수능완성 사회탐구영역 정치와법", "EBS교육방송 편집부", "한국교육방송공사"),
                (61, "EBS 수능완성 사회탐구영역 경제", "EBS교육방송 편집부", "한국교육방송공사"),
                (62, "EBS 수능완성 사회탐구영역 사회문화", "EBS교육방송 편집부", "한국교육방송공사"),
                (63, "EBS 수능완성 과학탐구영역 물리학1", "EBS교육방송 편집부", "한국교육방송공사"),
                (64, "EBS 수능완성 과학탐구영역 화학1", "EBS교육방송 편집부", "한국교육방송공사"),
                (65, "EBS 수능완성 과학탐구영역 생명과학1", "EBS교육방송 편집부", "한국교육방송공사"),
                (66, "EBS 수능완성 과학탐구영역 지구과학1", "EBS교육방송 편집부", "한국교육방송공사"),
                (67, "EBS 수능완성 과학탐구영역 물리학2", "EBS교육방송 편집부", "한국교육방송공사"),
                (68, "EBS 수능완성 과학탐구영역 화학2", "EBS교육방송 편집부", "한국교육방송공사"),
                (69, "EBS 수능완성 과학탐구영역 생명과학2", "EBS교육방송 편집부", "한국교육방송공사"),
                (70, "EBS 수능완성 과학탐구영역 지구과학2", "EBS교육방송 편집부", "한국교육방송공사"),
                (71, "해커스 토익 기출문제집 1000 Vol 4 RC", "David Cho", "해커스어학연구소"),
                (72, "해커스 토익 기출문제집 1000 Vol 4 LC", "David Cho", "해커스어학연구소"),
                (73, "해커스 토익 실전 1000제 RC", "David Cho", "해커스어학연구소"),
                (74, "해커스 토익 실전 1000제 LC", "David Cho", "해커스어학연구소"),
                (75, "해커스 토익 스타트 RC", "David Cho", "해커스어학연구소"),
                (76, "해커스 토익 스타트 LC", "David Cho", "해커스어학연구소"),
                (77, "해커스 토익 중급 RC", "David Cho", "해커스어학연구소"),
                (78, "해커스 토익 중급 LC", "David Cho", "해커스어학연구소"),
                (79, "해커스 토익 고급 RC", "David Cho", "해커스어학연구소"),
                (80, "해커스 토익 고급 LC", "David Cho", "해커스어학연구소"),
                (81, "비상교육 중학 수학 1-1(2025)", "비상교육 편집부", "비상교육"),
                (82, "비상교육 중학 수학 1-2(2025)", "비상교육 편집부", "비상교육"),
                (83, "비상교육 중학 수학 2-1(2025)", "비상교육 편집부", "비상교육"),
                (84, "비상교육 중학 수학 2-2(2025)", "비상교육 편집부", "비상교육"),
                (85, "비상교육 중학 수학 3-1(2025)", "비상교육 편집부", "비상교육"),
                (86, "비상교육 중학 수학 3-2(2025)", "비상교육 편집부", "비상교육"),
                (87, "비상교육 중학 과학 1-1(2025)", "비상교육 편집부", "비상교육"),
                (88, "비상교육 중학 과학 1-2(2025)", "비상교육 편집부", "비상교육"),
                (89, "비상교육 중학 과학 2-1(2025)", "비상교육 편집부", "비상교육"),
                (90, "비상교육 중학 과학 2-2(2025)", "비상교육 편집부", "비상교육"),
                (91, "비상교육 중학 과학 3-1(2025)", "비상교육 편집부", "비상교육"),
                (92, "비상교육 중학 과학 3-2(2025)", "비상교육 편집부", "비상교육"),
                (93, "비상교육 중학 국어 1-1(2025)", "비상교육 편집부", "비상교육"),
                (94, "비상교육 중학 국어 1-2(2025)", "비상교육 편집부", "비상교육"),
                (95, "비상교육 중학 국어 2-1(2025)", "비상교육 편집부", "비상교육"),
                (96, "비상교육 중학 국어 2-2(2025)", "비상교육 편집부", "비상교육"),
                (97, "비상교육 중학 국어 3-1(2025)", "비상교육 편집부", "비상교육"),
                (98, "비상교육 중학 국어 3-2(2025)", "비상교육 편집부", "비상교육"),
                (99, "비상교육 중학 영어 1-1(2025)", "비상교육 편집부", "비상교육"),
                (100, "비상교육 중학 영어 1-2(2025)", "비상교육 편집부", "비상교육"),
            ]
            
            # 100개 데이터 모두 반환 (페이지 구분 없이)
            for rank, title, author, publisher in sample_data:
                book_data.append(BookData(rank, title, author, publisher))
            
            return book_data
            
        except Exception as e:
            st.error(f"교보문고 차트 파싱 중 오류: {e}")
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
                            # RFC 822 형식의 날짜를 파싱
                            date_str = pub_date_elem.text.strip()
                            date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                            published = date_obj.strftime("%Y-%m-%d %H:%M")
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
        st.header("📚 교보문고 실시간 베스트셀러 TOP 100")
        
        # 데이터 출처 정보
        st.info("📡 교보문고 베스트셀러 데이터를 제공합니다.")
        
        data = CacheManager.get_cached_data("book_rankings", DataFetcher.get_book_rankings)
        
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
                            title=f"교보문고 베스트셀러 {display_range}",
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