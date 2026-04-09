# AI Research Project Recommender

A beginner-friendly Streamlit app that helps students discover project ideas from real arXiv research papers.

## Technology Stack

- Language: Python 3.11+
- Web Framework: Streamlit
- Data Handling: Pandas
- Research Data Source: arXiv API (Atom feed via `feedparser`)
- Relevance Ranking: Sentence Transformers (`all-MiniLM-L6-v2`) + Scikit-learn cosine similarity
- Optional LLM Provider: Anthropic Claude (`claude-haiku-3-5-20251001`)
- Version Control and Hosting: Git + GitHub

## Features

- Fetches live papers from arXiv by domain
- Ranks papers by semantic relevance (Sentence Transformers)
- Generates project ideas in free mode by default
- Optionally uses Anthropic API if `ANTHROPIC_API_KEY` is set
- Shows 10-15 similar papers per project
- Exports generated ideas to a `.txt` file

## Platforms Used

- Local Development: VS Code + PowerShell + Python virtual environment
- Source Code Hosting: GitHub
- Deployment Platform: Streamlit Community Cloud (recommended free option)

## Project Structure

```text
ai-recommender/
|
|-- app.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- .env.example
|
|-- src/
|   |-- __init__.py
|   |-- helpers.py
|   |-- recommender.py
|   |-- api.py
|
|-- data/
|-- assets/
|-- tests/
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app:

```powershell
streamlit run app.py
```

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud and sign in with GitHub.
3. Click `New app` and select your repository.
4. Set the main file path to `app.py`.
5. Click `Deploy`.

The app works in free mode without any API key. If you add Anthropic credentials, it will use Claude for idea generation.

## Optional API Key

If you want Anthropic-based idea generation, set this environment variable:

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

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
