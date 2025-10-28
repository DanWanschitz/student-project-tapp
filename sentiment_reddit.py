import praw
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- Reddit API credentials ---
reddit = praw.Reddit(
    client_id="_nhEWXohCEde3YpVpPtkzQ",
    client_secret="tupeb1E-uwj1DViSvdEmVqGFBHa7QQ",
    user_agent="cycling-safety-analysis:v1.0 (by u/party-examination-46)"
)

import pandas as pd
import time
from datetime import datetime

# --- Improved subreddits and search terms ---
subreddits = [
    "Amsterdam",
    "cycling", 
    "bicycling",
    "bikecommuting",
    "Netherlands",
    "urbanplanning",
    "CityCycling",  # Added relevant cycling subreddit
    "biketouring",  # May have Amsterdam discussions
    "thenetherlands"  # More specific than Netherlands
]

# Simplified queries - Reddit search is often better with simpler terms
queries = [
    "Amsterdam cycling",
    "Amsterdam bike", 
    "Amsterdam safety",
    "bike lane Amsterdam",
    "cycling Amsterdam"
]

# Enhanced keywords for better matching
keywords = [
    "amsterdam", "cycling", "bike", "bicycle", "safety", "dangerous", "safe", 
    "accident", "accidents", "crash", "crashes", "lane", "lanes", "bikelane", 
    "bikelanes", "bike lane", "cycle lane", "traffic", "cars", "pedestrian",
    "infrastructure", "separated", "protected", "scary", "confident", "fear",
    "comfortable", "stress", "helmet", "visibility", "intersection", "roundabout"
]

# --- Improved data collection ---
posts = []
seen_ids = set()

def contains_amsterdam_cycling_content(text):
    """More sophisticated content filtering"""
    text_lower = text.lower()
    
    # Must mention Amsterdam (or common abbreviations)
    amsterdam_terms = ["amsterdam", "ams", "dam"]
    has_amsterdam = any(term in text_lower for term in amsterdam_terms)
    
    # Must mention cycling/biking
    cycling_terms = ["cycling", "bike", "bicycle", "biking", "cycle", "biked", "cycle lane", "infrastructure", "intersection", "traffic light", "separated", "protected", "path"]
    has_cycling = any(term in text_lower for term in cycling_terms)

    # Must mention safety attitudes or conditions
    safety_terms = ["safe", "accident", "unsafe", "dangerous", "nervous", "stressful", "enjoyable", "relaxed", "crash", "safety", "stress", "fear", "scary", "collision", "close call", "helmet", "visibility", "confident", "comfortable", "visible", "near miss"]
    has_safety = any(term in text_lower for term in safety_terms)
    
    return has_amsterdam and has_cycling and has_safety

for sub in subreddits:
    print(f"Processing {sub}...")
    subreddit = reddit.subreddit(sub)
    
    search_found = 0
    fallback_found = 0
    
    # Try multiple individual queries instead of OR combination
    for individual_query in queries:
        try:
            for submission in subreddit.search(individual_query, limit=50, time_filter='year'):
                if submission.id in seen_ids:
                    continue
                    
                # Additional content validation
                full_text = (submission.title or "") + " " + (submission.selftext or "")
                if contains_amsterdam_cycling_content(full_text):
                    posts.append({
                        "subreddit": sub,
                        "title": submission.title,
                        "text": submission.selftext,
                        "score": submission.score,
                        "url": submission.url,
                        "created_utc": submission.created_utc,
                        "num_comments": submission.num_comments,
                        "query_used": individual_query,
                        "method": "search"
                    })
                    seen_ids.add(submission.id)
                    search_found += 1
                    
        except Exception as e:
            print(f"Search error for {sub} with query '{individual_query}': {e}")
        
        # Small delay to be respectful to Reddit's API
        time.sleep(0.5)
    
    # Enhanced fallback approach
    if search_found < 5:  # Still do fallback even if some search results found
        try:
            # Try both 'new' and 'hot' sorting
            for sort_method in ['new', 'hot']:
                submission_generator = subreddit.new(limit=300) if sort_method == 'new' else subreddit.hot(limit=100)
                
                for submission in submission_generator:
                    if submission.id in seen_ids:
                        continue
                    
                    full_text = (submission.title or "") + " " + (submission.selftext or "")
                    
                    if contains_amsterdam_cycling_content(full_text):
                        posts.append({
                            "subreddit": sub,
                            "title": submission.title,
                            "text": submission.selftext,
                            "score": submission.score,
                            "url": submission.url,
                            "created_utc": submission.created_utc,
                            "num_comments": submission.num_comments,
                            "query_used": "fallback_" + sort_method,
                            "method": "fallback"
                        })
                        seen_ids.add(submission.id)
                        fallback_found += 1
                        
        except Exception as e:
            print(f"Fallback scan error for {sub}: {e}")
    
    print(f"{sub}: search_found={search_found}, fallback_found={fallback_found}")
    time.sleep(1)  # Be respectful to Reddit's API

# --- Enhanced data processing ---
df = pd.DataFrame(posts)
print(f"Collected {len(df)} posts total.")

if len(df) > 0:
    # Add datetime column
    df['created_date'] = pd.to_datetime(df['created_utc'], unit='s')
    
    # Remove duplicates based on title similarity (optional)
    # df = df.drop_duplicates(subset=['title'], keep='first')
    
    # Sort by score and date
    df = df.sort_values(['score', 'created_date'], ascending=[False, False])
    
    print(f"Posts by subreddit:")
    print(df['subreddit'].value_counts())
    
    print(f"\nPosts by method:")
    print(df['method'].value_counts())
    
    # Save intermediate results
    df.to_csv('amsterdam_cycling_posts.csv', index=False)
    print("Data saved to amsterdam_cycling_posts.csv")
else:
    print("No posts found. Consider:")
    print("1. Checking your Reddit API credentials")
    print("2. Expanding time_filter to 'all'")
    print("3. Trying broader keywords")