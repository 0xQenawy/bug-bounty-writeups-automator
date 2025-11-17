# bug-bounty-writeups-automator
A simple, serverless Python bot that runs on GitHub Actions to fetch, filter, and send relevant bug bounty write-ups to a Telegram chat every day.
## Features
- Fully Automated: Runs on a daily schedule using GitHub Actions.

- Serverless: No need to host it on a VPS or pay for servers.

- Smart Filtering:

- Filters articles by a custom list of keywords (ex: XSS, IDOR, RCE).

- Intelligently skips "Question" or "Discussion" posts from Reddit using a flair blocklist.

- Instant Notifications: Delivers a clean list of new write-ups directly to your Telegram chat.

 ## How It Works
 1. Schedule: A cron job in GitHub Actions (.github/workflows/workflows.yml) triggers the bot every day.
 2. Fetch: The Python script (get_feeds.py) fetches the latest posts from multiple RSS feeds (PortSwigger, Medium, Reddit).
 3. Filter: The script filters all articles based on two criteria:
> * Must contain a keyword from the `KEYWORDS_TO_FIND` list.
> * If from Reddit, must NOT have a flair in the `REDDIT_FLAIRS_TO_BLOCK` list.
 4. Send: The script uses the Telegram Bot API to send the final, filtered list of articles to your specified chat.

 ## Setup (How to use it yourself)
 You can easily fork this repository and set it up for yourself in 5 minutes.

Fork this Repository: Click the "Fork" button at the top right of this page.

Create your Telegram Bot: 
> * Talk to @BotFather on Telegram. 
> * Create a new bot and get your Bot Token. 
> * Start a chat with your new bot (this is important!). 
> * Get your Chat ID (you can get it by sending a message and checking the getUpdates URL, or by talking to @userinfobot).

Add Repository Secrets: 
> * In your forked repository, go to Settings 
> Secrets and variables > Actions. 
> * Click New repository secret and add the following two secrets: 
> * TELEGRAM_BOT_TOKEN: (Your bot token from BotFather) 
> * TELEGRAM_CHAT_ID: (Your personal chat ID)

Customize (Optional): 
> * Edit get_feeds.py to change the KEYWORDS_TO_FIND or REDDIT_FLAIRS_TO_BLOCK lists to match your interests. 
> * Edit .github/workflows/workflows.yml to change the cron schedule.

Enable Actions: 
> * Go to the ***"Actions"*** tab in your repository. 
> * Click the ***"I understand my workflows, go ahead and enable them"*** button. 
> * You can trigger a manual run to test it using the ***"Run workflow"*** button.

## Tech Stack
- python
- GitHub Actions
- Libraries: requests, feedparser, python-telegram-bot

  
