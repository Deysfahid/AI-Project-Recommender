# AI Research Project Recommender

A beginner-friendly Streamlit web app that suggests project ideas from real arXiv papers using semantic ranking and context-aware filtering.

## Live Demo

- https://ai-project-recommender.streamlit.app/

## What This App Does

The app supports two independent recommendation modes:

1. Search-based mode
- User enters a free-text query in Smart Search.
- App parses query tags (domain, type, area), fetches papers, ranks semantically, and generates project ideas.

2. Filter-based mode
- User uses sidebar fields (domain, skill level, language, project type, semester, goal).
- App fetches papers and applies multi-stage ranking and filtering based on those fields.

## Core Features

- Fetches research papers from arXiv API
- Semantic ranking using sentence-transformers (all-MiniLM-L6-v2)
- Strict + boosted filtering by:
  - domain
  - programming language
  - project type
- Skill-aware reranking (Beginner / Intermediate / Advanced)
- Semester-aware complexity filtering
- Relevance score (0 to 100 percent)
- Complexity score (1 to 10)
- Clickable source paper links per project
- Similar papers section (up to 30)
- Save/bookmark projects with session state
- Trending keywords chart
- Download results as .txt
- Active mode badge in UI:
  - Search-based
  - Filter-based

## How Ranking Works

### Pipeline (Filter Mode)

1. Fetch papers from arXiv
2. Semantic search ranking
3. Domain/language/type context filtering and boost
4. Skill-level rerank
5. Semester rerank
6. Complexity score filter by semester band
7. Generate final project ideas

### Semester to Complexity Mapping

- Semester 1 to 2: score 1 to 4 (Beginner)
- Semester 3 to 4: score 3 to 7 (Intermediate)
- Semester 5 to 6: score 5 to 9 (Advanced)
- Semester 7 to 8: score 7 to 10 (Research level)

## Technology Stack

- Python 3.11+
- Streamlit
- Pandas
- feedparser
- sentence-transformers
- scikit-learn
- Optional: Anthropic SDK (for LLM generation)

## Project Structure

```text
ai-recommender/
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- .env.example
|-- src/
|   |-- __init__.py
|   |-- api.py
|   |-- recommender.py
|   |-- helpers.py
|-- data/
|-- assets/
|-- tests/
```

## Setup

1. Create virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Run app

```powershell
streamlit run app.py
```

## Environment Variables

- ANTHROPIC_API_KEY (optional)

If not set, app still works in free fallback mode.

## Notes for Evaluation/Judging

- Uses real arXiv research metadata, not static mock data.
- Changing sidebar fields in Filter Mode actively changes ranking and final projects.
- Search Mode is independent from sidebar recommendation filters.
- Each project card shows both relevance and complexity for transparency.
