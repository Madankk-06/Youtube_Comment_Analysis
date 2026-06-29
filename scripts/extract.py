import os
from googleapiclient.discovery import build
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('YOUTUBE_API_KEY')
VIDEO_ID = os.getenv('VIDEO_ID')

if not API_KEY or not VIDEO_ID:
    raise ValueError("Missing API_KEY or VIDEO_ID in .env file")

youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_comments(video_id, max_results=100):
    comments = []
    request = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=max_results,
        textFormat='plainText'
    )
    
    while request:
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'comment_id': item['id'],
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'like_count': comment['likeCount'],
                'published_at': comment['publishedAt'],
                'video_id': video_id
            })
        request = youtube.commentThreads().list_next(request, response)
    
    return pd.DataFrame(comments)

if __name__ == "__main__":
    print(f"Extracting comments for video: {VIDEO_ID}")
    df = get_comments(VIDEO_ID)
    
    # Save to data folder
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/raw_comments.csv', index=False)
    
    print(f"✅ Success! Extracted {len(df)} comments")
    print(f"📁 Saved to: data/raw_comments.csv")