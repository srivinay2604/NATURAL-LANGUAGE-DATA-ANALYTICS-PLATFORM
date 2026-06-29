# 🦆 NL Analytics — Ask Your Data

NL Analytics is a full-stack, AI-powered Natural Language to SQL analytics platform. Users can ask questions in plain English to query structured database records via DuckDB or retrieve policy documentation using a semantic vector store (RAG), completely eliminating the need for SQL knowledge.

## 🏗️ Architecture

```
                  ┌───────────────────────────┐
                  │       Streamlit UI        │◀┐
                  └───────────────────────────┘ │
                                │               │
                     User Input │               │ Displays
                                ▼               │ Charts & Answers
                  ┌───────────────────────────┐ │
                  │     LangGraph Agent       │─┘
                  └───────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼ (sql)                                         ▼ (rag)
┌────────────────┐                              ┌────────────────┐
│   Groq LLM     │                              │   ChromaDB     │
│(Llama 3.1 8B)  │                              │(Vector Database)│
└────────────────┘                              └────────────────┘
        │                                               │
        ▼                                               ▼
┌────────────────┐                              ┌────────────────┐
│    DuckDB      │                              │SentenceTransf. │
│(SQL Database)  │                              │  (Embeddings)  │
└────────────────┘                              └────────────────┘
```

## ⚙️ Core Pipeline Steps
1. **Semantic Cache Check**: Checks local Redis instance for identical/highly similar queries using cosine similarity. If cached, returns answers immediately.
2. **Intent Classification**: Evaluates if query relates to numerical aggregates (routed to SQL generation) or guidelines/policies (routed to RAG retrieval).
3. **SQL Generation & Execution**: Translates user query into SQL using Groq Llama 3.1, runs against in-memory DuckDB, and self-heals up to 3 times if query errors occur.
4. **RAG retrieval**: Searches ChromaDB using SentenceTransformers embeddings for policy matching.
5. **Plotly Visualization**: Generates suitable metrics, lines, bars, pies, or scatter plots dynamically based on schema traits.

---

## 📋 Prerequisites
- **Python 3.10+**
- **Redis** running locally (on default port `6379`)

---

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd nl_analytics
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Copy the `.env.example` template:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your API keys (see below).

4. **Start Redis Server**
   Ensure Redis is running locally:
   ```bash
   redis-server
   ```

5. **Run the Streamlit Application**
   ```bash
   streamlit run app.py
   ```

---

## 🔑 Getting Free API Keys

- **Groq API Key**: Go to [console.groq.com](https://console.groq.com/), sign up, and generate an API key.
- **Langfuse Keys** (Optional): Sign up on [cloud.langfuse.com](https://cloud.langfuse.com/), create a project, and generate API keys to enable observability tracing.

---

## 💡 Example Questions to Try

### SQL Queries
- *"Top 5 products by revenue"* (Generates bar chart)
- *"Monthly sales trend 2024"* (Generates line chart)
- *"Which region has highest profit?"* (Generates bar chart)
- *"Compare category performance"* (Generates bar/pie chart)

### RAG (Document Search) Queries
- *"What is our revenue policy?"* (Extracts text from `revenue_policy.txt`)
- *"What is the definition of profit margin?"* (Extracts formula from `kpi_definitions.txt`)
- *"What are the customer segment definitions?"* (Extracts rules from `company_guidelines.txt`)

---

## 🔧 Troubleshooting

- **Redis is Down**: If Redis is offline, the app logs a warning in the console and continues execution, bypassing the caching layer without crashing.
- **Langfuse Connection Issues**: If Langfuse is unreachable, the observability pipeline falls back silently to local logs, ensuring the user experience is unaffected.
- **SQL Error Retries**: The LangGraph state machine handles up to 3 self-healing attempts by feeding error codes back into Groq to repair incorrect SQL syntax dynamically.
- **ChromaDB SQLite issue**: If you encounter SQLite version conflicts with ChromaDB, ensure python is running with an updated SQLite version or set `IS_CHROMA_PERSISTENT=False`.
