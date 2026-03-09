# 🤖 Context-Aware Personal Executive

> An AI-powered personal assistant that searches across your emails, documents, and notes to answer questions intelligently.

**Built for Hackathons** - Clean, modular architecture designed for 3 developers to work independently without conflicts.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Developer Responsibilities](#developer-responsibilities)
- [Quick Start](#quick-start)
- [Running the Application](#running-the-application)
- [Development Guide](#development-guide)
- [API Documentation](#api-documentation)

---

## 🎯 Overview

The Context-Aware Personal Executive is an intelligent system that:

- 🔍 Searches across multiple data sources (emails, PDFs, CSV notes)
- 🤖 Uses AI to understand queries and select appropriate tools
- 💬 Provides a clean chat interface for interaction
- 🔧 Follows a modular agent + tool architecture

**Data Flow:**
```
User Query → Frontend → AI Agent → Tool Selection → Data Tools → Response Synthesis → User
```

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ ← Developer 3
│  (UI Layer) │
└──────┬──────┘
       │
┌──────▼──────┐
│  AI Agent   │ ← Developer 2
│  (Decision) │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│      Data Tools              │ ← Developer 1
├──────────────────────────────┤
│ • search_email(query)        │
│ • search_pdf(query)          │
│ • search_csv(query)          │
└──────────────────────────────┘
```

**Key Components:**

1. **Data Tools** - Specialized search functions for different data sources
2. **AI Agent** - OpenAI-powered agent that selects and orchestrates tools
3. **Frontend** - User interface (Streamlit or Flask)

---

## 📁 Project Structure

```
Context-Aware-Personal-Executive/
│
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config.py                   # Shared configuration
├── main.py                     # Main entry point
│
├── tools/                      # 👤 Developer 1's workspace
│   ├── __init__.py
│   ├── base_tool.py           # Base class for tools
│   ├── email_tool.py          # Email search implementation
│   ├── pdf_tool.py            # PDF search implementation
│   └── csv_tool.py            # CSV search implementation
│
├── agent/                      # 👤 Developer 2's workspace
│   ├── __init__.py
│   ├── llm_agent.py           # Main AI agent logic
│   └── tool_registry.py       # Tool registration system
│
├── frontend/                   # 👤 Developer 3's workspace
│   ├── __init__.py
│   ├── streamlit_app.py       # Streamlit UI
│   └── flask_app.py           # Flask alternative
│
├── sample_data/                # Sample data files
│   ├── emails.json            # Sample emails
│   ├── notes.csv              # Sample CSV notes
│   └── README_PDF.txt         # PDF placeholder
│
└── utils/                      # Shared utilities
    ├── __init__.py
    └── helpers.py             # Helper functions
```

---

## 👥 Developer Responsibilities

### Developer 1: Data Tools 🔧

**Folder:** `tools/`

**Tasks:**
- Implement `search_email(query)` - Search through email data
- Implement `search_pdf(query)` - Extract and search PDF content
- Implement `search_csv(query)` - Query CSV/tabular data
- Add relevance scoring and ranking
- Handle edge cases and errors

**Files to modify:**
- [tools/email_tool.py](tools/email_tool.py)
- [tools/pdf_tool.py](tools/pdf_tool.py)
- [tools/csv_tool.py](tools/csv_tool.py)

**Testing:**
```bash
python tools/email_tool.py    # Test email search
python tools/pdf_tool.py      # Test PDF search
python tools/csv_tool.py      # Test CSV search
```

---

### Developer 2: AI Agent 🤖

**Folder:** `agent/`

**Tasks:**
- Implement OpenAI function calling logic
- Build tool selection strategy
- Synthesize responses from multiple tools
- Handle conversation context
- Error handling and fallbacks

**Files to modify:**
- [agent/llm_agent.py](agent/llm_agent.py)
- [agent/tool_registry.py](agent/tool_registry.py) (if adding features)

**Testing:**
```bash
python agent/llm_agent.py     # Test agent directly
python main.py --test         # Full integration test
```

---

### Developer 3: Frontend 💻

**Folder:** `frontend/`

**Tasks:**
- Build chat interface (Streamlit OR Flask)
- Display conversation history
- Handle user input and responses
- Add loading states and error messages
- Style the UI

**Files to modify:**
- [frontend/streamlit_app.py](frontend/streamlit_app.py) (for Streamlit)
- [frontend/flask_app.py](frontend/flask_app.py) (for Flask)

**Testing:**
```bash
streamlit run frontend/streamlit_app.py   # Test Streamlit UI
python frontend/flask_app.py              # Test Flask UI
```

---

## 🚀 Quick Start

### 1. Clone or Setup

```bash
cd Context-Aware-Personal-Executive
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set OpenAI API Key

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Mac/Linux:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Or create a `.env` file:**
```
OPENAI_API_KEY=your-api-key-here
```

### 4. Run the Application

```bash
# CLI Mode (quick testing)
python main.py

# Streamlit UI (recommended)
python main.py --streamlit

# Flask UI (alternative)
python main.py --flask

# Run tests
python main.py --test
```

---

## 🎮 Running the Application

### Option 1: CLI Mode (Quick Testing)

```bash
python main.py
```

Interactive command-line interface for testing queries.

### Option 2: Streamlit UI (Recommended)

```bash
python main.py --streamlit
# Or directly:
streamlit run frontend/streamlit_app.py
```

Access at: `http://localhost:8501`

### Option 3: Flask Web UI

```bash
python main.py --flask
# Or directly:
python frontend/flask_app.py
```

Access at: `http://localhost:5000`

### Run Tests

```bash
python main.py --test
```

Tests all components (tools, agent, integration).

---

## 💻 Development Guide

### For Developer 1 (Data Tools)

1. **Email Tool:**
   - Load [sample_data/emails.json](sample_data/emails.json)
   - Implement keyword + semantic search
   - Return top N relevant emails

2. **PDF Tool:**
   - Install: `pip install PyPDF2` or `pdfplumber`
   - Extract text from PDFs
   - Search by keywords or semantic similarity
   - Return excerpts with page numbers

3. **CSV Tool:**
   - Load [sample_data/notes.csv](sample_data/notes.csv)
   - Search across all columns
   - Return matching rows with context

**Key Files:**
- [tools/email_tool.py](tools/email_tool.py)
- [tools/pdf_tool.py](tools/pdf_tool.py)
- [tools/csv_tool.py](tools/csv_tool.py)

---

### For Developer 2 (AI Agent)

1. **Agent Logic:**
   - Use OpenAI's function calling API
   - Define tool specifications
   - Handle tool selection and execution
   - Synthesize final answers

2. **Tool Registry:**
   - Register tools from Developer 1
   - Provide tool specs to OpenAI
   - Execute tool calls

**Key Files:**
- [agent/llm_agent.py](agent/llm_agent.py)
- [agent/tool_registry.py](agent/tool_registry.py)

**Example OpenAI Integration:**
```python
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=messages,
    tools=tool_specs,
    tool_choice="auto"
)
```

---

### For Developer 3 (Frontend)

1. **Streamlit UI:**
   - Use `st.chat_message()` for chat interface
   - `st.chat_input()` for user input
   - Display conversation history
   - Add sidebar with settings

2. **Flask UI:**
   - Create HTML template with chat interface
   - POST endpoint for queries
   - WebSocket for real-time updates (optional)
   - Session management

**Key Files:**
- [frontend/streamlit_app.py](frontend/streamlit_app.py)
- [frontend/flask_app.py](frontend/flask_app.py)

---

## 📚 API Documentation

### Tool Functions

Each tool has the same signature:

```python
def search_tool(query: str) -> List[Dict[str, Any]]:
    """
    Search a specific data source
    
    Args:
        query: User's search query
    
    Returns:
        List of results with relevance scores
    """
```

**Example:**
```python
from tools import search_email, search_pdf, search_csv

results = search_email("meeting tomorrow")
# Returns: [{"from": "...", "subject": "...", "relevance_score": 0.85}, ...]
```

---

### Agent API

```python
from agent import ContextAwareAgent

agent = ContextAwareAgent()
response = agent.process_query("Find emails about the project")
# Returns: Synthesized answer from the agent
```

---

## 🔧 Configuration

Edit [config.py](config.py) to customize:

```python
# OpenAI settings
OPENAI_MODEL = "gpt-4-turbo-preview"
AGENT_TEMPERATURE = 0.7

# Search settings
MAX_SEARCH_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7

# Ports
STREAMLIT_PORT = 8501
FLASK_PORT = 5000
```

---

## 🎯 Development Tips

### Avoiding Merge Conflicts

Each developer works in their own folder:
- Developer 1: `tools/`
- Developer 2: `agent/`
- Developer 3: `frontend/`

Shared files (`config.py`, `utils/`) should be modified carefully.

### Testing Workflow

1. **Test individually:** Each developer tests their module
2. **Integration test:** Use `python main.py --test`
3. **End-to-end test:** Run full UI and test queries

### Without OpenAI API Key

The system includes a `SimpleAgent` fallback that uses keyword matching instead of AI. Perfect for testing without API costs.

---

## 📝 Example Queries

Try these queries once the system is running:

- "Find emails about project meetings"
- "What did Sarah say about the hackathon?"
- "Show me notes about budget planning"
- "Search PDFs for technical specifications"
- "When is my dentist appointment?"

---

## 🚀 Next Steps

### Phase 1: Core Features (Hackathon Day 1-2)
- ✅ Project structure
- ⬜ Implement all three tools
- ⬜ Working AI agent
- ⬜ Basic frontend

### Phase 2: Polish (Hackathon Day 2-3)
- ⬜ Improve search relevance
- ⬜ Better UI/UX
- ⬜ Error handling
- ⬜ Demo preparation

### Phase 3: Extensions (If time permits)
- ⬜ Semantic search with embeddings
- ⬜ Calendar integration
- ⬜ Voice input
- ⬜ Mobile UI

---

## 🤝 Team Collaboration

### Git Workflow

```bash
# Developer 1
git checkout -b feature/data-tools
# Work on tools/
git commit -am "Implement email search"
git push origin feature/data-tools

# Developer 2
git checkout -b feature/ai-agent
# Work on agent/
git commit -am "Add OpenAI function calling"
git push origin feature/ai-agent

# Developer 3
git checkout -b feature/frontend
# Work on frontend/
git commit -am "Build Streamlit UI"
git push origin feature/frontend
```

### Communication

- **Daily standups:** What did you do? What will you do? Blockers?
- **Shared docs:** Keep a shared doc for API changes
- **Test early:** Don't wait until the end to integrate

---

## 📄 License

MIT License - Feel free to use for your hackathon!

---

## 🙋 Questions?

- Check the inline code comments - every file has detailed TODOs
- Look at [main.py](main.py) for example usage
- Test individual components before integration

---

**Built with ❤️ for hackathons. Good luck! 🚀**