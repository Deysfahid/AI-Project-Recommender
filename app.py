import pandas as pd
import streamlit as st

from src.api import fetch_papers
from src.helpers import make_project_idea
from src.recommender import get_top_papers, get_trending_keywords

st.set_page_config(page_title="AI Project Recommender", layout="wide")


# This function formats project ideas as plain text for easy download.
def build_export_text(domain, skill_level, semester, projects):
    lines = [
        "AI Research Project Recommender",
        f"Domain: {domain}",
        f"Skill Level: {skill_level}",
        f"Semester: {semester}",
        "",
    ]
    for i, idea in enumerate(projects, start=1):
        lines.extend(
            [
                f"Project {i}: {idea.get('title', 'Untitled')}",
                f"Description: {idea.get('description', '')}",
                f"Difficulty: {idea.get('difficulty', '')}",
                f"Why Matched: {idea.get('why_matched', '')}",
                "",
            ]
        )
    return "\n".join(lines)


# This function draws one project card in a clean and readable format.
def show_project_card(idea):
    with st.container(border=True):
        st.subheader(idea.get("title", "Untitled Project"))
        difficulty = idea.get("difficulty", "Unknown")
        st.markdown(
            f"<span style='display:inline-block;background:#93c5fd;color:#0b1220;"
            f"padding:6px 12px;border-radius:999px;border:1px solid #60a5fa;font-weight:700;'>"
            f"Difficulty: {difficulty}</span>",
            unsafe_allow_html=True,
        )
        st.write(idea.get("description", "No description available."))
        st.caption(f"Why matched: {idea.get('why_matched', 'No reason provided.')}")


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

st.title("AI Research Project Recommender")
st.write("Pick your domain and skill level to discover research-driven project ideas.")

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
    semester = st.slider("Semester", min_value=1, max_value=8, value=4)
    project_count = st.slider("How many project ideas", min_value=6, max_value=15, value=10)
    paper_count = st.slider("How many research papers", min_value=10, max_value=15, value=12)
    find_projects = st.button("Find Projects")

if find_projects:
    with st.spinner("Searching papers..."):
        papers = fetch_papers(domain)
        st.session_state["no_papers"] = len(papers) == 0

        if papers:
            user_query = f"{domain} semester {semester} {skill_level} student project"
            top_papers = get_top_papers(papers, user_query, top_n=project_count)

            ideas = []
            fallback_used = False
            for paper in top_papers:
                idea = make_project_idea(paper, skill_level)
                source_summary = paper.get("summary", "")
                similar_papers = get_top_papers(papers, source_summary, top_n=paper_count)
                idea["source_paper"] = paper
                idea["similar_papers"] = similar_papers
                fallback_used = fallback_used or idea.get("is_fallback", False)
                ideas.append(idea)

            st.session_state["results"] = ideas
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
    st.subheader("Recommended Student Projects")
    cols = st.columns(2)
    for i, idea in enumerate(st.session_state["results"]):
        with cols[i % 2]:
            show_project_card(idea)
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

    st.subheader("Trending Keywords")
    keywords = st.session_state["keywords"]
    if keywords:
        chart_df = pd.DataFrame(
            {"keyword": list(keywords.keys()), "count": list(keywords.values())}
        ).set_index("keyword")
        st.bar_chart(chart_df)

    export_text = build_export_text(
        domain, skill_level, semester, st.session_state["results"]
    )
    st.download_button(
        label="Download Results (.txt)",
        data=export_text,
        file_name="ai_project_recommendations.txt",
        mime="text/plain",
    )

if st.session_state["top_papers"]:
    st.subheader("Source Research Papers (arXiv)")
    for i, paper in enumerate(st.session_state["top_papers"], start=1):
        title = paper.get("title", "Untitled")
        link = paper.get("link", "")
        summary = paper.get("summary", "No summary available.")
        st.markdown(f"{i}. [{title}]({link})")
        with st.expander("Show summary"):
            st.write(summary)
