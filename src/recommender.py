from collections import Counter

import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity


# This function loads and caches the embedding model so it is reused across reruns.
@st.cache_resource
def load_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


# This function finds the most relevant papers by comparing summaries to the user query.
def get_top_papers(papers, user_query, top_n=5):
    if not papers:
        return []

    summaries = [paper.get("summary", "") for paper in papers]
    model = load_embedding_model()
    if model is None:
        # Fallback ranking if embedding model is unavailable in the local environment.
        query_words = set(user_query.lower().split())
        scored = []
        for paper in papers:
            summary_words = set(paper.get("summary", "").lower().split())
            score = len(query_words.intersection(summary_words))
            scored.append((score, paper))
        return [paper for _, paper in sorted(scored, key=lambda x: x[0], reverse=True)[:top_n]]

    embeddings = model.encode([user_query] + summaries)
    query_embedding = embeddings[0]
    paper_embeddings = embeddings[1:]

    similarities = cosine_similarity([query_embedding], paper_embeddings)[0]
    ranked = sorted(zip(similarities, papers), key=lambda x: x[0], reverse=True)

    top_papers = []
    for score, paper in ranked[:top_n]:
        paper_copy = dict(paper)
        paper_copy["score"] = float(score)
        top_papers.append(paper_copy)
    return top_papers


# This function extracts simple trending keywords from paper titles.
def get_trending_keywords(papers):
    titles_text = " ".join(paper.get("title", "") for paper in papers).lower()
    words = [word.strip(".,:;!?()[]{}\"'") for word in titles_text.split()]
    stopwords = {
        "the", "a", "an", "of", "in", "for", "with", "and", "to", "on", "by",
        "from", "using", "via", "based", "towards", "at", "into", "is", "are",
    }
    filtered = [w for w in words if len(w) > 2 and w not in stopwords]
    return dict(Counter(filtered).most_common(10))
