import streamlit as st
import os
import re
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime
import emoji
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob

# Page config
st.set_page_config(
    page_title="YouTube Comment Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - FIXED UI
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    .stTextInput > label {
        display: none !important;
    }
    .stTextInput > div {
        padding-top: 0 !important;
    }
    
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF4444;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #AAAAAA;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Input container - NO empty bars */
    .input-container {
        background: #2D2D2D;
        border-radius: 1rem;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 800px;
        border: 1px solid #444;
    }
    
    /* Clean input field */
    .stTextInput > div > div > input {
        background-color: #1A1A1A !important;
        color: white !important;
        border: 2px solid #444 !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #FF4444 !important;
        box-shadow: 0 0 0 2px rgba(255,68,68,0.2) !important;
    }
    
    /* Button styling - CENTERED */
    .stButton {
        display: flex;
        justify-content: center;
    }
    .stButton > button {
        background: linear-gradient(90deg, #FF4444 0%, #CC0000 100%);
        color: white;
        border: none;
        padding: 0.75rem 3rem;
        border-radius: 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        min-width: 200px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(255,68,68,0.3);
    }
    
    /* Info box */
    .info-box {
        background-color: #1E3A5F;
        border-left: 4px solid #4A90D9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #FFFFFF !important;
    }
    
    /* Success box */
    .success-box {
        background-color: #1E4D2B;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #FFFFFF !important;
    }
    
    /* Section headers */
    h3 {
        color: #FFFFFF !important;
        margin-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

load_dotenv()

API_KEY = os.getenv('YOUTUBE_API_KEY')
CONTESTANTS = ['samay', 'raina', 'badshah', 'malaika', 'kirron', 'bharti', 'krushna', 'raghav']

def get_engine():
    return create_engine(
        f"mysql+mysqlconnector://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@"
        f"{os.getenv('DB_HOST', 'localhost')}/youtube_analytics"
    )

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\s?]+)',
        r'youtube\.com/shorts/([^&\s?]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_comments(video_id, max_results=100):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    comments = []
    request = youtube.commentThreads().list(
        part='snippet', videoId=video_id,
        maxResults=max_results, textFormat='plainText'
    )
    total_fetched = 0
    max_allowed = 10000
    
    while request and total_fetched < max_allowed:
        try:
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
                total_fetched += 1
            request = youtube.commentThreads().list_next(request, response)
        except Exception as e:
            break
    
    return pd.DataFrame(comments), total_fetched

def clean_text(text):
    if pd.isna(text) or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def analyze_data(df):
    stop_words = set(stopwords.words('english'))
    
    def preprocess(text):
        words = text.split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        return ' '.join(words)
    
    def get_sentiment(text):
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.1: return 'positive'
        elif polarity < -0.1: return 'negative'
        else: return 'neutral'
    
    def extract_mentions(text):
        return [c for c in CONTESTANTS if c in text]
    
    df['processed_text'] = df['cleaned_text'].apply(preprocess)
    df['sentiment'] = df['processed_text'].apply(get_sentiment)
    df['mentions'] = df['processed_text'].apply(extract_mentions)
    return df

def parse_datetime(dt_string):
    if pd.isna(dt_string): return None
    dt = datetime.strptime(str(dt_string), '%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def safe_str(val):
    return '' if pd.isna(val) else str(val)

def safe_int(val):
    return 0 if pd.isna(val) else int(val)

def load_to_mysql(df, video_id):
    import mysql.connector
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database='youtube_analytics',
        auth_plugin='mysql_native_password'
    )
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fact_mentions WHERE comment_id IN (SELECT comment_id FROM fact_comments WHERE video_id = %s)", (video_id,))
    cursor.execute("DELETE FROM fact_comments WHERE video_id = %s", (video_id,))
    cursor.execute("DELETE FROM staging_comments WHERE video_id = %s", (video_id,))
    conn.commit()
    
    df = df.dropna(subset=['comment_id'])
    df['author'] = df['author'].fillna('Unknown')
    df['text'] = df['text'].fillna('')
    df['cleaned_text'] = df['cleaned_text'].fillna('')
    df['processed_text'] = df['processed_text'].fillna('')
    df['sentiment'] = df['sentiment'].fillna('neutral')
    df['like_count'] = df['like_count'].fillna(0).astype(int)
    
    for _, row in df.iterrows():
        pub_date = parse_datetime(row['published_at'])
        cursor.execute("""
            INSERT INTO staging_comments VALUES (%s,%s,%s,%s,%s,%s,DEFAULT)
            ON DUPLICATE KEY UPDATE text=VALUES(text)
        """, (safe_str(row['comment_id']), safe_str(row['author']), safe_str(row['text']),
              safe_int(row['like_count']), pub_date, safe_str(row['video_id'])))
    
    for _, row in df.iterrows():
        pub_date = parse_datetime(row['published_at'])
        if pub_date:
            dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT IGNORE INTO dim_date VALUES (DEFAULT,%s,%s,%s,%s,%s)",
                (dt.date(), dt.year, dt.month, dt.day, dt.strftime('%A')))
    
    for contestant in CONTESTANTS:
        cursor.execute("INSERT IGNORE INTO dim_contestant VALUES (DEFAULT,%s,CURDATE())", (contestant,))
    
    for _, row in df.iterrows():
        pub_date = parse_datetime(row['published_at'])
        if pub_date:
            dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT date_id FROM dim_date WHERE full_date = %s", (dt.date(),))
            result = cursor.fetchone()
            if result:
                date_id = result[0]
                cursor.execute("""
                    INSERT INTO fact_comments VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE sentiment=VALUES(sentiment)
                """, (safe_str(row['comment_id']), date_id, safe_str(row['video_id']),
                      safe_str(row['author']), safe_str(row['sentiment']),
                      safe_int(row['like_count']), safe_str(row['processed_text'])))
    
    for _, row in df.iterrows():
        for mention in row['mentions']:
            cursor.execute("SELECT contestant_id FROM dim_contestant WHERE contestant_name = %s", (mention,))
            result = cursor.fetchone()
            if result:
                cursor.execute("""
                    INSERT INTO fact_mentions VALUES (DEFAULT,%s,%s,1)
                    ON DUPLICATE KEY UPDATE mention_count = mention_count + 1
                """, (safe_str(row['comment_id']), result[0]))
    
    conn.commit()
    cursor.close()
    conn.close()

