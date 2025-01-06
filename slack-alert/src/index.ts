import {WebClient} from "@slack/web-api";
import * as cheerio from 'cheerio';
import axios from "axios";

const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN || '';
const SLACK_CHANNEL_ID = process.env.SLACK_CHANNEL_ID || '';
const CRAWL_URL = process.env.CRAWL_URL || '';
const KEYWORDS = process.env.KEYWORDS ? process.env.KEYWORDS.split(',') : [];

const slackClient = new WebClient(SLACK_BOT_TOKEN)

const crawlWebsite =async  (url: string, keywords: string[]) =>{
    try {
        // URL에서 HTML 데이터를 가져옴
        const response = await axios.get(url);
        const $ = cheerio.load(response.data);

        // 문서 내 모든 텍스트 추출 후 키워드 포함 여부 검사
        const matchingText = $('body')
            .text() // 문서 전체 텍스트를 가져옴
            .split('\n') // 줄 단위로 분리
            .map((line) => line.trim()) // 각 줄의 공백 제거
            .filter((line) =>
                keywords.some((keyword) => line.includes(keyword)) // 키워드 배열 중 하나라도 포함되면 필터링
            );

        if (matchingText.length > 0) {
         const result = matchingText.join(', ')
         await sendSlackMessage(SLACK_CHANNEL_ID, result)
        }
    } catch (error) {
        console.error('An Error occurred while retrieving web site', error)
    }
}

const sendSlackMessage = async (channel: string, text: string) => {
    try {
        await slackClient.chat.postMessage({
            channel,
            text
        })
    } catch (error) {
        console.log('An Error occurred while sending message', error)
    }
}


const scheduleDailyTask = () => {
    const now =  new Date()

    const calculateNextRun = (hour: number) => {
        const nextRun = new Date()
        nextRun.setUTCHours(hour - 9, 0, 0, 0)
        if (nextRun <= now) {
            nextRun.setDate(nextRun.getDate() + 1)
        }
        return nextRun
    }

    const scheduleTask = (hour: number) => {
        const nextRun = calculateNextRun(hour);
        const delay = nextRun.getTime() - now.getTime();
        console.log(`📆 다음 실행 시간 (한국시간): ${nextRun.toLocaleString('ko-KR', {
            timeZone: 'Asia/Seoul',
        })}`);

        setTimeout(async function runTask() {
            try {
                await crawlWebsite(CRAWL_URL, KEYWORDS);
            } catch (error) {
                console.error('작업 실행 중 오류:', error);
            }

            // 이후 매일 실행
            setInterval(async () => {
                try {
                    await crawlWebsite(CRAWL_URL, KEYWORDS);
                } catch (error) {
                    console.error('작업 실행 중 오류:', error);
                }
            }, 24 * 60 * 60 * 1000);
        }, delay);
    }

    scheduleTask(9)
    scheduleTask(22)
}

scheduleDailyTask()
