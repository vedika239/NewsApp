# 📰 AI-Powered News Aggregator & Fake News Detection System

An AI-driven web application built with **Flask** that aggregates real-time news, personalizes content based on user interests, provides AI-powered news search, and verifies news authenticity using **Perplexity AI** and Machine Learning.

---

## 🚀 Features

### 🔐 User Authentication
- User registration and login
- Secure password hashing
- Session-based authentication using Flask-Login

### 🗂 Personalized News Feed
- Users select preferred news niches
- News fetched automatically from NewsAPI
- Duplicate articles avoided using source URLs

### 🌐 Real-Time News Aggregation
- Live news from NewsAPI
- Category-based and keyword-based filtering
- Country-specific news support

### 🤖 AI News Bot
- AI-assisted real-time news search
- Supports:
  - Keywords
  - Niche/category
  - Date-based search
  - Year-based search
- Intelligent fallback strategy for better results

### 🧠 Fake News Detection
- Uses **Perplexity AI** for fact-checking
- Classifies news into:
  - Likely Real
  - Likely Fake / Misleading
  - Unclear / Needs Verification
- Confidence score and explanation included

### 💬 Comments System
- Public and private comments
- Comments linked to news articles
- Timestamped user interactions

---

## 🛠 Tech Stack

| Layer | Technology |
|-----|-----------|
| Backend | Flask |
| Database | SQLite + SQLAlchemy |
| Authentication | Flask-Login |
| AI APIs | NewsAPI, Perplexity AI |
| Machine Learning | Scikit-learn |
| Frontend | HTML (Jinja Templates) |

---

## 📂 Project Structure
news_app/
│
├── app.py
├── models.py
├── news_api_client.py
├── news_search.py
├── ai_news_bot.py
├── perplexity_news_verifier.py
├── fake_news_detector.py
│
├── templates/
│ ├── login.html
│ ├── register.html
│ ├── news_list.html
│ ├── news_detail.html
│ └── ai_bot.html
│
├── instance/
│ └── news_app.db
│
├── requirements.txt
└── README.md
