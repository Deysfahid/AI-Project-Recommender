import pandas as pd
import streamlit as st

from src.api import fetch_papers
from src.helpers import build_why_explanation, make_project_idea, normalize_difficulty
from src.recommender import get_top_papers, get_trending_keywords, rerank_papers_by_skill_level

st.set_page_config(page_title="AI Project Recommender", layout="wide")


# This function formats project ideas as plain text for easy download.
def build_export_text(domain, skill_level, semester, language, project_type, project_goal, projects):
    lines = [
        "AI Research Project Recommender",
        f"Domain: {domain}",
        f"Skill Level: {skill_level}",
        f"Semester: {semester}",
        f"Language: {language}",
        f"Project Type: {project_type}",
        f"Project Goal: {project_goal}",
        "",
    ]
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


if "results" not in st.session_state:
    st.session_state["results"] = []
if "keywords" not in st.session_state:
    st.session_state["keywords"] = {}
if "api_fallback" not in st.session_state:
    st.session_state["api_fallback"] = False
if "no_papers" not in st.session_state:
    st.session_state["no_papers"] = False
if "top_papers" not in st.session_state:
    st.session_state["top_papers"] = []
if "paper_count" not in st.session_state:
    st.session_state["paper_count"] = 12
if "saved_projects" not in st.session_state:
    st.session_state["saved_projects"] = []
    

st.title("AI Research Project Recommender")
st.write("Pick your domain and skill level to discover research-driven project ideas.")
st.divider()

with st.sidebar:
    st.header("Project Inputs")
    domain = st.selectbox(
        "Choose a domain",
        [
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
        ["Portfolio-ready project", "Hackathon-ready prototype", "Research replication", "Industry-style solution"],
    )
    semester = st.slider("Semester", min_value=1, max_value=8, value=4)
    project_count = st.slider("How many project ideas", min_value=6, max_value=15, value=10)
    paper_count = st.slider("How many research papers", min_value=10, max_value=15, value=12)
    find_projects = st.button("Find Projects")

if find_projects:
    with st.spinner("Searching papers..."):
        papers = fetch_papers(domain)

        # Retry once if cache contains stale empty results from a transient API/network issue.
        if not papers:
            fetch_papers.clear()
            papers = fetch_papers(domain)

        st.session_state["no_papers"] = len(papers) == 0

        if papers:
            skill_context = {
                "Beginner": "simple baseline tutorial",
                "Intermediate": "modular evaluation practical",
                "Advanced": "research optimization scalable",
            }
            user_query = (
                f"{domain} semester {semester} {skill_level} {skill_context[skill_level]} "
                f"{language} {project_type} {project_goal} student project"
            )
            # Fetch a larger candidate pool first, then skill-rerank for distinct level outputs.
            candidate_count = min(max(project_count * 3, 18), len(papers))
            candidate_papers = get_top_papers(papers, user_query, top_n=candidate_count)
            top_papers = rerank_papers_by_skill_level(candidate_papers, skill_level, top_n=project_count)

            ideas = []
            fallback_used = False
            preferences = {
                "domain": domain,
                "language": language,
                "project_type": project_type,
                "project_goal": project_goal,
            }
            for paper in top_papers:
                idea = make_project_idea(paper, skill_level, preferences=preferences)
                source_summary = paper.get("summary", "")
                similar_papers = get_top_papers(papers, source_summary, top_n=paper_count)
                idea["source_paper"] = paper
                idea["similar_papers"] = similar_papers
                idea["difficulty"] = normalize_difficulty(idea.get("difficulty", skill_level))
                idea["relevance_pct"] = int(round(float(paper.get("score", 0.0)) * 100))
                idea["why_matched"] = build_why_explanation(
                    domain,
                    skill_level,
                    source_summary,
                    idea["relevance_pct"],
                )
                fallback_used = fallback_used or idea.get("is_fallback", False)
                ideas.append(idea)

            # Difficulty filtering is applied before rendering, not only in UI labels.
            filtered_ideas = [
                idea for idea in ideas if normalize_difficulty(idea.get("difficulty")) == skill_level
            ]

            st.session_state["results"] = filtered_ideas
            st.session_state["top_papers"] = top_papers
            st.session_state["keywords"] = get_trending_keywords(papers)
            st.session_state["api_fallback"] = fallback_used
            st.session_state["paper_count"] = paper_count
        else:
            st.session_state["results"] = []
            st.session_state["top_papers"] = []
            st.session_state["keywords"] = {}
            st.session_state["api_fallback"] = False

if st.session_state["no_papers"]:
    st.warning("No papers found. Try a different domain.")

if st.session_state["results"]:
    st.subheader("🚀 Recommended Student Projects")
    st.markdown("")
    cols = st.columns(2)
    for i, idea in enumerate(st.session_state["results"]):
        with cols[i % 2]:
            saved_clicked = show_project_card(idea, card_key=i)
            if saved_clicked:
                save_project(idea)
                st.success("Saved to bookmarks")

            similar_papers = idea.get("similar_papers", [])
            similar_count = st.session_state.get("paper_count", 12)
            with st.expander(f"Show {similar_count} similar research papers"):
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
    keywords = st.session_state["keywords"]
    if keywords:
        chart_df = pd.DataFrame(
            {"keyword": list(keywords.keys()), "count": list(keywords.values())}
        ).set_index("keyword")
        st.bar_chart(chart_df)

    export_text = build_export_text(
        domain,
        skill_level,
        semester,
        language,
        project_type,
        project_goal,
        st.session_state["results"],
    )
    st.download_button(
        label="Download Results (.txt)",
        data=export_text,
        file_name="ai_project_recommendations.txt",
        mime="text/plain",
    )
else:
    if not st.session_state["no_papers"]:
        st.info("Click Find Projects to generate recommendations.")

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

if st.session_state["top_papers"]:
    st.divider()
    st.subheader("📚 Source Research Papers (arXiv)")
    for i, paper in enumerate(st.session_state["top_papers"], start=1):
        title = paper.get("title", "Untitled")
        link = paper.get("link", "")
        summary = paper.get("summary", "No summary available.")
        st.markdown(f"{i}. [{title}]({link})")
        with st.expander("Show summary"):
            st.write(summary)
