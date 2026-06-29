from typing import Any, TypedDict

class AgentState(TypedDict):
    question: str        # original user question
    intent: str          # "sql" or "rag"
    schema: str          # CSV column descriptions
    sql_query: str       # generated SQL
    sql_result: Any      # DataFrame from DuckDB
    sql_error: str       # error message if SQL fails
    retry_count: int     # number of SQL retries so far
    rag_context: str     # retrieved document chunks
    rag_answer: str      # LLM answer from documents
    chart_type: str      # bar/line/pie/scatter/table
    final_answer: str    # answer shown to user
    cached: bool         # whether answer came from cache
    trace_id: str        # Langfuse trace ID
