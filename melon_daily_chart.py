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

def get_melon_chart():
    """멜론 차트에서 데이터를 가져옵니다."""
    url = "https://www.melon.com/chart/day/index.htm"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.134 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    rows = soup.select("tbody > tr")
    chart_data = []

    for row in rows:
        rank_tag = row.select_one(".rank")
        title_tag = row.select_one(".ellipsis.rank01 > span > a")
        artist_tag = row.select_one(".ellipsis.rank02 > a")
        
        if rank_tag and title_tag and artist_tag:
            rank = rank_tag.get_text(strip=True)
            title = title_tag.get_text(strip=True)
            artist = artist_tag.get_text(strip=True)
            chart_data.append(f"{rank}. {title} - {artist}")
    
    return chart_data

def send_email_to_wordpress(chart_data):
    """멜론 차트를 이메일로 워드프레스에 전송합니다."""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # 이메일 제목과 내용 구성
    subject = f"[멜론 데일리 차트] {current_time}"
    body = "[category melon_daily_chart]\n\n*멜론 데일리 차트*\n\n"
    for entry in chart_data[:100]:
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
            print("멜론 차트를 성공적으로 워드프레스에 전송했습니다.")
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("멜론 차트를 가져오는 중...")
    chart_data = get_melon_chart()
    if chart_data:
        send_email_to_wordpress(chart_data)
    else:
        print("멜론 차트를 가져오지 못했습니다.")