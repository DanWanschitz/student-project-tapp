import praw
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- Reddit API credentials ---
reddit = praw.Reddit(
    client_id="_nhEWXohCEde3YpVpPtkzQ",
    client_secret="tupeb1E-uwj1DViSvdEmVqGFBHa7QQ",
    user_agent="cycling-safety-analysis:v1.0 (by u/party-examination-46)"
)

# --- Choose subreddits and search terms ---
subreddits = [
    "Amsterdam",
    "cycling",
    "bicycling",
    "urbanplanning",
    "bikecommuting",
    "travel",
    "europe",
    "Netherlands"
]
query = [
    "cycling safety Amsterdam",

]



# --- Collect posts ---
posts = []
for sub in subreddits:
    subreddit = reddit.subreddit(sub)
    for submission in subreddit.search(query, limit=100):
        posts.append({
            "subreddit": sub,
            "title": submission.title,
            "text": submission.selftext,
            "score": submission.score,
            "url": submission.url
        })

df = pd.DataFrame(posts)
print(f"Collected {len(df)} posts.")


