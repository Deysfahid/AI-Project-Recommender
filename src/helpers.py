import os
import hashlib


# This function parses a free-text query into domain, project type, and application area tags.
def parse_query(query):
    text = (query or "").lower()

    domain_map = {
        "AI": ["ai", "artificial intelligence"],
        "Machine Learning": ["machine learning", "ml", "deep learning"],
        "Computer Vision": ["computer vision", "vision", "image", "opencv"],
        "NLP": ["nlp", "language model", "text", "transformer"],
        "Web Development": ["web", "frontend", "backend", "full stack", "fullstack"],
        "Data Science": ["data science", "analytics", "data analysis"],
        "Cybersecurity": ["cybersecurity", "security", "threat", "malware"],
    }
    type_map = {
        "Full Stack": ["full stack", "fullstack"],
        "Frontend": ["frontend", "front end", "ui"],
        "Backend": ["backend", "back end", "api"],
        "Machine Learning": ["machine learning", "ml", "model"],
        "Data Pipeline": ["pipeline", "etl", "workflow"],
        "Management System": ["management system", "admin panel", "dashboard"],
    }
    area_map = {
        "Healthcare": ["healthcare", "medical", "hospital", "diagnosis"],
        "E-commerce": ["e-commerce", "ecommerce", "e commerce", "shopping", "retail", "store"],
        "Finance": ["finance", "banking", "fintech", "fraud"],
        "Education": ["education", "learning", "student", "school", "college", "university"],
        "Social Media": ["social", "social media", "recommendation"],
    }

    def match_tag(tag_map):
        for label, words in tag_map.items():
            if any(word in text for word in words):
                return label
        return "General"

    tokens = [t for t in text.replace("/", " ").replace("-", " ").split() if len(t) > 2]
    return {
        "domain": match_tag(domain_map),
        "project_type": match_tag(type_map),
        "application_area": match_tag(area_map),
        "tokens": tokens,
    }


# This function expands a user query into multiple fallback arXiv search terms.
def build_search_terms(query, tags):
    base = []
    query_text = (query or "").strip()
    if query_text:
        base.append(query_text)

    domain = tags.get("domain", "General")
    project_type = tags.get("project_type", "General")
    area = tags.get("application_area", "General")

    if domain != "General":
        base.append(domain)
    if project_type != "General":
        base.append(project_type)
    if area != "General":
        base.append(area)

    token_terms = [t for t in tags.get("tokens", []) if len(t) > 3]
    for term in token_terms[:6]:
        base.append(term)

    # Preserve order but remove duplicates.
    unique_terms = []
    seen = set()
    for term in base:
        normalized = term.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_terms.append(term)
    return unique_terms


# This function filters papers by parsed tags while keeping a fallback to the full list.
def filter_papers_by_tags(papers, tags, minimum_results=8):
    if not papers:
        return []

    searchable_terms = []
    for key in ["domain", "project_type", "application_area"]:
        value = tags.get(key, "")
        if value and value != "General":
            searchable_terms.extend(value.lower().split())
    searchable_terms.extend(tags.get("tokens", [])[:6])

    searchable_terms = [t for t in searchable_terms if len(t) > 2]
    if not searchable_terms:
        return papers

    filtered = []
    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
        if any(term in text for term in searchable_terms):
            filtered.append(paper)

    return filtered if len(filtered) >= minimum_results else papers


# This function extracts a few meaningful terms to make each fallback idea more specific.
def _extract_focus_terms(title, summary):
    text = f"{title} {summary}".lower()
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    words = [w for w in cleaned.split() if len(w) > 3]
    stopwords = {
        "with", "from", "that", "this", "their", "using", "based", "towards", "through",
        "study", "paper", "approach", "analysis", "method", "methods", "results", "system",
    }
    filtered = [w for w in words if w not in stopwords]
    return filtered[:4]


# This function estimates project complexity (1-10) from text signals.
def get_complexity_score(text):
    content = (text or "").lower()
    score = 4

    beginner_terms = ["tutorial", "survey", "introduction", "basic", "simple", "overview"]
    advanced_terms = [
        "optimization",
        "benchmark",
        "state-of-the-art",
        "novel",
        "multimodal",
        "theoretical",
        "robust",
        "scalable",
    ]

    score -= sum(1 for term in beginner_terms if term in content)
    score += sum(1 for term in advanced_terms if term in content)

    token_count = len(content.split())
    if token_count > 160:
        score += 2
    elif token_count > 90:
        score += 1
    elif token_count < 45:
        score -= 1

    return max(1, min(10, score))


# This function checks if a complexity score is suitable for a selected semester.
def filter_by_semester(score, semester):
    sem = int(semester)
    if sem <= 2:
        low, high = 1, 4
    elif sem <= 4:
        low, high = 3, 7
    elif sem <= 6:
        low, high = 5, 9
    else:
        low, high = 7, 10
    return low <= int(score) <= high


# This function normalizes difficulty labels so filtering stays consistent.
def normalize_difficulty(value):
    raw = str(value or "").strip().lower()
    if raw.startswith("beg"):
        return "Beginner"
    if raw.startswith("int"):
        return "Intermediate"
    if raw.startswith("adv"):
        return "Advanced"
    return "Beginner"


