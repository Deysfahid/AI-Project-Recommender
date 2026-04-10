from collections import Counter

import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity


DOMAIN_KEYWORDS = {
    "artificial intelligence": ["ai", "artificial intelligence", "machine learning", "deep learning"],
    "machine learning": ["machine learning", "ml", "deep learning", "neural"],
    "computer vision": ["computer vision", "image", "vision", "object detection", "segmentation"],
    "nlp": ["nlp", "language model", "text", "transformer", "token"],
    "web development": ["web", "frontend", "backend", "full stack", "api"],
    "cybersecurity": ["security", "encryption", "malware", "threat", "vulnerability"],
    "data science": ["data science", "analytics", "prediction", "dataset", "statistics"],
}

LANGUAGE_KEYWORDS = {
    "python": ["python", "pytorch", "tensorflow", "numpy", "pandas"],
    "javascript": ["javascript", "node", "react", "frontend", "browser"],
    "java": ["java", "spring", "backend", "jvm"],
    "c++": ["c++", "cpp", "performance", "embedded"],
    "go": ["go", "golang", "microservice", "concurrency"],
    "rust": ["rust", "memory safety", "systems"],
}

PROJECT_TYPE_KEYWORDS = {
    "web app": ["web", "frontend", "backend", "full stack"],
    "notebook prototype": ["notebook", "prototype", "experiment"],
    "cli tool": ["command", "cli", "terminal", "tool"],
    "data pipeline": ["pipeline", "etl", "workflow", "data processing"],
    "api service": ["api", "service", "endpoint", "backend"],
}


# This function keeps a score value inside the 0.0 to 1.0 range.
def _clamp_score(value):
    return max(0.0, min(1.0, float(value)))


# This function returns domain/language/type keywords for filtering and boosting.
def _keywords_for_context(domain, language, project_type):
    domain_terms = DOMAIN_KEYWORDS.get((domain or "").lower(), [])
    language_terms = LANGUAGE_KEYWORDS.get((language or "").lower(), [])
    type_terms = PROJECT_TYPE_KEYWORDS.get((project_type or "").lower(), [])
    return domain_terms, language_terms, type_terms


# This function filters and boosts papers using selected domain/language/project-type context.
def apply_context_filters(papers, domain, language, project_type, min_results=10):
    if not papers:
        return []

    domain_terms, language_terms, type_terms = _keywords_for_context(domain, language, project_type)

    rescored = []
    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
        domain_hit = any(term in text for term in domain_terms) if domain_terms else False
        language_hit = any(term in text for term in language_terms) if language_terms else False
        type_hit = any(term in text for term in type_terms) if type_terms else False

        boost = 0.0
        if domain_hit:
            boost += 0.12
        if language_hit:
            boost += 0.08
        if type_hit:
            boost += 0.06

        paper_copy = dict(paper)
        paper_copy["score"] = _clamp_score(paper.get("score", 0.0) + boost)
        paper_copy["context_hits"] = {
            "domain": domain_hit,
            "language": language_hit,
            "project_type": type_hit,
        }
        rescored.append(paper_copy)

    strict = [
        p for p in rescored
        if p.get("context_hits", {}).get("domain") and (
            p.get("context_hits", {}).get("language") or p.get("context_hits", {}).get("project_type")
        )
    ]

    if len(strict) >= min_results:
        base = strict
    else:
        domain_only = [p for p in rescored if p.get("context_hits", {}).get("domain")]
        base = domain_only if len(domain_only) >= min_results else rescored

    return sorted(base, key=lambda x: x.get("score", 0.0), reverse=True)


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


# This function reranks papers by semester maturity so project complexity grows over time.
def rerank_papers_by_semester(papers, semester, top_n=10):
    if not papers:
        return []

    sem = int(semester)
    if sem <= 2:
        keywords = {
            "tutorial": 1.0,
            "survey": 0.9,
            "introduction": 0.9,
            "simple": 0.8,
            "application": 0.6,
        }
    elif sem <= 5:
        keywords = {
            "implementation": 1.0,
            "evaluation": 0.9,
            "framework": 0.8,
            "pipeline": 0.8,
            "practical": 0.7,
        }
    else:
        keywords = {
            "optimization": 1.0,
            "benchmark": 0.9,
            "state-of-the-art": 0.9,
            "novel": 0.9,
            "robust": 0.7,
            "multimodal": 0.7,
        }

    rescored = []
    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
        semester_bonus = 0.0
        for word, weight in keywords.items():
            if word in text:
                semester_bonus += weight

        normalized_bonus = _clamp_score(semester_bonus / 3.0)
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


# This function provides a semantic-search API used by the app pipeline.
def semantic_search(papers, user_query, top_n=10):
    return get_top_papers(papers, user_query, top_n=top_n)


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
