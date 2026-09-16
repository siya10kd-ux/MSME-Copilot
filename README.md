# MSME Copilot

An AI operations agent for small manufacturers that turns invoices, purchase orders, inventory sheets, and production reports into actionable business decisions.

## Features

- Extract data from business documents
- Forecast inventory requirements
- Identify delayed suppliers
- Generate purchase orders
- Explain cash-flow risks
- Create daily production summaries
- Answer business questions via multi-agent workflow

## Architecture

Multi-agent LangGraph workflow with local Ollama LLMs:

```
Business → Document Agent → Finance Agent → Inventory Agent → Supplier Agent → Business Advisor
```

## Tech Stack

- **LangGraph** — agent orchestration
- **Ollama** — local LLM inference (qwen2.5-coder:7b-instruct)
- **LangChain** — LLM wrappers and prompts
- **ChromaDB** — document memory
- **SQLite** — structured business metrics
- **FastAPI** — backend API
- **React + Vite** — frontend UI

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) with `qwen2.5-coder:7b-instruct` pulled
- Node.js 18+ (for frontend)

### Backend

```bash
cd msme-copilot
pip install -r requirements.txt
python data/generate_synthetic_data.py
python main.py --check-ollama
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
msme-copilot/
├── agents/          # Document, Finance, Inventory, Supplier, Business Advisor
├── graph/           # LangGraph state, workflow, router
├── tools/           # OCR, CSV parser, PO generator, report generator
├── data/            # Raw, processed, sample datasets
├── db/              # ChromaDB vector store, SQLite store
├── config/          # Settings and prompts
├── frontend/        # React + Vite UI
├── main.py          # CLI entry point
└── api.py           # FastAPI backend
```

## Sample Data

Synthetic datasets are in `data/sample_datasets/` with a fixed random seed for reproducible demos.

## Usage

```bash
# Run workflow from CLI
python main.py --question "Which products are profitable but frequently delayed?"

# Start API server
uvicorn api:app --reload --port 8000
```
