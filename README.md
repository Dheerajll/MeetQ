# MeetQ Web App

The backend + frontend of MeetQ: it ingests transcript chunks produced by
the LMA (Local Meeting Agent), cleans them, builds hierarchical meeting
summaries with structured extraction, and answers questions over meetings
via RAG. Fully local LLM inference through Ollama.

    LMA (chunks.json)  →  Cleaning  →  Hierarchical Summarization
                                     →  RAG indexing  →  Query / UI

---

## Features

- Transcript cleaning with two language paths:
  - English: code-based overlap removal (instant, 0 s)
  - Nepali / code-switched: LLM-based cleaning (handles broken Devanagari
    and mixed Nepali/English speech)
- Meeting-type detection (business / educational / podcast)
- Sliding-window hierarchical Map-Reduce summarization
- Structured extraction: key topics, decisions, action items
- Cross-lingual summarization (Nepali audio → English summary)
- RAG over transcripts (embeddings + retrieval + local LLM answers)
- JWT authentication, meetings/datasets management
- Built-in evaluation harness (ROUGE + LLM judge + deterministic metrics)

---

## Directory structure

    WebApp/
    ├── backend/
    │   ├── main.py                      # app entrypoint
    │   ├── config/
    │   │   └── ollama.py                # Ollama host/model config
    │   ├── app/
    │   │   ├── ai/
    │   │   │   └── ollama_client.py     # async Ollama client
    │   │   ├── api/routes/
    │   │   │   ├── auth_routes.py
    │   │   │   ├── dataset_routes.py
    │   │   │   ├── meeting_routes.py
    │   │   │   ├── query_routes.py
    │   │   │   └── summarize_routes.py
    │   │   ├── auth/
    │   │   │   └── jwt_utils.py
    │   │   ├── core/
    │   │   │   └── database.py          # async SQLAlchemy session
    │   │   ├── models/                  # dataset, meeting, summary,
    │   │   │   └── ...                  #   transcript, user
    │   │   ├── rag/
    │   │   │   ├── embeddings.py
    │   │   │   ├── llm.py
    │   │   │   └── retriever.py
    │   │   └── services/
    │   │       ├── cleaning/            # EN code path + NE LLM path
    │   │       │   └── ...
    │   │       ├── summarization/
    │   │       │   ├── type_detector.py
    │   │       │   ├── hierarchical.py  # sliding-window Map-Reduce
    │   │       │   ├── overview.py
    │   │       │   ├── extractor.py
    │   │       │   └── prompts.py
    │   │       ├── dataset_pipeline.py
    │   │       ├── dataset_query.py
    │   │       ├── dataset_summarization.py
    │   │       └── rag_service.py
    │   ├── eval_summarization.py        # EN summarization eval
    │   └── eval_nepali_summarization.py # NE cross-lingual eval
    └── frontend/
        └── pages: login, meetings, transcript, summary, query,
                   settings, dataset_summary, dataset_query, ...

---

## Requirements

- Python 3.10+
- PostgreSQL 14+
- Ollama running locally (model used in this project: llama3)
- Node.js + npm/pnpm for the frontend

Backend dependencies:

    pip install fastapi uvicorn sqlalchemy[asyncio] asyncpg \
                ollama python-jose[cryptography] pydantic \
                rouge-score numpy

---

## Installation

### 1. Database
    createdb meetq
    # apply migrations / create tables (users, meetings, datasets,
    # transcripts, summaries)

### 2. Ollama
    ollama pull llama3
    ollama serve          # keep running while the backend is up

### 3. Backend
    cd WebApp/backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    # environment
    export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/meetq"
    export OLLAMA_BASE_URL="http://localhost:11434"
    export OLLAMA_MODEL="llama3"
    export JWT_SECRET="change-me"

    uvicorn main:app --reload --port 8000

### 4. Frontend
    cd WebApp/frontend
    npm install
    npm run dev

---

## Core pipeline

### 1. Cleaning
Input: LMA `chunks.json` (`raw_text` with `[speaker N]` labels).

- English path: pure-code overlap removal between consecutive chunks
  (removes the 3 s boundary duplication). Runtime: ~0 s.
- Nepali / code-switched path: LLM-based cleaning that repairs broken
  Devanagari, normalizes disfluencies, and keeps embedded English terms.
  Runtime: ~6 min for 10 min of audio (acceptable as background work).

### 2. Summarization (hierarchical Map-Reduce)
- Level 1: chunks are grouped with a sliding window
  (group size 5, stride 4 → 1-chunk overlap) and each group is
  summarized. The overlap gives every group the previous group's tail
  context so no group starts mid-thought.
- Level 2+: partial summaries are reduced with the same sliding-window
  strategy (group size 4, stride 3) until one summary remains.
- Overview generation + structured extraction produce:
  key topics, decisions, action items.
- Redundancy from window overlap is removed by the REDUCE prompt.

### 3. RAG
Cleaned chunks are embedded and indexed. Query routes retrieve the
top-k relevant chunks and answer with the local LLM.

---

## Evaluation harness

Two eval scripts run the production pipeline fully in-memory
(zero DB writes):

### eval_summarization.py (English)
    python eval_summarization.py <chunks.json> --name ami_1 \
        --reference-summary <human_summary.txt>

Produces `eval_results/<name>/`:
- summary_eval.json   → ROUGE-1/2/L, compression, number preservation,
                        keyword coverage, LLM-judge scores, timings
- generated_summary.txt
- cleaned_transcript.txt

LLM judge rubric (1–5): coverage, accuracy, coherence, conciseness.

### eval_nepali_summarization.py (cross-lingual)
    python eval_nepali_summarization.py <chunks.json> --name nepali_1 \
        --reference-transcript <english_ref.txt>

Same outputs; ROUGE is skipped (no human Nepali summaries exist), and the
judge compares the generated English summary against the English reference
transcript.

### Validated results (this project)
| Domain              | WER    | Judge accuracy | ROUGE-1 |
|---------------------|--------|----------------|---------|
| English business    | 30.0%  | 5.0 / 5        | 0.217   |
| English educational | 8.3%   | 5.0 / 5        | n/a     |
| Nepali cross-lingual| —      | 5.0 / 5        | n/a     |

---

## Configuration knobs

| Setting                 | Default | Location                       |
|-------------------------|---------|--------------------------------|
| LEVEL1_GROUP_SIZE       | 5       | summarization/hierarchical.py  |
| LEVEL1_STRIDE           | 4       | summarization/hierarchical.py  |
| REDUCE_GROUP_SIZE       | 4       | summarization/hierarchical.py  |
| REDUCE_STRIDE           | 3       | summarization/hierarchical.py  |
| Ollama model            | llama3  | config/ollama.py               |
| Ollama timeout          | 600 s   | ai/ollama_client.py            |

---

## Troubleshooting

- Ollama timeouts on large groups → raise the timeout in
  ai/ollama_client.py to 600 s and keep the model warm
  (`ollama run llama3 ""` once before evals).
- Cleaning returns 0 chunks → verify chunks.json has non-empty raw_text
  and the language field is set.
- Summaries appear in Nepali for Nepali input → ensure prompts instruct
  English output (or that the judge evaluates cross-lingually).
- Empty ROUGE → confirm --reference-summary points to a plain-text file.