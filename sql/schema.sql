-- Create database
CREATE DATABASE IF NOT EXISTS youtube_analytics;
USE youtube_analytics;

-- Staging table for raw comments
CREATE TABLE IF NOT EXISTS staging_comments (
    comment_id VARCHAR(100) PRIMARY KEY,
    author VARCHAR(255),
    text TEXT,
    like_count INT,
    published_at DATETIME,
    video_id VARCHAR(50),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Contestant
CREATE TABLE IF NOT EXISTS dim_contestant (
    contestant_id INT AUTO_INCREMENT PRIMARY KEY,
    contestant_name VARCHAR(255) NOT NULL,
    first_seen_date DATE,
    UNIQUE KEY uk_name (contestant_name)
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT AUTO_INCREMENT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT,
    month INT,
    day INT,
    day_of_week VARCHAR(20),
    UNIQUE KEY uk_date (full_date)
);

-- Fact: Comments
CREATE TABLE IF NOT EXISTS fact_comments (
    comment_id VARCHAR(100) PRIMARY KEY,
    date_id INT,
    video_id VARCHAR(50),
    author VARCHAR(255),
    sentiment VARCHAR(20),
    like_count INT,
    processed_text TEXT,
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- Fact: Mentions (bridge table for contestant mentions)
CREATE TABLE IF NOT EXISTS fact_mentions (
    mention_id INT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(100),
    contestant_id INT,
    mention_count INT DEFAULT 1,
    FOREIGN KEY (comment_id) REFERENCES fact_comments(comment_id),
    FOREIGN KEY (contestant_id) REFERENCES dim_contestant(contestant_id)
);