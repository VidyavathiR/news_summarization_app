import streamlit as st
import requests
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer  # ✅ Sentiment Analysis
from nltk import download
from langdetect import detect, DetectorFactory
from gtts import gTTS  
import tempfile  
from deep_translator import GoogleTranslator  # For translation

# ✅ Download necessary data
download('vader_lexicon')  

DetectorFactory.seed = 0  # Fixes inconsistent language detection

# ✅ News API URL (Replace with your API key)
NEWS_API_KEY = "2f40e6f4e1c84a18ac697923ff00e683"
NEWS_API_URL = f"https://newsapi.org/v2/everything?q={{query}}&apiKey={NEWS_API_KEY}"

# Initialize Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# Function to clean HTML
def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip() if text else "No content available."

# Function to summarize text
def summarize_text(text, max_words=25):
    text = clean_html(text).split("…")[0]  
    sentences = sent_tokenize(text)  

    if not sentences:
        return "No summary available."

    words = sentences[0].split()  
    return " ".join(words[:max_words]) + "..." if len(words) > max_words else sentences[0]

# Function to analyze sentiment
def analyze_sentiment(text):
    sentiment_score = sia.polarity_scores(text)['compound']
    if sentiment_score >= 0.05:
        return "Positive 😊"
    elif sentiment_score <= -0.05:
        return "Negative 😡"
    else:
        return "Neutral 😐"

# Function to fetch top 10 English news articles
def fetch_news(company):
    response = requests.get(NEWS_API_URL.format(query=company))

    if response.status_code != 200:
        return [{"title": "Error", "summary": "Failed to fetch news"}]

    articles = response.json().get("articles", [])
    processed_articles = []
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}  # ✅ For comparative analysis

    for article in articles:
        title = article.get("title", "No title available")
        content = article.get("content") or article.get("description") or "No content available"

        # **Filter only English articles**
        try:
            if detect(title) != "en":
                continue
        except:
            continue  

        summary = summarize_text(content, max_words=25)  

        # **Ignore articles with irrelevant content**
        if "Content not available." in summary or len(summary) < 10:
            continue  

        sentiment = analyze_sentiment(summary)  # ✅ Get sentiment analysis
        sentiment_counts[sentiment.split()[0]] += 1  # ✅ Update count

        processed_articles.append({"title": title, "summary": summary, "sentiment": sentiment})

        if len(processed_articles) == 10:  # Limit to 10 articles
            break  

    return processed_articles, sentiment_counts  # ✅ Return sentiment counts too

# Function to generate Hindi audio
def generate_hindi_audio(text):
    """Translates English summary to Hindi and generates speech."""
    hindi_text = GoogleTranslator(source="en", target="hi").translate(text)  # Translate to Hindi
    tts = gTTS(hindi_text, lang="hi")  
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")  
    tts.save(temp_file.name)  
    return temp_file.name  

# ✅ STREAMLIT UI
st.title("📰 News Summarizer with Hindi Audio 🎙️")

company = st.text_input("Enter a topic (e.g., Tesla, AI, Bitcoin):")

if st.button("Fetch News"):
    if company:
        news_articles, sentiment_counts = fetch_news(company)

        if news_articles and news_articles[0]["title"] == "Error":
            st.error("Failed to fetch news. Check your API key!")
        else:
            # ✅ Display Comparative Sentiment Analysis
            st.subheader("📊 Sentiment Analysis Overview")
            st.write(f"**Positive Articles:** {sentiment_counts['Positive']} 😊")
            st.write(f"**Negative Articles:** {sentiment_counts['Negative']} 😡")
            st.write(f"**Neutral Articles:** {sentiment_counts['Neutral']} 😐")
            st.divider()

            for article in news_articles:
                st.subheader(article["title"])  # Title in English
                st.write(f"**Summary:** {article['summary']}")  # Summary in English
                st.write(f"**Sentiment:** {article['sentiment']}")  # ✅ Show Sentiment

                # Generate and play Hindi audio
                hindi_audio_path = generate_hindi_audio(article["summary"])
                st.audio(hindi_audio_path, format="audio/mp3")  

                st.divider()  # Adds a line separator
    else:
        st.warning("Please enter a company or topic.")
