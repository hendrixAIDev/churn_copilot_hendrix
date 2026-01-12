# ChurnPilot

AI-powered credit card churning management system. Replace spreadsheet chaos with intelligent extraction and actionable insights.

## MVP Features

- **Paste & Parse**: Paste card terms, emails, or T&C text → get structured data
- **AI Extraction**: Claude extracts card name, issuer, annual fee, SUB details, and credits
- **Dashboard**: View all cards with next action dates highlighted

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key

### Installation

```bash
# Clone and enter directory
cd churn_copilot

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set API key
set ANTHROPIC_API_KEY=your-key-here  # Windows
# export ANTHROPIC_API_KEY=your-key-here  # macOS/Linux
```

### Run

```bash
streamlit run src/ui/app.py
```

## Project Structure

```
churn_copilot/
├── src/
│   ├── core/               # Business logic (UI-agnostic)
│   │   ├── models.py       # Pydantic data models
│   │   ├── extractor.py    # AI extraction via Anthropic
│   │   ├── storage.py      # JSON/SQLite persistence
│   │   └── prompts.py      # AI prompt templates
│   └── ui/                 # Streamlit frontend
│       └── app.py
├── data/                   # Local data storage
├── tests/                  # Unit tests
├── CLAUDE.md               # Development guidelines
├── requirements.txt
└── README.md
```

## Architecture

The core extraction logic is **decoupled from the UI layer**, enabling:

- Swap Streamlit for React/Next.js without rewriting AI logic
- Unit test extraction independently
- Reuse core module for CLI tools or APIs

## Roadmap

### MVP (Current)
- [x] Project structure
- [ ] Paste & Parse interface
- [ ] AI extraction pipeline
- [ ] Basic dashboard table

### Phase 2
- [ ] Email ingestion
- [ ] PDF statement parsing
- [ ] SQLite persistence

### Phase 3
- [ ] Proactive alerts
- [ ] Chase 5/24 tracker
- [ ] RAG-based strategy advisor

## License

Private - All rights reserved
