import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

# 워드프레스 이메일 주소
wordpress_email = "vuze274loso@post.wordpress.com"

# 이메일 발신자 정보 (네이버 메일)
sender_email = "dew1052ii@naver.com"
sender_password = "dew1052ii@jhm"  # 네이버 비밀번호 반영

def get_google_news():
    """구글 뉴스 RSS에서 최신 뉴스를 가져옵니다."""
    url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"

    response = requests.get(url)
    xml_data = response.text

    news_list = []

    if response.status_code == 200:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        
        for item in root.iter("item"):
            title = item.find("title").text
            link = item.find("link").text

            news_list.append({
                "title": title,
                "link": link
            })
    else:
        print("구글 뉴스를 가져오는 중 오류가 발생했습니다.")
    
    return news_list

def send_email_to_wordpress(news_list):
    """구글 뉴스를 이메일로 워드프레스에 전송합니다."""
    # 현재 날짜와 시간 추가
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 이메일 제목과 내용 구성
    subject = f"[뉴스 업데이트] {current_time}"
    body = "*최신 뉴스*\n\n"
    for news in news_list[:10]:  # 최신 뉴스 10개만 가져오기
        body += f"• *{news['title']}*\n{news['link']}\n\n"

    # 이메일 메시지 구성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = wordpress_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # 네이버 SMTP 서버에 연결
        with smtplib.SMTP("smtp.naver.com", 587) as server:
            server.starttls()  # TLS 연결 시작
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, wordpress_email, msg.as_string())
            print("뉴스를 성공적으로 워드프레스에 전송했습니다.")
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("뉴스 업데이트 시작...")
    news = get_google_news()
    if news:
        send_email_to_wordpress(news)
    else:
        print("가져온 뉴스가 없습니다.")
