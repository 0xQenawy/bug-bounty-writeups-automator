# bug-bounty-writeups-automator
A smart, serverless Python bot that runs on GitHub Actions to fetch, filter, prioritize, and send the most relevant bug bounty write-ups to a Telegram chat every day.

This project goes beyond simple filtering. It uses a priority scoring system and a persistent SQLite database to create a smart queue, ensuring you always read the most important articles first and never see a duplicate.
## Features
- Smart Prioritization (Scoring): Automatically assigns a "score" to each source (ex: PortSwigger articles get 3 points, Reddit gets 1).

- Priority Queue System: Fetches all new articles but only sends the `MAX_ARTICLES_TO_SEND` (ex: Top 3) highest-scoring ones. Lower-scoring articles wait in the queue for the next day.

- Persistent Memory (SQLite): Uses a built-in SQLite database (`writeups.db`) to remember every link it has ever sent, 100% preventing duplicates.

- Auto-Pruning Database: The database automatically cleans itself, removing any links older than 30 days (`PRUNE_AFTER_DAYS`) to stay fast and lightweight.

- Expanded & Smart Filtering:
    - Fetches from 6+ high-quality sources (PortSwigger, Google Project Zero, Intigriti, etc.).

    - Filters by a comprehensive keyword list (KEYWORDS_TO_FIND).

    - Intelligently skips "Question" or "Discussion" posts from Reddit using a flair blocklist.

- Fully Automated & Serverless: Runs on a daily schedule using GitHub Actions. No servers or payments required.

 ## How It Works
 1. Schedule: A cron job in .github/workflows/main.yml triggers the bot (e.g., daily at 07:00 UTC).

 2. Prune: The script first connects to writeups.db and runs prune_old_links() to delete all entries older than 30 days.

 3. Fetch: Fetches the latest posts from all 6+ RSS feeds in the FEEDS_TO_CHECK list.

 4. Filter & Score: It loops through every single article and performs 4 checks:

 > *Check 1 (Memory): Is this link already in the writeups.db? (If yes, Skip).

 > *Check 2 (Keyword): Is there a Keyword in the title? (If no, Skip).

 > *Check 3 (Flair): Is this from Reddit with a "Question" flair? (If yes, Skip).

 > *Check 4 (Score): If it passes all checks, assign it a score based on its source (e.g., 3 points for PortSwigger).

 5. Sort & Select:

 > *The script gathers all new, filtered articles into a master list.

 > *It sorts this list by score (highest to lowest).

 > *It selects only the Top 3 (or MAX_ARTICLES_TO_SEND) from this sorted list.

 6. Send & Save:

 > *The Top 3 articles are sent to your Telegram chat.

 > *Only those 3 links are saved to the writeups.db as "sent."

 7. Commit & Push: The GitHub Action automatically commits and pushes the updated writeups.db file back to your repository, saving the "memory" for the next run.

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

Set Workflow Permissions (CRITICAL STEP):

> *The Action needs permission to git push the database file.

> *Go to Settings > Actions > General.

> *Scroll down to "Workflow permissions".

> *Select the "Read and write permissions" option.

> *Click Save.

Customize (Optional): 
> * Edit get_feeds.py to change `KEYWORDS_TO_FIND`, `SOURCE_SCORES`, or `MAX_ARTICLES_TO_SEND`. 
> * Edit `.github/workflows/workflows.yml` to change the cron schedule.

Enable Actions: 
> * Go to the `"Actions"` tab in your repository. 
> * Click the `"I understand my workflows, go ahead and enable them"` button. 
> * You can trigger a manual run to test it using the `"Run workflow"` button.

## Tech Stack
- python
- GitHub Actions
- SQLite (for persistent memory)
- Libraries: requests, feedparser, python-telegram-bot

  
