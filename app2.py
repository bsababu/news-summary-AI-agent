import streamlit as st
from bs4 import BeautifulSoup
import requests
import json
from transformers import pipeline


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
        for lin in content_links[6:11]:  # Fetch the first 5 articles
            linkx = lin.find('a', href=True)
            if linkx:
                article = pull_from_web(linkx['href'])
                if "error" not in article:
                    articles.append(article)
    return articles


if st.button("Fetch and Summarize Articles"):
    with st.spinner("Fetching and summarizing articles..."):
        articles = fetch_articles()
        if articles:
            for article in articles:
                st.subheader(article["Title"])
                st.write(article["Summary"])
                st.markdown(f"[Read more]({article['URL']})")
                st.write("---")
        else:
            st.error("No articles found or unable to fetch articles.")