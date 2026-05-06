import ssl
import urllib.parse
import urllib.request

import feedparser
import streamlit as st


# This function fetches recent papers from arXiv for a chosen topic.
@st.cache_data(ttl=3600)
def fetch_papers(domain, max_results=30):
    try:
        safe_domain = urllib.parse.quote_plus(domain)
        url = (
            "https://export.arxiv.org/api/query?"
            f"search_query=all:{safe_domain}&max_results={int(max_results)}"
        )

        # arXiv increasingly expects a User-Agent; use explicit request first.
        request = urllib.request.Request(url, headers={"User-Agent": "ai-recommender/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            feed = feedparser.parse(response.read())

        # Some environments fail SSL verification; fallback to unverified context.
        if len(feed.entries) == 0 and getattr(feed, "bozo", False):
            error_text = str(getattr(feed, "bozo_exception", ""))
            if "CERTIFICATE_VERIFY_FAILED" in error_text:
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(request, context=context, timeout=20) as response:
                    feed = feedparser.parse(response.read())

        papers = []
        for entry in feed.entries:
            papers.append(
                {
                    "title": entry.get("title", "Untitled").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "link": entry.get("link", ""),
                }
            )
        return papers
    except Exception:
        return []
