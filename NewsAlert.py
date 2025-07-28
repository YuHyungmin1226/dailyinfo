import requests

def send_news_to_slack(news_list, slack_webhook_url):
    message = "*최신 뉴스*\n\n"
    for news in news_list:
        message += f"• *{news['title']}*\n{news['link']}\n\n"

    payload = {
        "text": message,
        "mrkdwn": True
    }

    try:
        response = requests.post(slack_webhook_url, json=payload)
        if response.status_code == 200:
            print("뉴스를 Slack 채널로 성공적으로 전송했습니다.")
        else:
            print(f"뉴스 전송 실패: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"뉴스 전송 실패: {e}")

def get_google_news():
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
    
    return news_list

if __name__ == "__main__":
    print("구글 뉴스를 가져오는 중...")
    news = get_google_news()

    if news:
        # Slack 웹후크 URL 설정
        slack_webhook_url = "https://hooks.slack.com/services/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"

        print("Slack 채널로 뉴스를 전송하는 중...")
        send_news_to_slack(news, slack_webhook_url)
    else:
        print("구글 뉴스를 가져오지 못했습니다.")
