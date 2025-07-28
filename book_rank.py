import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 워드프레스 이메일 주소
wordpress_email = "vuze274loso@post.wordpress.com"

# 이메일 발신자 정보 (하드코딩)
sender_email = "dew1052ii@naver.com"
sender_password = "dew1052ii@jhm"

def get_aladin_bestseller():
    """알라딘 베스트셀러에서 데이터를 가져옵니다."""
    url = "https://www.aladin.co.kr/shop/common/wbest.aspx?BranchType=1&start=we"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.134 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        soup = BeautifulSoup(response.text, "html.parser")
        
        books = soup.select(".ss_book_box")
        bestseller_data = []

        for rank, book in enumerate(books, start=1):
            # 순위
            rank_str = f"{rank}위"

            # 책 제목
            title_tag = book.select_one(".bo3")
            title = title_tag.get_text(strip=True) if title_tag else "정보 없음"

            # 지은이
            author_tag = book.select_one("li > a[href*='AuthorSearch']")
            author = author_tag.get_text(strip=True) if author_tag else "정보 없음"

            bestseller_data.append(f"{rank_str}: {title} / 지은이: {author}")

            if rank == 50:  # 1위부터 50위까지만 가져오기
                break

        return bestseller_data
    except requests.RequestException as e:
        print(f"웹 크롤링 중 오류가 발생했습니다: {e}")
        return []

def send_email_to_wordpress(bestseller_data):
    """알라딘 베스트셀러 데이터를 이메일로 워드프레스에 전송합니다."""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # 이메일 제목과 내용 구성
    subject = f"[알라딘 베스트셀러] {current_time}"
    body = "[category book_daily_chart]\n\n*알라딘 베스트셀러*\n\n"
    for entry in bestseller_data:
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
            print("알라딘 베스트셀러를 성공적으로 워드프레스에 전송했습니다.")
    except Exception as e:
        print(f"이메일 전송 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("알라딘 베스트셀러 데이터를 가져오는 중...")
    try:
        bestseller_data = get_aladin_bestseller()
        if bestseller_data:
            send_email_to_wordpress(bestseller_data)
        else:
            print("알라딘 베스트셀러 데이터를 가져오지 못했습니다.")
    except Exception as e:
        print(f"작업 중 오류가 발생했습니다: {e}")