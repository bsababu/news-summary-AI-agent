import streamlit as st
from bs4 import BeautifulSoup
import requests
import json
from transformers import pipeline
import schedule
import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


st.title("📰 News Summarizer")
st.write("Fetch and summarize the latest articles from [The New Times Rwanda](https://www.newtimes.co.rw/rwanda).")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

root = "https://www.newtimes.co.rw/rwanda"


def pull_from_web(url):
    try:
        urll = requests.get(url)
        sup = BeautifulSoup(urll.text, 'html.parser')
        content_script = sup.find('script', type='application/ld+json')
        if content_script:
            json_cont = json.loads(content_script.string)
            article_body = json_cont.get('articleBody', None)
            article_title = json_cont.get('headline', None)
            if article_body:
                summary = summarizer(article_body, max_length=130, min_length=30, do_sample=False)
                return {
                    "Title": article_title,
                    "Summary": summary[0].get('summary_text'),
                    "URL": url
                }
    except Exception as e:
        return {"error": f"Unable to retrieve article: {str(e)}"}


def fetch_articles():
    articles = []
    urll = requests.get(root)
    sup = BeautifulSoup(urll.text, 'html.parser')
    content_links = sup.find_all('div', class_="article-title")
    if content_links:
        for lin in content_links[6:11]:
            linkx = lin.find('a', href=True)
            if linkx:
                article = pull_from_web(linkx['href'])
                if "error" not in article:
                    articles.append(article)
    return articles

def send_email(email, subject, body):
    sender_email = "oscobosco@gmail.com"
    sender_password = "otle wlex iezf hpzc"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        st.success(f"Email sent to {email}!")
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")

def fetch_summarize_and_display():
    articles = fetch_articles()
    if articles:
        st.subheader("Latest Articles")
        for article in articles:
            st.write(f"**Title:** {article['Title']}")
            st.write(f"**Summary:** {article['Summary']}")
            st.markdown(f"[Read more]({article['URL']})")
            st.write("---")

        email_body = "Here are the latest article summaries:\n\n"
        for article in articles:
            email_body += f"Title: {article['Title']}\n"
            email_body += f"Summary: {article['Summary']}\n"
            email_body += f"Read more: {article['URL']}\n\n"

        return email_body
    else:
        st.warning("No articles found.")
        return None


with st.sidebar:
    st.header("News Summarizer Agent")
    email = st.text_input("Enter your email to receive hourly summaries:")
    search_term = st.text_input("Search for articles by keyword:")
    search_button = st.button("Search")

if email:
    st.success(f"Email registered: {email}")
    if st.button("Start Hourly Summaries"):
        st.write("Fetching and summarizing articles...")
        email_body = fetch_summarize_and_display()

        if email_body:
            send_email(email, "Latest Article Summaries", email_body)

        # Schedule
        schedule.every(1).hour.do(fetch_summarize_and_display)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=run_scheduler, daemon=True).start()

# Handle search functionality
if search_button and search_term:
    articles = fetch_articles()
    filtered_articles = [article for article in articles if search_term.lower() in article["Title"].lower()]
    if filtered_articles:
        st.subheader("Search Results")
        for article in filtered_articles:
            st.write(f"**Title:** {article['Title']}")
            st.write(f"**Summary:** {article['Summary']}")
            st.markdown(f"[Read more]({article['URL']})")
            st.write("---")
    else:
        st.write("No articles found matching your search term.")