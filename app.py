import pandas as pd
import streamlit as st

from src.api import fetch_papers
from src import helpers as helper_utils
from src import recommender as recommender_utils


# Keep deployment robust if cloud temporarily runs mixed file versions.
make_project_idea = helper_utils.make_project_idea
normalize_difficulty = getattr(helper_utils, "normalize_difficulty", lambda value: str(value or "Beginner"))
get_complexity_score = getattr(helper_utils, "get_complexity_score", lambda text: 5)
filter_by_semester = getattr(helper_utils, "filter_by_semester", lambda score, semester: True)
build_why_explanation = getattr(
    helper_utils,
    "build_why_explanation",
    lambda domain, skill_level, paper_summary, relevance_pct: (
        f"This project aligns with {domain} for {skill_level}. Relevance score: {relevance_pct}%."
    ),
)
parse_query = getattr(
    helper_utils,
    "parse_query",
    lambda query: {
        "domain": "General",
        "project_type": "General",
        "application_area": "General",
        "tokens": [],
    },
)
filter_papers_by_tags = getattr(
    helper_utils,
    "filter_papers_by_tags",
    lambda papers, tags, minimum_results=8: papers,
)
build_search_terms = getattr(
    helper_utils,
    "build_search_terms",
    lambda query, tags: [query] if query else [],
)

get_top_papers = recommender_utils.get_top_papers
semantic_search = getattr(recommender_utils, "semantic_search", get_top_papers)
get_trending_keywords = recommender_utils.get_trending_keywords
apply_context_filters = getattr(
    recommender_utils,
    "apply_context_filters",
    lambda papers, domain, language, project_type, min_results=10: papers,
)
rerank_papers_by_skill_level = getattr(
    recommender_utils,
    "rerank_papers_by_skill_level",
    lambda papers, skill_level, top_n=10: sorted(
        papers,
        key=lambda x: float(x.get("score", 0.0)),
        reverse=True,
    )[:top_n],
)
rerank_papers_by_semester = getattr(
    recommender_utils,
    "rerank_papers_by_semester",
    lambda papers, semester, top_n=10: sorted(
        papers,
        key=lambda x: float(x.get("score", 0.0)),
        reverse=True,
    )[:top_n],
)

st.set_page_config(page_title="AI Project Recommender", layout="wide")


