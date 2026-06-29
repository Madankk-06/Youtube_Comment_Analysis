import pandas as pd
import nltk
from nltk.corpus import stopwords
from textblob import TextBlob

nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

# Define contestants for India's Got Latent
CONTESTANTS = ['samay raina',
    'raghav',
    'bharti',
    'krushna',
    'malaika',
    'kirron',
    'badshah'
]  # Update with real names

def preprocess(text):
    words = text.split()
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return ' '.join(words)

def get_sentiment(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

def extract_mentions(text):
    return [c for c in CONTESTANTS if c in text]

def main():
    df = pd.read_csv('data/cleaned_comments.csv')
    df['processed_text'] = df['cleaned_text'].apply(preprocess)
    df['sentiment'] = df['processed_text'].apply(get_sentiment)
    df['mentions'] = df['processed_text'].apply(extract_mentions)
    
    df.to_csv('data/analyzed_comments.csv', index=False)
    print(f"✅ Analysis complete: {len(df)} comments processed")
    print(f"Sentiment distribution:\n{df['sentiment'].value_counts()}")

if __name__ == "__main__":
    main()