@st.cache_data(ttl=300)
def get_data(query):
    return pd.read_sql(query, get_engine())

def show_metrics(total, positive, neutral, negative):
    cols = st.columns(4)
    metrics = [
        ("📊 Total Comments", total, "#4A90D9"),
        ("😊 Positive", positive, "#28a745"),
        ("😐 Neutral", neutral, "#f39c12"),
        ("😠 Negative", negative, "#dc3545")
    ]
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}33 0%, {color}66 100%);
                        border: 2px solid {color}; border-radius: 1rem; padding: 1.5rem; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700; color: {color};">{value:,}</div>
                <div style="font-size: 0.9rem; color: #FFFFFF; margin-top: 0.5rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def show_dashboard(video_id):
    st.markdown("---")
    st.markdown('<div class="main-header">📊 Analysis Results</div>', unsafe_allow_html=True)
    
    total = get_data(f"SELECT COUNT(*) as c FROM fact_comments WHERE video_id='{video_id}'").iloc[0]['c']
    sentiment_counts = get_data(f"""
        SELECT sentiment, COUNT(*) as count 
        FROM fact_comments 
        WHERE video_id='{video_id}'
        GROUP BY sentiment
    """)
    pos = sentiment_counts[sentiment_counts['sentiment']=='positive']['count'].sum() if 'positive' in sentiment_counts['sentiment'].values else 0
    neu = sentiment_counts[sentiment_counts['sentiment']=='neutral']['count'].sum() if 'neutral' in sentiment_counts['sentiment'].values else 0
    neg = sentiment_counts[sentiment_counts['sentiment']=='negative']['count'].sum() if 'negative' in sentiment_counts['sentiment'].values else 0
    
    show_metrics(int(total), int(pos), int(neu), int(neg))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 Sentiment Distribution")
        fig = px.pie(sentiment_counts, values='count', names='sentiment',
                     color='sentiment',
                     color_discrete_map={'positive':'#28a745','neutral':'#f39c12','negative':'#dc3545'},
                     hole=0.4)
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🏆 Top Mentioned Contestants")
        df_mentions = get_data(f"""
            SELECT c.contestant_name, SUM(fm.mention_count) as mentions
            FROM fact_mentions fm
            JOIN dim_contestant c ON fm.contestant_id = c.contestant_id
            JOIN fact_comments fc ON fm.comment_id = fc.comment_id
            WHERE fc.video_id = '{video_id}'
            GROUP BY c.contestant_name
            ORDER BY mentions DESC
            LIMIT 10
        """)
        if not df_mentions.empty:
            fig2 = px.bar(df_mentions, x='contestant_name', y='mentions',
                          color='mentions', color_continuous_scale='Reds')
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
                yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No contestant mentions found in this video's comments.")
    
    st.markdown("### 📅 Sentiment Trend Over Time")
    df_trend = get_data(f"""
        SELECT d.full_date, fc.sentiment, COUNT(*) as count
        FROM fact_comments fc
        JOIN dim_date d ON fc.date_id = d.date_id
        WHERE fc.video_id = '{video_id}'
        GROUP BY d.full_date, fc.sentiment
        ORDER BY d.full_date
    """)
    if not df_trend.empty and df_trend['full_date'].nunique() > 1:
        fig3 = px.line(df_trend, x='full_date', y='count', color='sentiment',
                       color_discrete_map={'positive':'#28a745','neutral':'#f39c12','negative':'#dc3545'})
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white')),
            yaxis=dict(title_font=dict(color='white'), tickfont=dict(color='white'))
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("All comments are from the same date — no trend to display.")
    
    st.markdown("### 💬 Top Comments")
    df_comments = get_data(f"""
        SELECT fc.author, fc.processed_text as comment, fc.sentiment, fc.like_count
        FROM fact_comments fc
        WHERE fc.video_id = '{video_id}'
        ORDER BY fc.like_count DESC
        LIMIT 20
    """)
    
    def color_sentiment(val):
        colors = {'positive': 'background-color: #1E4D2B; color: white', 
                  'negative': 'background-color: #5C1E1E; color: white', 
                  'neutral': 'background-color: #5C4B1E; color: white'}
        return colors.get(val, '')
    
    styled = df_comments.style.map(color_sentiment, subset=['sentiment'])
    st.dataframe(styled, use_container_width=True, height=500)

