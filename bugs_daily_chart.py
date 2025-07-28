import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 워드프레스 이메일 주소
wordpress_email = "vuze274loso@post.wordpress.com"

# 이메일 발신자 정보 (네이버 메일)
sender_email = "dew1052ii@naver.com"
sender_password = "dew1052ii@jhm"

def get_bugs_chart():
    """Bugs 차트에서 데이터를 가져옵니다."""
    url = "https://music.bugs.co.kr/chart/track/day/total"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.134 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    current_rankings = []
    titles = []
    artists = []

    rows = soup.select("tbody > tr")  # 순위 데이터가 포함된 테이블 행

    for row in rows:
        # 현재 순위
        rank_tag = row.select_one(".ranking > strong")
        if not rank_tag:  # 순위가 없는 행(공백 행 또는 광고 행 등) 필터링
            continue

        current_rank = rank_tag.get_text(strip=True)
        current_rankings.append(current_rank)

        # 곡명
        title_tag = row.select_one(".title")
        title = title_tag.get_text(strip=True) if title_tag else "곡명없음"
        titles.append(title)

        # 뮤지션
        artist_tag = row.select_one(".artist")
        artist = artist_tag.get_text(strip=True) if artist_tag else "뮤지션없음"
        artists.append(artist)

    chart_data = []
    for rank, title, artist in zip(current_rankings, titles, artists):
        chart_data.append(f"{rank}. {title} - {artist}")
    
    return chart_data

def send_email_to_wordpress(chart_data):
    """Bugs 차트를 이메일로 워드프레스에 전송합니다."""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # 이메일 제목과 내용 구성
    subject = f"[Bugs 데일리 차트] {current_time}"
    body = "[category bugs_daily_chart]\n\n*Bugs 데일리 차트*\n\n"
    for entry in chart_data[:100]:  # 최대 100위까지 포스팅
        body += f"{entry}\n"

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
            print("Bugs 차트를 성공적으로 워드프레스에 전송했습니다.")
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("Bugs 차트를 가져오는 중...")
    try:
        chart_data = get_bugs_chart()
        if chart_data:
            send_email_to_wordpress(chart_data)
        else:
            print("Bugs 차트를 가져오지 못했습니다.")
    except Exception as e:
        print(f"작업 중 오류가 발생했습니다: {e}")