# This function initializes all state keys used by both independent modes.
def init_state():
    defaults = {
        "mode": None,
        "active_mode": None,
        "no_papers": False,
        "saved_projects": [],
        "paper_count": 20,
        "parsed_tags": {
            "domain": "General",
            "project_type": "General",
            "application_area": "General",
            "tokens": [],
        },
        "last_search_query": "",
        "search_results": [],
        "search_keywords": {},
        "search_top_papers": [],
        "filter_results": [],
        "filter_keywords": {},
        "filter_top_papers": [],
        "filter_feedback": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# This function formats project ideas as plain text for easy download.
def build_export_text(mode_name, context_info, projects):
    lines = [
        "AI Research Project Recommender",
        f"Mode: {mode_name}",
    ]
    for key, value in context_info.items():
        lines.append(f"{key}: {value}")
    lines.append("")

    for i, idea in enumerate(projects, start=1):
        paper_link = idea.get("source_paper", {}).get("link", "")
        relevance = idea.get("relevance_pct", 0)
        lines.extend(
            [
                f"Project {i}: {idea.get('title', 'Untitled')}",
                f"Description: {idea.get('description', '')}",
                f"Difficulty: {idea.get('difficulty', '')}",
                f"Relevance Score: {relevance}%",
                f"Why Matched: {idea.get('why_matched', '')}",
                f"Source Paper: {paper_link}",
                "",
            ]
        )
    return "\n".join(lines)


# This function draws one project card in a clean and readable format.
def show_project_card(idea, card_key):
    difficulty_colors = {
        "Beginner": ("#16a34a", "#ecfdf3"),
        "Intermediate": ("#ea580c", "#fff7ed"),
        "Advanced": ("#dc2626", "#fef2f2"),
    }
    with st.container(border=True):
        st.markdown("### 🚀 " + idea.get("title", "Untitled Project"))
        difficulty = normalize_difficulty(idea.get("difficulty", "Beginner"))
        badge_fg, badge_bg = difficulty_colors.get(difficulty, ("#1d4ed8", "#eff6ff"))
        st.markdown(
            f"<span style='display:inline-block;background:{badge_bg};color:{badge_fg};"
            f"padding:6px 12px;border-radius:999px;border:1px solid {badge_fg};font-weight:700;'>"
            f"Difficulty: {difficulty}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"⚙️ **Complexity: {idea.get('complexity_score', 0)}/10**")
        st.markdown(f"🔥 **Relevance Score: {idea.get('relevance_pct', 0)}%**")

        source_paper = idea.get("source_paper", {})
        source_title = source_paper.get("title", "Original arXiv Paper")
        source_link = source_paper.get("link", "")
        if source_link:
            st.markdown(f"📄 [Read source paper: {source_title}]({source_link})")

        st.write(idea.get("description", "No description available."))
        st.caption("💡 Why this project? " + idea.get("why_matched", "No reason provided."))
        st.markdown("")
        return st.button("💾 Save Project", key=f"save_project_{card_key}")


# This function adds a project to bookmarks and avoids duplicate saves.
def save_project(idea):
    saved = st.session_state["saved_projects"]
    source_link = idea.get("source_paper", {}).get("link", "")
    already_saved = any(
        p.get("title") == idea.get("title") and p.get("source_paper", {}).get("link", "") == source_link
        for p in saved
    )
    if not already_saved:
        saved.append(idea)
        st.session_state["saved_projects"] = saved


# This function builds project cards from ranked papers.
def build_ideas(top_papers, all_papers, paper_count, preferences, skill_level_for_generation, domain_for_explanation):
    ideas = []
    fallback_used = False
    for paper in top_papers:
        idea = make_project_idea(paper, skill_level_for_generation, preferences=preferences)
        source_summary = paper.get("summary", "")
        similar_papers = get_top_papers(all_papers, source_summary, top_n=paper_count)
        idea["source_paper"] = paper
        idea["similar_papers"] = similar_papers
        idea["difficulty"] = normalize_difficulty(idea.get("difficulty", skill_level_for_generation))
        idea["relevance_pct"] = int(round(float(paper.get("score", 0.0)) * 100))
        idea["complexity_score"] = int(paper.get("complexity_score", get_complexity_score(source_summary)))
        idea["why_matched"] = build_why_explanation(
            domain_for_explanation,
            skill_level_for_generation,
            source_summary,
            idea["relevance_pct"],
        )
        fallback_used = fallback_used or idea.get("is_fallback", False)
        ideas.append(idea)
    return ideas, fallback_used


# This function runs filter-based mode only from sidebar inputs.
def run_filter_mode(domain, skill_level, language, project_type, project_goal, semester, project_count, paper_count):
    papers = fetch_papers(domain, max_results=40)
    if not papers:
        fetch_papers.clear()
        papers = fetch_papers(domain, max_results=40)

    st.session_state["no_papers"] = len(papers) == 0
    if not papers:
        st.session_state["filter_results"] = []
        st.session_state["filter_top_papers"] = []
        st.session_state["filter_keywords"] = {}
        st.session_state["active_mode"] = "filter"
        st.session_state["search_results"] = []
        st.session_state["search_top_papers"] = []
        st.session_state["search_keywords"] = {}
        return

    skill_context = {
        "Beginner": "simple baseline tutorial",
        "Intermediate": "modular evaluation practical",
        "Advanced": "research optimization scalable",
    }
    user_query = (
        f"{domain} semester {semester} {skill_level} {skill_context[skill_level]} "
        f"{language} {project_type} {project_goal} student project"
    )

    candidate_count = min(max(project_count * 4, 24), len(papers))

    # Step 1: semantic search ranking.
    candidate_papers = semantic_search(papers, user_query, top_n=candidate_count)

    # Step 2: strict + boosted context filtering (domain/language/project type).
    context_ranked = apply_context_filters(
        candidate_papers,
        domain=domain,
        language=language,
        project_type=project_type,
        min_results=max(project_count, 10),
    )

    # Step 3: skill + semester reranking.
    skill_ranked = rerank_papers_by_skill_level(context_ranked, skill_level, top_n=candidate_count)
    semester_ranked = rerank_papers_by_semester(skill_ranked, semester, top_n=candidate_count)

    # Step 4: semester complexity filter.
    semester_filtered = []
    for paper in semester_ranked:
        text_for_complexity = f"{paper.get('title', '')} {paper.get('summary', '')}"
        complexity = get_complexity_score(text_for_complexity)
        if filter_by_semester(complexity, semester):
            copy_paper = dict(paper)
            copy_paper["complexity_score"] = complexity
            semester_filtered.append(copy_paper)

    top_papers = semester_filtered[:project_count]

    # Keep visible results even when semester band is very strict.
    if not top_papers:
        for paper in semester_ranked[:project_count]:
            copy_paper = dict(paper)
            copy_paper["complexity_score"] = get_complexity_score(
                f"{paper.get('title', '')} {paper.get('summary', '')}"
            )
            top_papers.append(copy_paper)

    preferences = {
        "domain": domain,
        "language": language,
        "project_type": project_type,
        "project_goal": project_goal,
        "semester": semester,
    }
    ideas, _ = build_ideas(top_papers, papers, paper_count, preferences, skill_level, domain)

    # Filter mode keeps selected skill filtering before rendering.
    filtered_ideas = [idea for idea in ideas if normalize_difficulty(idea.get("difficulty")) == skill_level]

    st.session_state["filter_results"] = filtered_ideas
    st.session_state["filter_top_papers"] = top_papers
    st.session_state["filter_keywords"] = get_trending_keywords(papers)
    st.session_state["paper_count"] = paper_count
    st.session_state["filter_feedback"] = {
        "semester": semester,
        "domain": domain,
        "language": language,
        "project_type": project_type,
        "avg_complexity": round(
            sum(i.get("complexity_score", 0) for i in filtered_ideas) / max(1, len(filtered_ideas)),
            1,
        ),
    }
    st.session_state["mode"] = "filter"
    st.session_state["active_mode"] = "filter"

    # Reset search mode state to keep both systems independent.
    st.session_state["search_results"] = []
    st.session_state["search_top_papers"] = []
    st.session_state["search_keywords"] = {}


# This function runs smart-search mode independently of sidebar filters.
def run_search_mode(search_query, project_count, paper_count):
    query_text = (search_query or "").strip()
    st.session_state["last_search_query"] = query_text

    if not query_text:
        st.warning("Please enter a search query before clicking Search Projects.")
        return

    parsed_tags = parse_query(query_text)
    st.session_state["parsed_tags"] = parsed_tags

    # Always fetch fresh in search mode, independent from cached filter results.
    fetch_papers.clear()
    papers = fetch_papers(query_text, max_results=40)

    # Fallback: expand into multiple search terms for user-friendly but non-academic queries.
    if not papers:
        expanded_terms = build_search_terms(query_text, parsed_tags)
        combined = []
        seen = set()
        for term in expanded_terms[:8]:
            term_papers = fetch_papers(term, max_results=20)
            for paper in term_papers:
                key = paper.get("link", "") or paper.get("title", "")
                if key and key not in seen:
                    seen.add(key)
                    combined.append(paper)
            if len(combined) >= 40:
                break
        papers = combined[:40]

    st.session_state["no_papers"] = len(papers) == 0

    if not papers:
        st.session_state["search_results"] = []
        st.session_state["search_top_papers"] = []
        st.session_state["search_keywords"] = {}
        st.session_state["active_mode"] = "search"
        st.session_state["filter_results"] = []
        st.session_state["filter_top_papers"] = []
        st.session_state["filter_keywords"] = {}
        return

    candidate_source = filter_papers_by_tags(papers, parsed_tags, minimum_results=8)

    # Use full user query for semantic matching in search mode.
    top_papers = get_top_papers(candidate_source, query_text, top_n=project_count)

    search_preferences = {
        "domain": parsed_tags.get("domain", "General"),
        "language": "Python",
        "project_type": parsed_tags.get("project_type", "Prototype"),
        "project_goal": f"{parsed_tags.get('application_area', 'General')} focused project",
        "semester": 4,
    }
    ideas, _ = build_ideas(
        top_papers,
        papers,
        paper_count,
        search_preferences,
        "Intermediate",
        parsed_tags.get("domain", "General"),
    )

    st.session_state["search_results"] = ideas
    st.session_state["search_top_papers"] = top_papers
    st.session_state["search_keywords"] = get_trending_keywords(papers)
    st.session_state["paper_count"] = paper_count
    st.session_state["mode"] = "search"
    st.session_state["active_mode"] = "search"

    # Reset filter mode state to keep both systems independent.
    st.session_state["filter_results"] = []
    st.session_state["filter_top_papers"] = []
    st.session_state["filter_keywords"] = {}


# This function renders whichever mode is active in a consistent layout.
def render_mode_results(section_title, results, keywords, top_papers, paper_count, export_text):
    st.subheader(section_title)
    st.markdown("")

    if not results:
        st.info("No recommendations to show for this mode yet.")
        return

    cols = st.columns(2)
    for i, idea in enumerate(results):
        with cols[i % 2]:
            saved_clicked = show_project_card(idea, card_key=f"{section_title}_{i}")
            if saved_clicked:
                save_project(idea)
                st.success("Saved to bookmarks")

            similar_papers = idea.get("similar_papers", [])
            with st.expander(f"Show {paper_count} similar research papers"):
                if similar_papers:
                    for paper in similar_papers:
                        title = paper.get("title", "Untitled")
                        link = paper.get("link", "")
                        summary = paper.get("summary", "No summary available.")
                        st.markdown(f"- [{title}]({link})")
                        st.caption(summary[:240] + ("..." if len(summary) > 240 else ""))
                else:
                    st.write("No similar papers found for this project.")
            st.markdown("---")

    st.subheader("📊 Trending Keywords")
    if keywords:
        chart_df = pd.DataFrame(
            {"keyword": list(keywords.keys()), "count": list(keywords.values())}
        ).set_index("keyword")
        st.bar_chart(chart_df)

    st.download_button(
        label="Download Results (.txt)",
        data=export_text,
        file_name="ai_project_recommendations.txt",
        mime="text/plain",
    )

    if top_papers:
        st.divider()
        st.subheader("📚 Source Research Papers (arXiv)")
        for i, paper in enumerate(top_papers, start=1):
            title = paper.get("title", "Untitled")
            link = paper.get("link", "")
            summary = paper.get("summary", "No summary available.")
            st.markdown(f"{i}. [{title}]({link})")
            with st.expander("Show summary"):
                st.write(summary)


init_state()

st.title("AI Research Project Recommender")
st.write("Pick your domain and skill level to discover research-driven project ideas.")
st.divider()

# Search mode trigger (independent from sidebar filters).
search_query = st.text_input(
    "Smart Search",
    placeholder="Search for projects like 'Full stack e-commerce' or 'AI healthcare beginner projects'",
)
search_clicked = st.button("Search Projects")

if search_query.strip():
    tags_preview = parse_query(search_query)
    st.markdown(
        f"**Extracted Tags**  \\nDomain: `{tags_preview.get('domain', 'General')}` | "
        f"Type: `{tags_preview.get('project_type', 'General')}` | "
        f"Area: `{tags_preview.get('application_area', 'General')}`"
    )

with st.sidebar:
    st.header("Project Inputs")
    domain = st.selectbox(
        "Choose a domain",
        [
            "artificial intelligence",
            "machine learning",
            "computer vision",
            "nlp",
            "cybersecurity",
            "web development",
            "data science",
        ],
    )
    skill_level = st.radio("Skill level", ["Beginner", "Intermediate", "Advanced"])
    language = st.selectbox(
        "Programming language",
        ["Python", "JavaScript", "Java", "C++", "Go", "Rust"],
    )
    project_type = st.selectbox(
        "Project type",
        ["Web App", "Notebook Prototype", "CLI Tool", "Data Pipeline", "API Service"],
    )
    project_goal = st.selectbox(
        "Project goal",
        [
            "Portfolio-ready project",
            "Hackathon-ready prototype",
            "Research replication",
            "Industry-style solution",
        ],
    )
    semester = st.slider("Semester", min_value=1, max_value=8, value=4)
    project_count = st.slider("How many project ideas", min_value=6, max_value=15, value=10)
    paper_count = st.slider("How many research papers", min_value=10, max_value=30, value=20)

    # Filter mode trigger (independent from smart search).
    find_projects = st.button("Find Projects")

if search_clicked:
    # Clicking search mode clears filter mode state inside run_search_mode.
    run_search_mode(search_query, project_count, paper_count)
elif find_projects:
    # Clicking filter mode clears search mode state inside run_filter_mode.
    run_filter_mode(domain, skill_level, language, project_type, project_goal, semester, project_count, paper_count)

if st.session_state["no_papers"]:
    st.warning("No papers found. Try a different query/domain.")

# This badge makes it clear which recommendation system is currently active.
if st.session_state.get("mode") == "search":
    st.info("🔍 Active Mode: Search-based Recommendations")
elif st.session_state.get("mode") == "filter":
    st.info("🎛️ Active Mode: Filter-based Recommendations")

active_mode = st.session_state["active_mode"]
if active_mode == "search":
    tags = st.session_state.get("parsed_tags", {})
    st.caption(
        f"Domain: {tags.get('domain', 'General')} | "
        f"Type: {tags.get('project_type', 'General')} | "
        f"Area: {tags.get('application_area', 'General')}"
    )

    export_text = build_export_text(
        "Search-Based",
        {
            "Query": st.session_state.get("last_search_query", ""),
            "Domain Tag": tags.get("domain", "General"),
            "Type Tag": tags.get("project_type", "General"),
            "Area Tag": tags.get("application_area", "General"),
        },
        st.session_state["search_results"],
    )
    render_mode_results(
        "🔍 Search-Based Recommendations",
        st.session_state["search_results"],
        st.session_state["search_keywords"],
        st.session_state["search_top_papers"],
        st.session_state.get("paper_count", 12),
        export_text,
    )
elif active_mode == "filter":
    feedback = st.session_state.get("filter_feedback", {})
    st.write("🎯 Filters Applied:")
    st.write(f"Semester: {feedback.get('semester', semester)}")
    st.write(f"Domain: {feedback.get('domain', domain)}")
    st.write(f"Languages: {feedback.get('language', language)}")
    st.write(f"Project Type: {feedback.get('project_type', project_type)}")
    st.write(f"⚙️ Complexity Score: {feedback.get('avg_complexity', 0)}/10")

    export_text = build_export_text(
        "Filter-Based",
        {
            "Domain": domain,
            "Skill Level": skill_level,
            "Semester": semester,
            "Language": language,
            "Project Type": project_type,
            "Project Goal": project_goal,
        },
        st.session_state["filter_results"],
    )
    render_mode_results(
        "🎛️ Filter-Based Recommendations",
        st.session_state["filter_results"],
        st.session_state["filter_keywords"],
        st.session_state["filter_top_papers"],
        st.session_state.get("paper_count", 12),
        export_text,
    )
else:
    st.info("Use either Smart Search or Find Projects to generate recommendations.")

if st.session_state["saved_projects"]:
    st.divider()
    st.subheader("🔖 Saved Projects")
    saved_cols = st.columns(2)
    for i, saved_idea in enumerate(st.session_state["saved_projects"]):
        with saved_cols[i % 2]:
            with st.container(border=True):
                st.markdown("#### " + saved_idea.get("title", "Untitled"))
                st.write(saved_idea.get("description", ""))
                st.caption(saved_idea.get("why_matched", ""))
                saved_link = saved_idea.get("source_paper", {}).get("link", "")
                if saved_link:
                    st.markdown(f"📄 [Open source paper]({saved_link})")
    if st.button("Clear Saved Projects"):
        st.session_state["saved_projects"] = []
        st.rerun()
