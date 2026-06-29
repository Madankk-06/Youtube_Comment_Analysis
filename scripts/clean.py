import pandas as pd
import re
import emoji

def clean_text(text):
    # Handle NaN, None, or float values
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = emoji.replace_emoji(text, replace='')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    df = pd.read_csv('data/raw_comments.csv')
    
    # Drop rows where text is null before cleaning
    df = df.dropna(subset=['text'])
    
    df['cleaned_text'] = df['text'].apply(clean_text)
    df = df.drop_duplicates(subset=['cleaned_text'])
    df = df[df['cleaned_text'].str.len() > 0]
    
    df.to_csv('data/cleaned_comments.csv', index=False)
    print(f"✅ Cleaned data: {len(df)} comments saved")

if __name__ == "__main__":
    main()