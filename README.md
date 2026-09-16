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

If no document is uploaded, the Document Agent is skipped. Finance, Inventory, and Supplier still run on existing database data, then the Business Advisor answers.

## Tech Stack

- **LangGraph** — agent orchestration
- **Ollama** — local LLM inference (model names in `config/settings.py`)
- **LangChain** — LLM wrappers and prompts
- **ChromaDB** — document memory
- **SQLite** — structured business metrics
- **Streamlit** — frontend UI

## Setup

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) with the models listed in `config/settings.py`

### Install

```bash
pip install -r requirements.txt
python data/generate_synthetic_data.py
```

### Run the UI

```bash
streamlit run frontend/app.py
```

The Streamlit app calls backend modules (`main.py`, SQLite store, PO and report tools). It does not embed LangGraph agents in the UI.

### CLI

```bash
python main.py --question "Which products are profitable but frequently delayed?"
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
├── frontend/        # Streamlit UI
└── main.py          # CLI / workflow entry point
```

## Sample Data

Synthetic datasets are in `data/sample_datasets/`. `data/generate_synthetic_data.py` uses a fixed random seed (`RANDOM_SEED` in `config/settings.py`).
