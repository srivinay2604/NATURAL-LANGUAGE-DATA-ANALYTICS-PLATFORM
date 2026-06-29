import os
import time
import logging
from groq import Groq
from dotenv import load_dotenv
from services.observability import log_span

load_dotenv()
logger = logging.getLogger(__name__)

# Model config
MODEL_NAME = "llama-3.1-8b-instant"

# Initializing Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key or "your_groq" in api_key:
    logger.warning("GROQ_API_KEY is not configured. LLM calls will fail.")
    client = None
else:
    client = Groq(api_key=api_key)

def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """
    Helper function to call Groq API with 30s timeout and return response text.
    """
    if not client:
        raise ValueError("Groq client is not initialized. Please set GROQ_API_KEY in your .env file.")
        
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=1024,
            timeout=30.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        raise e

def generate_sql(question: str, schema: str, trace=None) -> str:
    """
    Generates a SQL query based on the user question and the CSV schema.
    """
    system_prompt = (
        "You are an expert SQL assistant. Your job is to translate natural language questions "
        "into valid SQL queries that will run on a DuckDB database containing a table named 'df'.\n\n"
        "DATABASE SCHEMA:\n"
        f"{schema}\n\n"
        "RULES:\n"
        "1. Return ONLY the executable SQL query. Do NOT wrap the query in markdown code blocks, do NOT write ```sql or ```, and do NOT include any comments or explanations.\n"
        "2. The table name is always 'df'. DuckDB reads the pandas DataFrame as a table named 'df'.\n"
        "3. Use standard ANSI SQL syntax. Avoid complex window functions unless absolutely necessary.\n"
        "4. Always use double quotes for column names that contain spaces or special characters.\n"
        "5. Ensure the SQL query uses ONLY columns that actually exist in the DATABASE SCHEMA above.\n"
        "6. In DuckDB, to format or truncate dates, use STRFTIME(CAST(date AS DATE), '%Y-%m') or EXTRACT(YEAR FROM CAST(date AS DATE)). Never use strptime on DATE columns."
    )
    
    start_time = time.time()
    try:
        sql = _call_groq(system_prompt, question)
        # Clean potential markdown wrapping just in case
        if sql.startswith("```"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        latency = time.time() - start_time
        log_span(trace, "generate_sql", {"question": question, "schema": schema}, {"sql": sql}, latency)
        return sql
    except Exception as e:
        latency = time.time() - start_time
        log_span(trace, "generate_sql_error", {"question": question}, {"error": str(e)}, latency)
        raise e

def fix_sql(question: str, bad_sql: str, error: str, trace=None) -> str:
    """
    Fixes a failed SQL query based on the error message.
    """
    system_prompt = (
        "You are an expert SQL debugging assistant. Fix the provided SQL query that failed to execute "
        "on DuckDB (table name 'df').\n\n"
        "RULES:\n"
        "1. Return ONLY the corrected SQL query. Do NOT wrap the query in markdown code blocks, do NOT write ```sql or ```, and do NOT include any comments or explanations.\n"
        "2. The table name is always 'df'.\n"
        "3. Always use double quotes for column names that contain spaces or special characters.\n"
        "4. In DuckDB, to format dates use STRFTIME(CAST(date AS DATE), '%Y-%m') or EXTRACT(YEAR FROM CAST(date AS DATE)). Never use strptime on DATE columns."
    )
    
    user_prompt = (
        f"Original Question: {question}\n"
        f"Failed SQL Query: {bad_sql}\n"
        f"DuckDB Error Message: {error}\n\n"
        "Fix this SQL query. Return only corrected SQL."
    )
    
    start_time = time.time()
    try:
        sql = _call_groq(system_prompt, user_prompt)
        if sql.startswith("```"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        latency = time.time() - start_time
        log_span(trace, "fix_sql", {"bad_sql": bad_sql, "error": error}, {"sql": sql}, latency)
        return sql
    except Exception as e:
        latency = time.time() - start_time
        log_span(trace, "fix_sql_error", {"bad_sql": bad_sql}, {"error": str(e)}, latency)
        raise e

def classify_intent(question: str, trace=None) -> str:
    """
    Classifies the intent of the question as 'sql' or 'rag'.
    """
    system_prompt = (
        "Classify this question as either 'sql' (questions about "
        "data, numbers, trends, comparisons, aggregations) or "
        "'rag' (questions about policies, definitions, guidelines, "
        "rules). Reply with only one word: sql or rag."
    )
    
    start_time = time.time()
    try:
        intent = _call_groq(system_prompt, question).lower().strip()
        # Clean any punctuation
        intent = "".join(c for c in intent if c.isalnum())
        latency = time.time() - start_time
        log_span(trace, "classify_intent", {"question": question}, {"intent": intent}, latency)
        return intent if intent in ["sql", "rag"] else "sql"
    except Exception as e:
        latency = time.time() - start_time
        log_span(trace, "classify_intent_error", {"question": question}, {"error": str(e)}, latency)
        raise e

def answer_from_rag(question: str, context: str, trace=None) -> str:
    """
    Synthesizes an answer using retrieved documentation chunks.
    """
    system_prompt = (
        "Answer the question using only the provided context. Be concise and accurate. "
        "If the answer is not in the context, say so clearly (e.g., 'I cannot find the answer in the provided guidelines.')."
    )
    
    user_prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    
    start_time = time.time()
    try:
        answer = _call_groq(system_prompt, user_prompt)
        latency = time.time() - start_time
        log_span(trace, "answer_from_rag", {"question": question, "context": context}, {"answer": answer}, latency)
        return answer
    except Exception as e:
        latency = time.time() - start_time
        log_span(trace, "answer_from_rag_error", {"question": question}, {"error": str(e)}, latency)
        raise e
