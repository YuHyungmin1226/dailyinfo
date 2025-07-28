import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
# XML 파서를 명시적으로 지정하기 위해 lxml 설치 필요
from collections import Counter
from textblob import TextBlob
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# 워드프레스 이메일 정보
wordpress_email = "vuze274loso@post.wordpress.com"

# 이메일 발신자 정보
sender_email = "dew1052ii@naver.com"
sender_password = "dew1052ii@jhm"

def get_latest_news():
    """Google 뉴스 RSS에서 모든 뉴스 제목을 가져옵니다."""
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
        soup = BeautifulSoup(response.content, "xml")  # XML 파서를 명시적으로 지정
        titles = [item.find("title").text for item in soup.find_all("item")]
        all_titles.update(titles)  # 중복 제거하며 병합
    return list(all_titles)

def get_naver_stock_data():
    """네이버 금융의 시세 정보를 크롤링합니다."""
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
    return stock_data

def filter_news_by_stock(stock_data, news_titles):
    """뉴스 기사 제목 중 시세 데이터에 포함된 종목명이 들어 있는 기사를 필터링."""
    stock_names = {stock["종목명"] for stock in stock_data}
    filtered_news = []
    for title in news_titles:
        for stock_name in stock_names:
            if stock_name in title:
                filtered_news.append((stock_name, title))
    return filtered_news

def analyze_sentiments(news_titles):
    """뉴스 제목의 감성을 분석합니다."""
    sentiment_results = []
    for stock_name, title in news_titles:
        blob = TextBlob(title)
        polarity = blob.sentiment.polarity
        sentiment_results.append((stock_name, title, polarity))
    return sentiment_results

def recommend_stocks(sentiment_results):
    """감성 분석 결과를 기반으로 종목 추천."""
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
    return recommendations

def send_email_to_wordpress(recommendations, total_news, filtered_news):
    """추천 종목 정보를 이메일로 워드프레스에 전송합니다."""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    subject = f"[뉴스 기반 투자 추천] {current_time}"
    body = "[category stock_daily_recommend]\n\n"
    body += "*뉴스 기반 유망 종목 추천*\n\n"
    body += f"크롤링된 뉴스 개수: {total_news}\n"
    body += f"필터링된 뉴스 개수: {filtered_news}\n\n"

    if recommendations:
        body += "\n".join(recommendations)
    else:
        body += "추천할 종목이 없습니다."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = wordpress_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp.naver.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, wordpress_email, msg.as_string())
            print("추천 정보를 성공적으로 워드프레스에 전송했습니다.")
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("네이버 시세 데이터를 크롤링 중...")
    stock_data = get_naver_stock_data()
    print(f"네이버 시세 데이터 종목명:\n{[stock['종목명'] for stock in stock_data]}")

    print("뉴스를 크롤링 중...")
    news_titles = get_latest_news()
    total_news_count = len(news_titles)
    print(f"크롤링된 뉴스 개수: {total_news_count}")

    print("시세 데이터와 뉴스 기사 비교 중...")
    filtered_news = filter_news_by_stock(stock_data, news_titles)
    filtered_news_count = len(filtered_news)
    print(f"필터링된 뉴스 개수: {filtered_news_count}")

    print("감성 분석 진행 중...")
    sentiment_results = analyze_sentiments(filtered_news)

    print("종목 추천 작성 중...")
    recommendations = recommend_stocks(sentiment_results)

    print("추천 종목 이메일 전송 중...")
    send_email_to_wordpress(recommendations, total_news_count, filtered_news_count)
