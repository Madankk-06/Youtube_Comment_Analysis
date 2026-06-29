# 🎬 YouTube Comment Analytics Dashboard

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.28+-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/MySQL-8.0+-orange.svg" alt="MySQL">
  <img src="https://img.shields.io/badge/YouTube%20Data%20API-v3-green.svg" alt="YouTube API">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <b>AI-powered sentiment analysis dashboard for YouTube comments with real-time data pipeline</b>
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [API Limits](#-api-limits)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **URL Analysis** | Paste any YouTube video URL and get instant analytics |
| 🧠 **Sentiment Analysis** | AI-powered categorization (Positive / Neutral / Negative) |
| 📊 **Interactive Dashboard** | Real-time charts with Plotly & Streamlit |
| 🏆 **Contestant Detection** | Auto-detects mentions of show participants |
| 📅 **Time Trends** | Track sentiment evolution over time |
| 💬 **Top Comments** | Most liked comments with sentiment coloring |
| 🗄️ **MySQL Integration** | Star schema data warehouse for analytics |
| ⚡ **Progress Tracking** | Real-time progress bar during analysis |

---

## 🏗️ Architecture
YouTube Video URL → YouTube API → Extract → Clean → Analyze → MySQL → Dashboard
plain

### Data Pipeline Flow
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Extract   │ →  │    Clean    │ →  │   Analyze   │
│  Comments   │    │Remove URLs, │    │  Sentiment  │
│  (YouTube)  │    │ emojis, dupes│    │ + Mentions  │
└─────────────┘    └─────────────┘    └──────┬──────┘
│
┌────────┴────────┐
▼                 ▼
┌──────────┐      ┌──────────┐
│  MySQL   │      │ Streamlit│
│  (Star   │      │ Dashboard│
│  Schema) │      │ (Plotly) │
└──────────┘      └──────────┘
plain

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Interactive web dashboard |
| **Visualization** | Plotly | Charts & graphs |
| **Backend** | Python 3.10+ | Data processing pipeline |
| **API** | YouTube Data API v3 | Comment extraction |
| **Database** | MySQL 8.0 | Data warehouse (Star Schema) |
| **ORM** | SQLAlchemy | Database connectivity |
| **NLP** | TextBlob | Sentiment analysis |
| **NLP** | NLTK | Stop word removal |
| **Environment** | python-dotenv | Configuration management |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- YouTube Data API v3 Key ([Get one here](https://console.cloud.google.com/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/youtube-comment-analytics.git
cd youtube-comment-analytics
Step 2: Create Virtual Environment
bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
Step 3: Install Dependencies
bash
pip install -r requirements.txt
Step 4: Download NLTK Data
bash
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"
⚙️ Configuration
1. Create .env File
Create a .env file in the project root:
env
# YouTube API Configuration
YOUTUBE_API_KEY=your_youtube_api_key_here

# MySQL Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
🔑 Get YouTube API Key: Google Cloud Console
2. Setup MySQL Database
bash
mysql -u root -p
sql
CREATE DATABASE youtube_analytics;
USE youtube_analytics;
Run the schema script:
bash
mysql -u root -p youtube_analytics < sql/schema.sql
🚀 Usage
Run the Application
bash
streamlit run scripts/app.py
The app will open at http://localhost:8501
How to Use
Paste a YouTube URL in the input field
Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Click "Analyze Video" button
Wait for processing (progress bar shows status)
Extracting comments from YouTube API
Cleaning & preprocessing
Running sentiment analysis
Saving to MySQL
View Dashboard with:
Sentiment distribution (pie chart)
Top mentioned contestants (bar chart)
Sentiment trend over time (line graph)
Top comments table (color-coded)
🗄️ Database Schema
Star Schema Design
sql
-- Dimension: Date
dim_date (
    date_id INT PK,
    full_date DATE,
    year INT,
    month INT,
    day INT,
    day_of_week VARCHAR(20)
)

-- Dimension: Contestant
dim_contestant (
    contestant_id INT PK,
    contestant_name VARCHAR(255),
    first_seen_date DATE
)

-- Fact: Comments
fact_comments (
    comment_id VARCHAR(100) PK,
    date_id INT FK,
    video_id VARCHAR(50),
    author VARCHAR(255),
    sentiment VARCHAR(20),
    like_count INT,
    processed_text TEXT
)

-- Fact: Mentions (Bridge Table)
fact_mentions (
    mention_id INT PK,
    comment_id VARCHAR(100) FK,
    contestant_id INT FK,
    mention_count INT DEFAULT 1
)

-- Staging Table
staging_comments (
    comment_id VARCHAR(100) PK,
    author VARCHAR(255),
    text TEXT,
    like_count INT,
    published_at DATETIME,
    video_id VARCHAR(50),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
⚠️ API Limits
Table
Limit	Value
Daily Quota	10,000 units
Cost per request	1 unit per 100 comments
Max comments fetched	~10,000 per day
💡 Tip: For videos with 15K+ comments, only the most recent ~7K-10K will be fetched due to API limits.
📸 Screenshots
<p align="center">
  <img src="screenshot-input.jpeg" alt="Input Page" width="700">
</p>
<p align="center">
  <img src="screenshot-Analysis.jpeg" alt="Results Dashboard" width="700">
</p>
<p align="center">
  <img src="screenshot-Sentiment.jpeg" alt="Results Dashboard" width="700">
</p>
📁 Project Structure
plain
youtube-comment-analytics/
│
├── scripts/
│   ├── app.py              ← Main Streamlit app (Pipeline + Dashboard)
│   ├── extract.py          ← YouTube API comment extraction
│   ├── clean.py            ← Data cleaning & preprocessing
│   ├── analyze.py          ← Sentiment analysis & NLP
│   ├── load_to_mysql.py    ← ETL to MySQL
│   └── dashboard.py        ← Standalone dashboard viewer
│
├── sql/
│   └── schema.sql          ← MySQL database schema
│
├── data/                   ← CSV files (auto-generated)
│
├── assets/                 ← Screenshots & images
│
├── .env                    ← Environment variables (not in git)
├── .gitignore              ← Git ignore rules
├── requirements.txt        ← Python dependencies
└── README.md               ← This file

🤝 Contributing
Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request
📄 License
This project is licensed under the MIT License.
<p align="center">
  Made with ❤️ by <a href="https://github.com/yourusername">Your Name</a>
</p>
```
GITHUB_PUSH_GUIDE.md
Markdown
Copy
Code
Preview
# 🚀 GitHub Push Guide

## Step 1: Install Git

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git
Step 2: Configure Git
bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
Step 3: Create GitHub Repository
Go to GitHub
Click New Repository
Name: youtube-comment-analytics
Description: "AI-powered YouTube comment sentiment analysis dashboard"
Choose Public or Private
DO NOT initialize with README
Click Create repository
Step 4: Prepare Project Structure
bash
cd /path/to/youtube-comments-dashboard

mkdir -p scripts sql data assets

# Move your Python scripts to scripts/
mv app.py scripts/
# (Keep extract.py, clean.py, analyze.py, load_to_mysql.py, dashboard.py in scripts/)

# Copy files to proper locations
cp schema.sql sql/
cp README.md .
cp .gitignore .
cp requirements.txt .
Step 5: Initialize & Push
bash
git init
git add .
git commit -m "Initial commit: YouTube Comment Analytics Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-comment-analytics.git
git push -u origin main
Done!
Visit: https://github.com/YOUR_USERNAME/youtube-comment-analytics
plain

---

## 📋 Quick Setup Checklist

| Step | Action |
|------|--------|
| 1 | Copy `app.py` to `scripts/` folder |
| 2 | Copy `schema.sql` to `sql/` folder |
| 3 | Copy `README.md`, `.gitignore`, `requirements.txt` to root |
| 4 | Create `assets/` folder for screenshots |
| 5 | Make sure `.env` has NO `VIDEO_ID` line |
| 6 | Run `git init`, `git add .`, `git commit`, `git push` |

All files are ready! Let me know if you need anything else.