import os
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="India's Got Latent - Analytics",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF0000;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def get_engine():
    return create_engine(
        f"mysql+mysqlconnector://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}@"
        f"{os.getenv('DB_HOST', 'localhost')}/youtube_analytics"
    )

@st.cache_data(ttl=300)
def get_data(query):
    return pd.read_sql(query, get_engine())

def show_metrics(total, positive, neutral, negative):
    cols = st.columns(4)
    metrics = [
        ("Total Comments", total, "#667eea"),
        ("😊 Positive", positive, "#28a745"),
        ("😐 Neutral", neutral, "#f39c12"),
        ("😠 Negative", negative, "#dc3545")
    ]
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}22 0%, {color}44 100%);
                        border: 2px solid {color}; border-radius: 1rem; padding: 1.5rem; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700; color: {color};">{value:,}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">🎬 India\'s Got Latent - YouTube Comment Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time sentiment analysis dashboard</div>', unsafe_allow_html=True)
    
    # Get all videos analyzed
    df_videos = get_data("SELECT DISTINCT video_id FROM fact_comments")
    if df_videos.empty:
        st.warning("No data found. Please run the analysis pipeline first.")
        return
    
    video_id = st.selectbox("Select Video", df_videos['video_id'].tolist())
    
    # Metrics
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
    
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Sentiment Distribution")
        fig = px.pie(sentiment_counts, values='count', names='sentiment',
                     color='sentiment',
                     color_discrete_map={'positive':'#28a745','neutral':'#f39c12','negative':'#dc3545'},
                     hole=0.4)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Top Mentioned Contestants")
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
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No contestant mentions found.")
    
    # Trend
    st.markdown("### Sentiment Trend Over Time")
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
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("All comments are from the same date — no trend to display.")
    
    # Comments table
    st.markdown("### 💬 Top Comments")
    df_comments = get_data(f"""
        SELECT fc.author, fc.processed_text as comment, fc.sentiment, fc.like_count
        FROM fact_comments fc
        WHERE fc.video_id = '{video_id}'
        ORDER BY fc.like_count DESC
        LIMIT 20
    """)
    
    def color_sentiment(val):
        colors = {'positive': 'background-color: #d4edda', 'negative': 'background-color: #f8d7da', 'neutral': 'background-color: #fff3cd'}
        return colors.get(val, '')
    
    styled = df_comments.style.map(color_sentiment, subset=['sentiment'])
    st.dataframe(styled, use_container_width=True, height=500)

if __name__ == "__main__":
    main()