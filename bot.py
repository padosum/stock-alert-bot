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
        url = os.getenv('SEARCH_URL')
        res = s.get(url)
        if res.status_code == requests.codes.ok:
            html = res.text
            soup = BeautifulSoup(html, 'html.parser')
            search_result = soup.select('#content ul')[2]
            products = search_result.select('li')
            inStock = False

            for l in products:
                name = l.select('strong')[0].text
                price = l.select('strong span')[0].text
                price_format = int(re.findall("\d+", price)[0])
                base_url = os.getenv('BASE_URL')
                url = f"{base_url}{l.find('a').get('href')}".replace(
                    ".", "\\.")

                # 가격 확인
                if price_format > int(os.getenv('BASE_PRICE')):
                    continue

                if len(l.select('span.text.blind')) == 0:
                  inStock = True
                else:
                  if l.select('span.text.blind')[0].text == '일시 품절':
                    inStock = False
                  else:
                    inStock = True

                # if inStock != False:
                #     break

        if inStock:
            bot.sendMessage(chat_id=chat_id,
                            text=f"🎉 *구매 가능* {url}", parse_mode="MarkdownV2")
        else:
            # 품절 알림은 4번에 1번 메시지 전송
            if count % 4 == 0:
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
