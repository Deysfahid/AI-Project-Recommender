import os


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
def make_project_idea(paper, skill_level):
    fallback_idea = {
        "title": f"Mini Project: {paper.get('title', 'Research Topic')[:70]}",
        "description": "Create a small prototype that applies the main idea from this paper. Focus on one measurable outcome and report your results.",
        "difficulty": skill_level,
        "why_matched": "Free mode: this paper closely matches your selected topic and skill level.",
        "is_fallback": True,
    }

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback_idea

    summary_snippet = paper.get("summary", "")[:300]
    prompt = (
        f"Based on this research paper: {paper.get('title', '')} - {summary_snippet}\n"
        f"Suggest ONE student project idea for a {skill_level} student.\n"
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
        return _parse_idea_text(text, paper, skill_level)
    except Exception:
        return fallback_idea
