import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database='youtube_analytics',
        auth_plugin='mysql_native_password'
    )

def parse_datetime(dt_string):
    """Convert YouTube ISO 8601 format to MySQL datetime format"""
    if pd.isna(dt_string):
        return None
    dt = datetime.strptime(str(dt_string), '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def safe_str(val):
    """Convert NaN/None to empty string or actual value"""
    if pd.isna(val):
        return ''
    return str(val)

def safe_int(val):
    """Convert NaN/None to 0 or actual integer"""
    if pd.isna(val):
        return 0
    return int(val)

def load_to_mysql():
    df = pd.read_csv('data/analyzed_comments.csv')
    
    # Drop rows with critical null values
    df = df.dropna(subset=['comment_id', 'video_id'])
    
    # Fill NaN in other columns
    df['author'] = df['author'].fillna('Unknown')
    df['text'] = df['text'].fillna('')
    df['cleaned_text'] = df['cleaned_text'].fillna('')
    df['processed_text'] = df['processed_text'].fillna('')
    df['sentiment'] = df['sentiment'].fillna('neutral')
    df['like_count'] = df['like_count'].fillna(0).astype(int)
    
    # Convert mentions from string representation back to list
    import ast
    df['mentions'] = df['mentions'].apply(
        lambda x: ast.literal_eval(x) if pd.notna(x) else []
    )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Load staging
    print("Loading staging_comments...")
    for _, row in df.iterrows():
        pub_date = parse_datetime(row['published_at'])
        cursor.execute("""
            INSERT INTO staging_comments (comment_id, author, text, like_count, published_at, video_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE text=VALUES(text)
        """, (
            safe_str(row['comment_id']), 
            safe_str(row['author']), 
            safe_str(row['text']),
            safe_int(row['like_count']), 
            pub_date, 
            safe_str(row['video_id'])
        ))
    
    # Populate dim_date
    print("Populating dim_date...")
    unique_dates = df['published_at'].dropna().unique()
    for dt_str in unique_dates:
        pub_date = parse_datetime(dt_str)
        if pub_date:
            dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT IGNORE INTO dim_date (full_date, year, month, day, day_of_week)
                VALUES (%s, %s, %s, %s, %s)
            """, (dt.date(), dt.year, dt.month, dt.day, dt.strftime('%A')))
    
    # Populate dim_contestant
    print("Populating dim_contestant...")
    contestants = ['samay raina', 'raghav', 'bharti', 'krushna', 'malaika', 'kirron', 'badshah']
    for contestant in contestants:
        cursor.execute("""
            INSERT IGNORE INTO dim_contestant (contestant_name, first_seen_date)
            VALUES (%s, CURDATE())
        """, (contestant,))
    
    # Populate fact_comments
    print("Populating fact_comments...")
    for _, row in df.iterrows():
        pub_date = parse_datetime(row['published_at'])
        if pub_date:
            dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT date_id FROM dim_date WHERE full_date = %s", (dt.date(),))
            result = cursor.fetchone()
            if result:
                date_id = result[0]
                cursor.execute("""
                    INSERT INTO fact_comments (comment_id, date_id, video_id, author, sentiment, like_count, processed_text)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE sentiment=VALUES(sentiment)
                """, (
                    safe_str(row['comment_id']), 
                    date_id, 
                    safe_str(row['video_id']), 
                    safe_str(row['author']),
                    safe_str(row['sentiment']), 
                    safe_int(row['like_count']), 
                    safe_str(row['processed_text'])
                ))
    
    # Populate fact_mentions
    print("Populating fact_mentions...")
    for _, row in df.iterrows():
        for mention in row['mentions']:
            cursor.execute("SELECT contestant_id FROM dim_contestant WHERE contestant_name = %s", (mention,))
            result = cursor.fetchone()
            if result:
                contestant_id = result[0]
                cursor.execute("""
                    INSERT INTO fact_mentions (comment_id, contestant_id, mention_count)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE mention_count = mention_count + 1
                """, (safe_str(row['comment_id']), contestant_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Data loaded to MySQL successfully!")

if __name__ == "__main__":
    load_to_mysql()