# This function creates a dynamic explanation using context from user choices and paper text.
def build_why_explanation(domain, skill_level, paper_summary, relevance_pct):
    summary = (paper_summary or "").replace("\n", " ").strip()
    first_sentence = summary.split(".")[0].strip() if summary else "core ideas from the selected paper"
    first_sentence = first_sentence[:180]

    skill_focus = {
        "Beginner": "keeping the scope small with a clear baseline",
        "Intermediate": "adding comparisons and stronger evaluation",
        "Advanced": "pushing toward optimization and research-style rigor",
    }
    focus_text = skill_focus.get(skill_level, skill_focus["Beginner"])
    return (
        f"This project aligns with {domain} because the paper emphasizes {first_sentence}. "
        f"It matches {skill_level} level by {focus_text}. Relevance score: {relevance_pct}%."
    )


# This function returns a semester-aware project scope profile.
def get_semester_profile(semester):
    sem = int(semester)
    if sem <= 2:
        return {
            "track": "Starter",
            "scope": "small and guided",
            "features": "1 core feature, basic UI, and a short report",
            "difficulty_hint": "Beginner",
        }
    if sem <= 5:
        return {
            "track": "Builder",
            "scope": "moderate and structured",
            "features": "2-3 features, evaluation metrics, and cleaner project structure",
            "difficulty_hint": "Intermediate",
        }
    return {
        "track": "Capstone",
        "scope": "advanced and research-oriented",
        "features": "multiple modules, optimization or comparison study, and strong documentation",
        "difficulty_hint": "Advanced",
    }


# This function turns Claude text into a simple dictionary for the app UI.
def _parse_idea_text(text, paper, skill_level):
    idea = {
        "title": f"Project from: {paper.get('title', 'Research Paper')}",
        "description": "Build a student-friendly prototype inspired by this paper.",
        "difficulty": skill_level,
        "why_matched": "It is semantically similar to your selected domain.",
        "is_fallback": False,
    }

    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        clean_key = key.strip().lower().replace(" ", "_")
        clean_value = value.strip()
        if clean_key in {"title", "description", "difficulty", "why_matched"} and clean_value:
            idea[clean_key] = clean_value
    return idea


# This function asks Claude for one project idea and falls back to a template if needed.
def make_project_idea(paper, skill_level, preferences=None):
    preferences = preferences or {}
    language = preferences.get("language", "Python")
    project_type = preferences.get("project_type", "Prototype")
    project_goal = preferences.get("project_goal", "Portfolio-ready project")
    domain = preferences.get("domain", "AI")
    semester = int(preferences.get("semester", 4))
    sem_profile = get_semester_profile(semester)

    skill_descriptions = {
        "Beginner": "Build a basic version with simple preprocessing, one baseline model, and a short results summary.",
        "Intermediate": "Build a modular version with comparative experiments, better evaluation, and clear error analysis.",
        "Advanced": "Build a research-grade version with stronger architecture choices, optimization, and reproducible benchmarks.",
    }
    detail = skill_descriptions.get(skill_level, skill_descriptions["Beginner"])
    paper_title = paper.get("title", "Research Topic")
    summary_text = (paper.get("summary", "") or "").replace("\n", " ").strip()
    summary_focus = summary_text.split(".")[0].strip() if summary_text else "the main contribution"
    summary_focus = summary_focus[:160]
    focus_terms = _extract_focus_terms(paper_title, summary_text)
    focus_hint = ", ".join(focus_terms[:3]) if focus_terms else "core paper concepts"

    # Deterministic template selection so each paper gets stable but varied wording.
    template_seed = int(hashlib.md5(paper_title.encode("utf-8", errors="ignore")).hexdigest(), 16)
    template_variant = template_seed % 3

    if template_variant == 0:
        varied_description = (
            f"Build a {project_goal.lower()} in {language} for {domain}, centered on {focus_hint}. "
            f"Keep the scope {sem_profile['scope']} with {sem_profile['features']}. {detail}"
        )
    elif template_variant == 1:
        varied_description = (
            f"Design a {project_type.lower()} that applies {focus_hint} from this paper in a practical {domain} scenario. "
            f"For semester {semester}, keep it {sem_profile['scope']} and include {sem_profile['features']}."
        )
    else:
        varied_description = (
            f"Create an end-to-end student project inspired by '{paper_title[:55]}', focusing on {focus_hint}. "
            f"Target a {project_goal.lower()} outcome with {sem_profile['features']} and clear evaluation."
        )

    clean_difficulty = normalize_difficulty(skill_level)
    fallback_idea = {
        "title": f"{sem_profile['track']} {project_type}: {paper_title[:56]}",
        "description": varied_description,
        "difficulty": clean_difficulty,
        "why_matched": (
            f"Matched to {domain} with {skill_level} scope for semester {semester} ({sem_profile['track']} track), "
            f"using paper-specific context ({focus_hint}) from '{paper_title[:70]}' in a {project_type.lower()} format with {language}."
        ),
        "is_fallback": True,
    }

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback_idea

    summary_snippet = paper.get("summary", "")[:300]
    prompt = (
        f"Based on this research paper: {paper.get('title', '')} - {summary_snippet}\n"
        f"Suggest ONE student project idea for a {skill_level} student.\n"
        f"Preferred language: {language}\n"
        f"Preferred project type: {project_type}\n"
        f"Goal: {project_goal}\n"
        f"Domain: {domain}\n"
        f"Semester: {semester}\n"
        f"Semester track: {sem_profile['track']}\n"
        f"Expected scope: {sem_profile['scope']}\n"
        f"Target features: {sem_profile['features']}\n"
        "Return ONLY: title, description (2 sentences), difficulty, why_matched"
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-3-5-20251001",
            max_tokens=220,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text if response.content else ""
        idea = _parse_idea_text(text, paper, clean_difficulty)
        idea["difficulty"] = normalize_difficulty(idea.get("difficulty", clean_difficulty))
        return idea
    except Exception:
        return fallback_idea