def main():
    st.markdown('<div class="main-header">🎬 YouTube Comment Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Paste any YouTube video URL to analyze comments with AI-powered sentiment analysis</div>', unsafe_allow_html=True)
    
    # CLEAN INPUT SECTION - No empty bars
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # Centered input
    _, col, _ = st.columns([1, 6, 1])
    with col:
        video_url = st.text_input(
            "url_input",  # Internal label (hidden by CSS)
            placeholder="Paste YouTube URL here...",
            label_visibility="collapsed"
        )
    
    # Centered button
    _, btn_col, _ = st.columns([2, 2, 2])
    with btn_col:
        analyze_btn = st.button("🚀 Analyze Video", type="primary", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if analyze_btn and video_url:
        video_id = extract_video_id(video_url)
        
        if not video_id:
            st.error("❌ Invalid YouTube URL. Please paste a valid link like: https://www.youtube.com/watch?v=...")
            return
        
        if not API_KEY:
            st.error("❌ YouTube API Key not found. Check your .env file.")
            return
        
        progress_bar = st.progress(0)
        status = st.empty()
        
        status.markdown('<div class="info-box">⏳ Fetching comments from YouTube API...</div>', unsafe_allow_html=True)
        df, fetched = get_comments(video_id)
        progress_bar.progress(30)
        st.markdown(f'<div class="info-box">📥 Fetched <strong>{fetched:,}</strong> comments (YouTube API limit may apply for videos with 10K+ comments)</div>', unsafe_allow_html=True)
        
        status.markdown('<div class="info-box">🧹 Cleaning & preprocessing comments...</div>', unsafe_allow_html=True)
        df = df.dropna(subset=['text'])
        df['cleaned_text'] = df['text'].apply(clean_text)
        df = df.drop_duplicates(subset=['cleaned_text'])
        df = df[df['cleaned_text'].str.len() > 0]
        progress_bar.progress(60)
        
        status.markdown('<div class="info-box">🧠 Running sentiment analysis & detecting mentions...</div>', unsafe_allow_html=True)
        df = analyze_data(df)
        progress_bar.progress(85)
        
        status.markdown('<div class="info-box">💾 Saving to MySQL database...</div>', unsafe_allow_html=True)
        load_to_mysql(df, video_id)
        progress_bar.progress(100)
        
        status.empty()
        progress_bar.empty()
        
        st.markdown(f"""
        <div class="success-box">
            ✅ <strong>Analysis Complete!</strong> {len(df):,} comments processed successfully.
        </div>
        """, unsafe_allow_html=True)
        
        show_dashboard(video_id)
    
    elif analyze_btn and not video_url:
        st.warning("⚠️ Please enter a YouTube URL first.")

if __name__ == "__main__":
    main()