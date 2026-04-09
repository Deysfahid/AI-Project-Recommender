# AI Research Project Recommender

A beginner-friendly Streamlit web app that helps students discover hackathon-ready project ideas from real arXiv papers.

<<<<<<< HEAD
## Technology Stack

- Language: Python 3.11+
- Web Framework: Streamlit
- Data Handling: Pandas
- Research Data Source: arXiv API (Atom feed via `feedparser`)
- Relevance Ranking: Sentence Transformers (`all-MiniLM-L6-v2`) + Scikit-learn cosine similarity
- Optional LLM Provider: Anthropic Claude (`claude-haiku-3-5-20251001`)
- Version Control and Hosting: Git + GitHub

## Features
=======
Users select domain, difficulty, programming preferences, and project goals. The app fetches papers, ranks relevance, generates ideas, explains why each idea matches, and allows bookmarking.
>>>>>>> 96706c1 (Updated features (UI improvements + scoring + filtering))

## Key Features

- Live arXiv integration (Atom feed parsing via `feedparser`)
- Semantic relevance ranking with `all-MiniLM-L6-v2` embeddings
- Skill-aware reranking so Beginner, Intermediate, and Advanced produce different project sets
- Relevance score per project (`0%` to `100%`)
- Clickable source paper link on each project card
- Smart dynamic explanation (`Why this project?`) based on:
	- selected domain
	- selected skill level
	- paper summary
	- relevance score
- Difficulty-based filtering before rendering (not just display)
- Save / bookmark projects using `st.session_state`
- Separate Saved Projects section with clear option
- Similar paper exploration (`10`-`15` papers per project)
- Trending keyword chart
- Export generated projects as `.txt`
- Free mode supported (no paid API key required)
- Automatic one-time refetch when stale empty cached results are detected

## Technology Stack

- Language: Python 3.11+
- Frontend / App Framework: Streamlit
- Data & Visualization: Pandas, Streamlit charts
- Research Source: arXiv API (`export.arxiv.org`)
- Feed Parsing: `feedparser`
- Semantic Search:
	- `sentence-transformers` (`all-MiniLM-L6-v2`)
	- `scikit-learn` cosine similarity
- Optional LLM Provider: Anthropic Claude (`claude-haiku-3-5-20251001`)
- Version Control: Git + GitHub
- Deployment: Streamlit Community Cloud

## Platforms Used

- Local Development: VS Code + PowerShell + Python virtual environment
- Source Code Hosting: GitHub
- Deployment Platform: Streamlit Community Cloud (recommended free option)

## Project Structure

```text
ai-recommender/
|
|-- app.py                  # Streamlit UI (cards, filters, bookmarks, charts)
|-- requirements.txt        # Python dependencies
|-- README.md
|-- .gitignore
|-- .env.example
|
|-- src/
|   |-- __init__.py
|   |-- api.py              # arXiv fetching and parsing
|   |-- recommender.py      # ranking + score normalization + skill-aware reranking + keywords
|   |-- helpers.py          # idea generation + difficulty normalization + smart explanation
|
|-- data/                   # optional future storage
|-- assets/                 # optional images/static files
|-- tests/                  # optional tests
```

## User Inputs

The sidebar includes:

- Domain
- Skill level (`Beginner`, `Intermediate`, `Advanced`)
- Programming language
- Project type
- Project goal
- Semester
- Number of project ideas
- Number of similar papers (`10`-`15`)

## How Recommendations Become Different Per Skill Level

The app uses two layers to avoid repetitive outputs across levels:

- Query conditioning: the user query includes level-specific context terms.
- Skill-aware reranking: candidate papers are reranked with level-focused keyword weighting.

Examples:

- Beginner favors papers with terms like tutorial, survey, baseline, overview.
- Intermediate favors implementation, evaluation, framework, analysis.
- Advanced favors optimization, benchmark, novel, state-of-the-art.

After reranking, difficulty filtering is applied before rendering.

## UI/UX Highlights

- 2-column project card layout
- Emoji-enhanced sections and labels
- Difficulty color coding:
	- Beginner -> green
	- Intermediate -> orange
	- Advanced -> red
- Clear dividers/spacings for scanability

## Setup (Local)

### 1) Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Run the app

```powershell
streamlit run app.py
```

<<<<<<< HEAD
## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and sign in with GitHub.
3. Click `New app` and select your repository.
4. Set the main file path to `app.py`.
5. Click `Deploy`.

The app works in free mode without any API key. If you add Anthropic credentials, it will use Claude for idea generation.

## Optional API Key
=======
## Free Mode vs API Mode
>>>>>>> 96706c1 (Updated features (UI improvements + scoring + filtering))

### Free mode (default)

- Works without any API key
- Uses fallback idea generation logic
- Keeps full paper fetch + ranking + bookmarks + charts

### Optional Anthropic mode

Set environment variable:

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

<<<<<<< HEAD
If no key is set, the app runs in free mode.

## Environment Variables

- `ANTHROPIC_API_KEY` (optional): Enables Anthropic-powered project idea generation.

You can copy values from `.env.example` when setting up your environment.

## Recommended README Additions (Checklist)

- Add a live demo URL after deployment.
- Add 2-3 screenshots or a short demo GIF.
- Add a short roadmap section (planned improvements).
- Add contribution guidelines if others will collaborate.
- Add license information (`MIT` is common for student projects).
=======
If the key is unavailable or fails, the app safely falls back to free mode.

## Deployment (Streamlit Community Cloud)

### 1) Push code to GitHub

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 2) Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository and branch
5. Set main file path to `app.py`
6. Click **Deploy**

## Environment Variables

- `ANTHROPIC_API_KEY` (optional)

Use `.env.example` as a reference.

## Troubleshooting

- If no papers are returned due to SSL certificate issues, the app includes a fallback request path for arXiv fetch.
- If some domains show no papers temporarily, the app clears stale fetch cache once and retries automatically.
- If embedding model dependencies are unavailable locally, ranking gracefully falls back to keyword overlap scoring.

## Future Enhancements

- Add stronger filtering (time budget, team size, compute budget)
- Add unit tests in `tests/`
- Add one-click export to Markdown / PDF
- Add project comparison mode
>>>>>>> 96706c1 (Updated features (UI improvements + scoring + filtering))
