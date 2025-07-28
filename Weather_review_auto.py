import requests
from datetime import datetime
import json

# OpenWeatherMap API 키
API_KEY = "35cff755c77fb497fd85bdc86605fac9"

# Slack 웹훅 URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

# Slack 메시지 전송 함수
def send_slack_message(message):
    payload = {
        "text": message
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code != 200:
        print("Error sending Slack message")

# 현재 시각 정보 가져오기
def get_current_time():
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    return current_time

# 풍향 정보 가져오기
def get_wind_direction(degrees):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return directions[index]

# 날씨 정보 가져오기
def get_weather_info():
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        wind_direction = data["wind"]["deg"]
        wind_direction_str = get_wind_direction(wind_direction)
        weather_info = f"Weather: {weather_description}\nTemperature: {temperature}°C\nHumidity: {humidity}%\nWind Speed: {wind_speed} m/s\nWind Direction: {wind_direction_str}"
        return weather_info
    else:
        print("Error retrieving weather information")

# 메시지 전송 함수
def send_message():
    # 현재 시각
    current_time = get_current_time()

    # 날씨 정보
    weather_info = get_weather_info()

    # Slack 메시지 작성
    slack_message = f"Current Time: {current_time}\n\nWeather Information:\n{weather_info}"

    # Slack으로 메시지 전송
    send_slack_message(slack_message)

def main():
    # 메시지 한 번만 보내기
    send_message()
    print("날씨 정보가 Slack으로 전송되었습니다.")

if __name__ == "__main__":
    main()
