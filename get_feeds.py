import feedparser
import requests
import re
import telegram
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from telegram.constants import ParseMode


DB_FILE = 'writeups.db'
PRUNE_AFTER_DAYS = 30
MAX_ARTICLES_TO_SEND = 3 

SOURCE_SCORES = {
    'portswigger.net': 3,            
    'googleprojectzero.blogspot.com': 3, 
    'blog.intigriti.com': 2,        
    'infosec-writeups.com': 2,       
    'www.reddit.com': 1,             
    'medium.com': 1,              
}

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


KEYWORDS_TO_FIND = [
    'idor', 'xss', 'sqli', 'sql injection', 'rce', 'lfi', 'ssrf', 'cve-',
    'writeup', 'write-up', 'bounty', 'disclosure', 'disclosed', 'walkthrough', 'bug'
]
REDDIT_FLAIRS_TO_BLOCK = [
    'question / discussion', 'beginner / newbie qa', 'collaboration / mentorship',
    'question', 'discussion', 'help'
]


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1', 
    'Connection': 'keep-alive', 
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document', 
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none', 
    'Sec-Fetch-User': '?1', 
    'TE': 'trailers'
}


FEEDS_TO_CHECK = [
    "https://www.reddit.com/r/bugbounty.rss",
    "https://portswigger.net/blog/rss",
    "https://medium.com/feed/tag/security-writeup", 
    "https://infosec-writeups.com/feed",
    "https://blog.intigriti.com/feed/",
    "https://googleprojectzero.blogspot.com/feeds/posts/default" # (ضفناه عشان النقط العالية)
]


async def send_telegram_messages(articles_list):
    print(f"Preparing to send {len(articles_list)} articles to Telegram Chat ID {TELEGRAM_CHAT_ID}...")
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    print("Telegram Bot initialized.")
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🔥 *Daily Security Write-ups ({len(articles_list)} Found)* 🔥", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
         print(f"[Telegram Error] Failed to send initial message: {e}")
    for article in articles_list:
        message_text = f"*Source:* `{article['source']}`\n"
        message_text += f"*Title:* {article['title']}\n\n"
        message_text += f"[Read Article]({article['link']})"
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)
            print(f"Sent: {article['title']}")
            await asyncio.sleep(1) 
        except Exception as e:
            print(f"[Telegram Error] Failed to send article '{article['title']}': {e}")
    print("Finished sending all articles to Telegram.")


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sent_links (
        link TEXT PRIMARY KEY,
        added_at TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DB_FILE}' initialized successfully.")

def is_link_sent(link):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_links WHERE link = ?", (link,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_new_link(link):
    timestamp = datetime.now()
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sent_links (link, added_at) VALUES (?, ?)", (link, timestamp))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass 
    except Exception as e:
        print(f"[DB Error] Failed to save link: {e}")

def prune_old_links():
    
    try:
        cutoff_date = datetime.now() - timedelta(days=PRUNE_AFTER_DAYS)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sent_links WHERE added_at < ?", (cutoff_date,))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"Pruned {rows_deleted} links older than {PRUNE_AFTER_DAYS} days.")
    except Exception as e:
        print(f"[DB Error] Failed to prune old links: {e}")

print("--- Starting to fetch articles (v21 - Priority Queue Edition) ---")

init_db()
prune_old_links()
print(f"Filtering for keywords: {KEYWORDS_TO_FIND}\n")


all_found_articles_with_score = [] 

for feed_url in FEEDS_TO_CHECK:
    source_domain = feed_url.split('/')[2] # (مثال: 'portswigger.net')
    score = SOURCE_SCORES.get(source_domain, 1) # (هيجيب النقطة، لو مش موجود هيدي 1)
    
    print(f"--- Checking Source: {source_domain} (Score: {score}) ---")
    
    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            d = feedparser.parse(response.content)
            print(f"[Debug] Found {len(d.entries)} total articles. Now filtering...")
            
            for entry in d.entries:
                title = entry.title.lower()
                link = entry.link
                
                if is_link_sent(link):
                    continue 

                found_keyword = False
                for keyword in KEYWORDS_TO_FIND:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                        found_keyword = True
                        break
                if not found_keyword:
                    continue 

                if source_domain == 'www.reddit.com':
                    flair_is_bad = False
                    if hasattr(entry, 'tags'): 
                        for tag in entry.tags:
                            flair = tag.term.lower().strip()
                            if flair in REDDIT_FLAIRS_TO_BLOCK:
                                flair_is_bad = True
                                break
                    if flair_is_bad:
                        continue
                
                
                article_data = {
                    'title': entry.title,
                    'link': link,
                    'source': source_domain
                }
                all_found_articles_with_score.append({
                    'article': article_data,
                    'score': score
                })

        else:
            print(f"[Error] Failed to fetch. Server responded with status code: {response.status_code}")
    except Exception as e:
        print(f"[Error] An error occurred while trying to fetch: {e}")

print("\n--- Finished Fetching. Sorting Results... ---")

if not all_found_articles_with_score:
    print("No new articles found matching your criteria today.")
else:
    print(f"Found {len(all_found_articles_with_score)} total new articles. Sorting by score...")
    
    sorted_articles = sorted(all_found_articles_with_score, key=lambda x: x['score'], reverse=True)
    articles_to_send_data = sorted_articles[:MAX_ARTICLES_TO_SEND]
    articles_to_send = [item['article'] for item in articles_to_send_data]
    
    print(f"Sending the Top {len(articles_to_send)} articles...")
    
    for article in articles_to_send:
        print(f"Title: {article['title']}\nLink: {article['link']}\n")
    
    try:
        asyncio.run(send_telegram_messages(articles_to_send))
        
        print(f"Saving {len(articles_to_send)} sent links to database...")
        for article in articles_to_send:
            save_new_link(article['link'])
        print("All sent links saved.")
        
    except Exception as e:
        print(f"An error occurred while running the async sender: {e}")

print("--- Script Finished ---")