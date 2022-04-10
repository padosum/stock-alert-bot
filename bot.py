import os
import telegram
import pytz
import requests
import re
import schedule
import datetime
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

count = 1


def job():
    global count
    count += 1

    # 23시 ~ 6시에 알림 x
    now = datetime.datetime.now(pytz.timezone('Asia/Seoul'))
    if now.hour >= 23 or now.hour < 6:
        return

    token = os.getenv('TELEGRAM_TOKEN')
    bot = telegram.Bot(token=token)
    chat_id = os.getenv('CHAT_ID')

    with requests.Session() as s:
        # 재고 확인 사이트 주소
        url = os.getenv('BASE_URL')
        res = s.get(url)
        if res.status_code == requests.codes.ok:
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            search_result = soup.select('#content ul')[2]
            products = search_result.select('li')
            outOfStock = False

            for l in products:
                name = l.select('strong')[0].text
                price = l.select('strong span')[0].text
                price_format = int(re.findall("\d+", price)[0])
                url = f"https://smartstore.naver.com{l.find('a').get('href')}".replace(
                    ".", "\\.")

                # 10,000원 이상 제품
                if price_format < 10:
                    continue

                outOfStock = True if len(
                    l.select('span.text.blind')) == 0 else False

                if outOfStock != False:
                    break

        if outOfStock:
            bot.sendMessage(chat_id=chat_id,
                            text=f"🎉 *구매 가능* {url}", parse_mode="MarkdownV2")
        else:
            # 품절 알림은 6번에 1번 메시지 전송
            if count % 6 == 0:
                bot.sendMessage(chat_id=chat_id, text="😂 *품절*",
                                parse_mode="MarkdownV2")
            else:
                print("Out of stock")


# 1시간 마다 실행
schedule.every(60).minutes.do(job)

print("Start App")

# 스케줄러
while True:
    schedule.run_pending()
    time.sleep(1)
