import streamlit as st
from melon_daily_chart import get_melon_chart
from bugs_daily_chart import get_bugs_chart
from book_rank import get_aladin_bestseller
from Weather_review_auto import get_weather_info
from NewsPost import get_google_news
import streamlit.components.v1 as components

st.set_page_config(page_title="데이터 정보 대시보드", layout="wide")
st.title("데이터 정보 대시보드")

menu = st.sidebar.selectbox(
    "보고 싶은 정보를 선택하세요",
    (
        "멜론 일간 차트",
        "벅스 일간 차트",
        "도서 순위",
        "날씨 정보",
        "뉴스(구글)"
    )
)

def parse_weather_info(weather_str):
    # 예시: 'Weather: clear sky\nTemperature: 20°C\nHumidity: 50%\nWind Speed: 2 m/s\nWind Direction: NW'
    lines = weather_str.split("\n")
    info = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    # 한국어 설명문 생성
    desc = info.get("Weather", "").replace("clear sky", "맑음").replace("few clouds", "구름 조금").replace("scattered clouds", "구름 많음").replace("broken clouds", "흐림").replace("shower rain", "소나기").replace("rain", "비").replace("thunderstorm", "뇌우").replace("snow", "눈").replace("mist", "안개")
    temp = info.get("Temperature", "")
    humidity = info.get("Humidity", "")
    wind_speed = info.get("Wind Speed", "")
    wind_dir = info.get("Wind Direction", "")
    result = f"오늘의 서울 날씨는 {desc}입니다.\n기온: {temp}, 습도: {humidity}, 바람: {wind_speed} ({wind_dir} 방향)"
    return result

if menu == "멜론 일간 차트":
    st.header("멜론 일간 차트 TOP 100")
    try:
        data = get_melon_chart()
        st.write("\n".join(data))
    except Exception as e:
        st.error(f"멜론 차트 정보를 불러오는 중 오류 발생: {e}")

elif menu == "벅스 일간 차트":
    st.header("벅스 일간 차트 TOP 100")
    try:
        data = get_bugs_chart()
        st.write("\n".join(data))
    except Exception as e:
        st.error(f"벅스 차트 정보를 불러오는 중 오류 발생: {e}")

elif menu == "도서 순위":
    st.header("알라딘 베스트셀러 TOP 50")
    try:
        data = get_aladin_bestseller()
        # 리스트로 받아서 한 줄씩 출력
        for entry in data:
            st.write(entry)
    except Exception as e:
        st.error(f"도서 순위 정보를 불러오는 중 오류 발생: {e}")

elif menu == "날씨 정보":
    st.header("서울 날씨 정보")
    try:
        data = get_weather_info()
        st.write(parse_weather_info(data))
    except Exception as e:
        st.error(f"날씨 정보를 불러오는 중 오류 발생: {e}")

elif menu == "뉴스(구글)":
    st.header("구글 뉴스 최신 10건")
    try:
        news_list = get_google_news()
        for news in news_list[:10]:
            st.markdown(f"- [{news['title']}]({news['link']})")
    except Exception as e:
        st.error(f"뉴스 정보를 불러오는 중 오류 발생: {e}") 