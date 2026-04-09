import os


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

    skill_descriptions = {
        "Beginner": "Build a basic version with simple preprocessing, one baseline model, and a short results summary.",
        "Intermediate": "Build a modular version with comparative experiments, better evaluation, and clear error analysis.",
        "Advanced": "Build a research-grade version with stronger architecture choices, optimization, and reproducible benchmarks.",
    }
    detail = skill_descriptions.get(skill_level, skill_descriptions["Beginner"])

    clean_difficulty = normalize_difficulty(skill_level)
    fallback_idea = {
        "title": f"{project_type}: {paper.get('title', 'Research Topic')[:65]}",
        "description": (
            f"Create a {project_goal.lower()} in {language} for {domain}. "
            f"{detail}"
        ),
        "difficulty": clean_difficulty,
        "why_matched": (
            f"Matched to {domain} with {skill_level} scope and a {project_type.lower()} format in {language}."
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
