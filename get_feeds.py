import feedparser
import requests
import re
import telegram
import asyncio  
import os 
from telegram.constants import ParseMode

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORDS_TO_FIND = [
    'idor', 'xss', 'sqli', 'sql injection',
    'rce', 'lfi', 'ssrf', 'cve-'
]


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1', 'Connection': 'keep-alive', 'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'TE': 'trailers'
}


FEEDS_TO_CHECK = [
    "https://www.reddit.com/r/bugbounty.rss",
    "https://medium.com/feed/tag/security-writeup",
    "https://portswigger.net/blog/rss"
]


async def send_telegram_messages(articles_list):
    print(f"Preparing to send {len(articles_list)} articles to Telegram Chat ID {TELEGRAM_CHAT_ID}...")
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    print("Telegram Bot initialized.")

    
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"🔥 *Daily Security Write-ups ({len(articles_list)} Found)* 🔥",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
         print(f"[Telegram Error] Failed to send initial message: {e}")

    for article in articles_list:
        message_text = f"*Source:* `{article['source']}`\n"
        message_text += f"*Title:* {article['title']}\n\n"
        message_text += f"[Read Article]({article['link']})"
        
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False 
            )
            print(f"Sent: {article['title']}")
            await asyncio.sleep(1) 
        except Exception as e:
            print(f"[Telegram Error] Failed to send article '{article['title']}': {e}")
            
    print("Finished sending all articles to Telegram.")

print("--- Starting to fetch articles (v15 - Async Fix) ---")
print(f"Filtering for keywords: {KEYWORDS_TO_FIND}\n")

all_found_articles = []

for feed_url in FEEDS_TO_CHECK:
    print(f"--- Checking Source: {feed_url.split('/')[2]} ---")
    
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            d = feedparser.parse(response.content)
            print(f"[Debug] Found {len(d.entries)} total articles. Now filtering...")
            
            for entry in d.entries:
                title = entry.title.lower()
                for keyword in KEYWORDS_TO_FIND:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                        if entry.link not in [a['link'] for a in all_found_articles]:
                            all_found_articles.append({
                                'title': entry.title,
                                'link': entry.link,
                                'source': feed_url.split('/')[2]
                            })
                            break
        else:
            print(f"[Error] Failed to fetch. Server responded with status code: {response.status_code}")
    except Exception as e:
        print(f"[Error] An error occurred while trying to fetch: {e}")

print("\n--- Finished Fetching. Filtered Results: ---")

if not all_found_articles:
    print("No articles found matching your keywords today.")
else:
    print(f"Found {len(all_found_articles)} matching articles:\n")
    for article in all_found_articles:
        print(f"Source: {article['source']}")
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}\n")
    
    try:
        print("Now sending to Telegram (using asyncio)...")
        asyncio.run(send_telegram_messages(all_found_articles))
    except Exception as e:
        print(f"An error occurred while running the async sender: {e}")

print("--- Script Finished ---")