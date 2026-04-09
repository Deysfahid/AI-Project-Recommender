from collections import Counter

import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity


# This function keeps a score value inside the 0.0 to 1.0 range.
def _clamp_score(value):
    return max(0.0, min(1.0, float(value)))


# This function returns level-specific keywords used to diversify project results.
def _skill_keyword_weights(skill_level):
    if skill_level == "Beginner":
        return {
            "tutorial": 1.0,
            "survey": 1.0,
            "introduction": 0.9,
            "baseline": 0.8,
            "simple": 0.8,
            "overview": 0.8,
            "applied": 0.6,
            "practical": 0.6,
        }
    if skill_level == "Intermediate":
        return {
            "application": 0.9,
            "implementation": 0.9,
            "evaluation": 0.9,
            "comparative": 0.8,
            "framework": 0.8,
            "analysis": 0.7,
            "workflow": 0.7,
            "pipeline": 0.7,
        }
    return {
        "optimization": 1.0,
        "novel": 1.0,
        "state-of-the-art": 1.0,
        "benchmark": 0.9,
        "transformer": 0.9,
        "diffusion": 0.9,
        "multimodal": 0.8,
        "theoretical": 0.8,
        "robust": 0.7,
    }


# This function reranks papers by combining semantic relevance and skill-level complexity cues.
def rerank_papers_by_skill_level(papers, skill_level, top_n=10):
    if not papers:
        return []

    keywords = _skill_keyword_weights(skill_level)
    rescored = []
    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
        keyword_bonus = 0.0
        for word, weight in keywords.items():
            if word in text:
                keyword_bonus += weight

        normalized_bonus = _clamp_score(keyword_bonus / 3.0)
        base_score = _clamp_score(paper.get("score", 0.0))
        combined_score = (0.75 * base_score) + (0.25 * normalized_bonus)

        paper_copy = dict(paper)
        paper_copy["score"] = _clamp_score(combined_score)
        rescored.append(paper_copy)

    return sorted(rescored, key=lambda x: x.get("score", 0.0), reverse=True)[:top_n]


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
        max_score = max([score for score, _ in scored], default=1) or 1
        ranked = sorted(scored, key=lambda x: x[0], reverse=True)
        top_papers = []
        for score, paper in ranked[:top_n]:
            paper_copy = dict(paper)
            paper_copy["score"] = _clamp_score(score / max_score)
            top_papers.append(paper_copy)
        return top_papers

    embeddings = model.encode([user_query] + summaries)
    query_embedding = embeddings[0]
    paper_embeddings = embeddings[1:]

    similarities = cosine_similarity([query_embedding], paper_embeddings)[0]
    ranked = sorted(zip(similarities, papers), key=lambda x: x[0], reverse=True)

    top_papers = []
    for score, paper in ranked[:top_n]:
        paper_copy = dict(paper)
        # Cosine can be in [-1, 1], so normalize to [0, 1].
        paper_copy["score"] = _clamp_score((float(score) + 1.0) / 2.0)
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
