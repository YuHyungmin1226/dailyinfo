import requests
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from textblob import TextBlob
import time

# 공통 설정
WORDPRESS_EMAIL = "vuze274loso@post.wordpress.com"
SENDER_EMAIL = "dew1052ii@naver.com"
SENDER_PASSWORD = "dew1052ii@jhm"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
OPENWEATHER_API_KEY = "35cff755c77fb497fd85bdc86605fac9"

class DailyInfoCollector:
    def __init__(self):
        self.now = datetime.now()
        self.current_time = self.now.strftime("%Y-%m-%d %H:%M:%S")

    def send_slack_message(self, message):
        """Slack으로 메시지를 전송합니다."""
        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print("Error sending Slack message")

    def send_email_to_wordpress(self, subject, body, category):
        """워드프레스로 이메일을 전송합니다."""
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = WORDPRESS_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(f"[category {category}]\n\n{body}", 'plain'))

        try:
            with smtplib.SMTP("smtp.naver.com", 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, WORDPRESS_EMAIL, msg.as_string())
                print(f"{subject}를 성공적으로 워드프레스에 전송했습니다.")
        except Exception as e:
            print(f"이메일 전송 중 오류가 발생했습니다: {e}")

    def get_weather_info(self):
        """서울의 날씨 정보를 가져옵니다."""
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            wind_direction = data["wind"]["deg"]
            
            # 풍향 계산
            directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            wind_direction_str = directions[round(wind_direction / 45) % 8]
            
            weather_info = f"*서울 날씨 정보*\n\n"
            weather_info += f"날씨: {weather_description}\n"
            weather_info += f"기온: {temperature}°C\n"
            weather_info += f"습도: {humidity}%\n"
            weather_info += f"풍속: {wind_speed} m/s\n"
            weather_info += f"풍향: {wind_direction_str}"
            
            return weather_info
        else:
            return "날씨 정보를 가져오는데 실패했습니다."

    def get_news_info(self):
        """구글 뉴스 정보를 가져옵니다."""
        url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
        response = requests.get(url)
        news_list = []

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            for item in root.iter("item"):
                title = item.find("title").text
                link = item.find("link").text
                news_list.append({"title": title, "link": link})

        news_info = "*최신 뉴스*\n\n"
        for news in news_list[:10]:  # 최신 뉴스 10개만
            news_info += f"• *{news['title']}*\n{news['link']}\n\n"
        
        return news_info

    def get_stock_recommendation(self):
        """주식 추천 정보를 가져옵니다."""
        # 네이버 시세 데이터 크롤링
        url = "https://finance.naver.com/sise/sise_quant.naver"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"class": "type_2"})
        rows = table.find_all("tr")
        stock_data = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 10:
                continue
            stock_name = cols[1].get_text(strip=True)
            stock_data.append({"종목명": stock_name})

        # 뉴스 데이터 수집
        rss_urls = [
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR%3Ako",  # 주요 뉴스
            "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFp4WkRNU0FtdHZLQUFQAQ?hl=ko&gl=KR&ceid=KR%3Ako",  # 비즈니스
            "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtdHZLQUFQAQ?hl=ko&gl=KR&ceid=KR%3Ako",  # 경제
            "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR%3Ako",  # 기술
            "https://news.google.com/rss/topics/CAAqKAgKIiJDQkFTRXdvSkwyMHZNR1ptZHpWbUVnSnJieG9DUzFJb0FBUAE?hl=ko&gl=KR&ceid=KR%3Ako"  # 산업 및 기업
        ]

        all_titles = set()
        for url in rss_urls:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            titles = [item.find("title").text for item in soup.find_all("item")]
            all_titles.update(titles)

        # 뉴스 필터링
        stock_names = {stock["종목명"] for stock in stock_data}
        filtered_news = []
        for title in all_titles:
            for stock_name in stock_names:
                if stock_name in title:
                    filtered_news.append((stock_name, title))

        # 감성 분석
        sentiment_results = []
        for stock_name, title in filtered_news:
            blob = TextBlob(title)
            polarity = blob.sentiment.polarity
            sentiment_results.append((stock_name, title, polarity))

        # 종목 추천
        stock_dict = {}
        for stock_name, title, polarity in sentiment_results:
            if stock_name not in stock_dict:
                stock_dict[stock_name] = {"titles": [], "polarity": 0, "count": 0}

            stock_dict[stock_name]["titles"].append(title)
            stock_dict[stock_name]["polarity"] += polarity
            stock_dict[stock_name]["count"] += 1

        recommendations = []
        for stock_name, data in stock_dict.items():
            avg_polarity = data["polarity"] / data["count"]
            if avg_polarity > 0.5:
                signal = "매수"
            elif avg_polarity < -0.5:
                signal = "매도"
            else:
                signal = "중립"

            related_titles = "; ".join(data["titles"])
            recommendations.append(
                f"종목명: {stock_name} | 의견: {signal} | 평균 감성 점수: {avg_polarity:.2f} | 관련 뉴스: {related_titles}"
            )

        # 결과 포맷팅
        stock_info = "*뉴스 기반 유망 종목 추천*\n\n"
        stock_info += f"크롤링된 뉴스 개수: {len(all_titles)}\n"
        stock_info += f"필터링된 뉴스 개수: {len(filtered_news)}\n\n"
        
        if recommendations:
            stock_info += "\n".join(recommendations)
        else:
            stock_info += "추천할 종목이 없습니다."

        return stock_info

    def get_melon_chart(self):
        """멜론 차트 정보를 가져옵니다."""
        url = "https://www.melon.com/chart/day/index.htm"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        chart_data = []
        rows = soup.select("tbody > tr")

        for row in rows:
            rank_tag = row.select_one(".rank")
            title_tag = row.select_one(".ellipsis.rank01 > span > a")
            artist_tag = row.select_one(".ellipsis.rank02 > a")
            
            if rank_tag and title_tag and artist_tag:
                rank = rank_tag.get_text(strip=True)
                title = title_tag.get_text(strip=True)
                artist = artist_tag.get_text(strip=True)
                chart_data.append(f"{rank}. {title} - {artist}")
        
        chart_info = "*멜론 데일리 차트*\n\n"
        for entry in chart_data[:100]:
            chart_info += f"{entry}\n"
        
        return chart_info

    def get_bugs_chart(self):
        """벅스 차트 정보를 가져옵니다."""
        url = "https://music.bugs.co.kr/chart/track/day/total"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        chart_data = []
        rows = soup.select("tbody > tr")

        for row in rows:
            rank_tag = row.select_one(".ranking > strong")
            if not rank_tag:
                continue

            title_tag = row.select_one(".title")
            artist_tag = row.select_one(".artist")
            
            if title_tag and artist_tag:
                rank = rank_tag.get_text(strip=True)
                title = title_tag.get_text(strip=True)
                artist = artist_tag.get_text(strip=True)
                chart_data.append(f"{rank}. {title} - {artist}")

        chart_info = "*벅스 데일리 차트*\n\n"
        for entry in chart_data[:100]:
            chart_info += f"{entry}\n"
        
        return chart_info

    def get_book_rank(self):
        """알라딘 베스트셀러 정보를 가져옵니다."""
        url = "https://www.aladin.co.kr/shop/common/wbest.aspx?BranchType=1&start=we"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        books = soup.select(".ss_book_box")
        book_data = []

        for rank, book in enumerate(books, start=1):
            title_tag = book.select_one(".bo3")
            author_tag = book.select_one("li > a[href*='AuthorSearch']")
            
            if title_tag and author_tag:
                title = title_tag.get_text(strip=True)
                author = author_tag.get_text(strip=True)
                book_data.append(f"{rank}위: {title} / 지은이: {author}")

            if rank == 50:
                break

        book_info = "*알라딘 베스트셀러*\n\n"
        for entry in book_data:
            book_info += f"{entry}\n"
        
        return book_info

    def collect_all_info(self):
        """모든 정보를 수집하고 전송합니다."""
        # 날씨 정보
        weather_info = self.get_weather_info()
        self.send_slack_message(weather_info)
        self.send_email_to_wordpress(
            f"[날씨 정보] {self.current_time}",
            weather_info,
            "weather_daily_info"
        )

        # 뉴스 정보
        news_info = self.get_news_info()
        self.send_email_to_wordpress(
            f"[뉴스 업데이트] {self.current_time}",
            news_info,
            "news_update"
        )

        # 주식 추천
        stock_info = self.get_stock_recommendation()
        self.send_email_to_wordpress(
            f"[뉴스 기반 투자 추천] {self.current_time}",
            stock_info,
            "stock_daily_recommend"
        )

        # 멜론 차트
        melon_info = self.get_melon_chart()
        self.send_email_to_wordpress(
            f"[멜론 데일리 차트] {self.current_time}",
            melon_info,
            "melon_daily_chart"
        )

        # 벅스 차트
        bugs_info = self.get_bugs_chart()
        self.send_email_to_wordpress(
            f"[벅스 데일리 차트] {self.current_time}",
            bugs_info,
            "bugs_daily_chart"
        )

        # 베스트셀러
        book_info = self.get_book_rank()
        self.send_email_to_wordpress(
            f"[알라딘 베스트셀러] {self.current_time}",
            book_info,
            "book_daily_chart"
        )

def main():
    collector = DailyInfoCollector()
    print("일일 정보 수집을 시작합니다...")
    collector.collect_all_info()
    print("모든 정보 수집이 완료되었습니다.")

if __name__ == "__main__":
    main() 