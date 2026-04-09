# AI Research Project Recommender

A beginner-friendly Streamlit app that helps students discover project ideas from real arXiv research papers.

## Features

- Fetches live papers from arXiv by domain
- Ranks papers by semantic relevance (Sentence Transformers)
- Generates project ideas in free mode by default
- Optionally uses Anthropic API if `ANTHROPIC_API_KEY` is set
- Shows 10-15 similar papers per project
- Exports generated ideas to a `.txt` file

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

## Optional API Key

If you want Anthropic-based idea generation, set this environment variable:

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

If no key is set, the app runs in free mode.
