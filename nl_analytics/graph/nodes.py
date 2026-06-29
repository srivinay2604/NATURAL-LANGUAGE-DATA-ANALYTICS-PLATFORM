import logging
import pandas as pd
from graph.state import AgentState
from services import llm, database, vector_store, cache, observability
from utils import intent_classifier

logger = logging.getLogger(__name__)

def detect_chart_type(df: pd.DataFrame, question: str) -> str:
    """
    Heuristically determines the best Plotly Express chart type for the given DataFrame.
    """
    if df is None or df.empty:
        return "table"
        
    num_rows, num_cols = df.shape
    
    # 1. Single cell -> metric card
    if num_rows == 1 and num_cols == 1:
        return "metric"
        
    # 2. Contains date/month column -> line trend
    date_keywords = ['date', 'month', 'year', 'quarter', 'day']
    date_cols = [col for col in df.columns if any(kw in col.lower() for kw in date_keywords)]
    if date_cols:
        return "line"
        
    # 3. Share or percentage queries -> pie chart
    question_lower = question.lower()
    has_share_word = any(kw in question_lower for kw in ["share", "percent", "percentage", "portion"])
    has_share_col = any("share" in str(col).lower() or "percent" in str(col).lower() for col in df.columns)
    if (has_share_word or has_share_col) and num_cols >= 2:
        return "pie"
        
    # 4. Two numeric columns -> scatter plot
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if len(numeric_cols) >= 2 and num_cols == 2:
        return "scatter"
        
    # 5. Exactly 2 columns: Category + Number -> bar chart
    if num_cols == 2:
        non_numeric_cols = [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])]
        if len(non_numeric_cols) == 1 and len(numeric_cols) == 1:
            return "bar"
            
    # 6. More than 5 columns -> styled table
    if num_cols > 5:
        return "table"
        
    # Default fallback
    return "bar"

# ----------------- NODES -----------------

def cache_check_node(state: AgentState) -> dict:
    """
    NODE 1: Checks Redis for a semantically similar query cache hit.
    """
    question = state.get("question", "")
    logger.info(f"--- NODE 1: Checking Cache for '{question}' ---")
    
    try:
        # Embed question
        question_vector = vector_store.embed(question)
        cached_result = cache.semantic_search(question_vector)
        
        if cached_result:
            logger.info("Semantic cache hit found!")
            sql_res_raw = cached_result.get("sql_result")
            sql_result = pd.DataFrame(sql_res_raw) if sql_res_raw is not None else None
            
            return {
                "cached": True,
                "final_answer": cached_result.get("final_answer", ""),
                "sql_result": sql_result,
                "chart_type": cached_result.get("chart_type", "table"),
                "sql_query": cached_result.get("sql_query", ""),
                "intent": cached_result.get("intent", "sql")
            }
    except Exception as e:
        logger.warning(f"Cache check failed: {e}. Continuing with standard workflow.")
        
    return {"cached": False}

def intent_classifier_node(state: AgentState) -> dict:
    """
    NODE 2: Classifies the question as 'sql' or 'rag'.
    """
    question = state.get("question", "")
    logger.info(f"--- NODE 2: Classifying Intent for '{question}' ---")
    
    trace = observability.active_traces.get(state.get("trace_id"))
    
    # Classify intent with fallback heuristics
    intent = intent_classifier.classify_intent(
        question, 
        llm_classifier_func=lambda q: llm.classify_intent(q, trace=trace)
    )
    
    logger.info(f"Classified intent: {intent}")
    return {"intent": intent}

def sql_generator_node(state: AgentState) -> dict:
    """
    NODE 3: Generates the SQL query based on the CSV schema.
    """
    question = state.get("question", "")
    schema = state.get("schema", "")
    logger.info("--- NODE 3: Generating SQL Query ---")
    
    trace = observability.active_traces.get(state.get("trace_id"))
    
    try:
        sql_query = llm.generate_sql(question, schema, trace=trace)
        logger.info(f"Generated SQL: {sql_query}")
        return {"sql_query": sql_query}
    except Exception as e:
        logger.error(f"SQL Generation failed: {e}")
        return {"sql_error": str(e), "sql_query": ""}

def sql_executor_node(state: AgentState) -> dict:
    """
    NODE 4: Executes the SQL query on DuckDB.
    """
    sql_query = state.get("sql_query", "")
    sql_error = state.get("sql_error", "")
    question = state.get("question", "")
    logger.info(f"--- NODE 4: Executing SQL: {sql_query} ---")

    trace = observability.active_traces.get(state.get("trace_id"))

    # If SQL generator already failed, propagate its real error
    if not sql_query and sql_error:
        logger.error(f"SQL Generator failed upstream: {sql_error}")
        return {"sql_error": f"SQL generation failed: {sql_error}", "sql_result": None}

    if not sql_query:
        return {"sql_error": "No SQL query was generated by the LLM.", "sql_result": None}

    try:
        df = database.execute_query(sql_query, trace=trace)
        chart_type = detect_chart_type(df, question)
        
        # Synthesize a final answer explaining the SQL results if relevant
        final_answer = f"Found {len(df)} matching rows in the database."
        if df.shape == (1, 1):
            val = df.iloc[0, 0]
            col = df.columns[0]
            final_answer = f"The resulting value for {col} is **{val}**."
            
        logger.info(f"SQL executed successfully. Chart type: {chart_type}")
        return {
            "sql_result": df, 
            "sql_error": "", 
            "chart_type": chart_type,
            "final_answer": final_answer
        }
    except Exception as e:
        logger.warning(f"SQL execution failed: {e}")
        return {"sql_error": str(e), "sql_result": None}

def sql_fix_node(state: AgentState) -> dict:
    """
    NODE 5: Fixes a failed SQL query using LLM repair capabilities.
    """
    question = state.get("question", "")
    sql_query = state.get("sql_query", "")
    sql_error = state.get("sql_error", "")
    retry_count = state.get("retry_count", 0)
    
    logger.info(f"--- NODE 5: Fixing SQL (Retry {retry_count + 1}/3) ---")
    trace = observability.active_traces.get(state.get("trace_id"))
    
    try:
        fixed_query = llm.fix_sql(question, sql_query, sql_error, trace=trace)
        logger.info(f"Repaired SQL: {fixed_query}")
        return {
            "sql_query": fixed_query, 
            "retry_count": retry_count + 1
        }
    except Exception as e:
        logger.error(f"SQL Repair failed: {e}")
        return {
            "sql_error": f"Repair failed: {str(e)}", 
            "retry_count": retry_count + 1
        }

def rag_retriever_node(state: AgentState) -> dict:
    """
    NODE 6: Retrieves relevant context from the vector database.
    """
    question = state.get("question", "")
    logger.info("--- NODE 6: Retrieving Document Context ---")
    
    try:
        results = vector_store.search(question, n_results=5)
        rag_context = "\n\n".join(results)
        logger.info(f"Retrieved {len(results)} relevant document chunks.")
        return {"rag_context": rag_context}
    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return {"rag_context": f"Failed to retrieve context: {str(e)}"}

def rag_answer_node(state: AgentState) -> dict:
    """
    NODE 7: Synthesizes an answer using the retrieved context.
    """
    question = state.get("question", "")
    rag_context = state.get("rag_context", "")
    logger.info("--- NODE 7: Generating Answer from Context ---")
    
    trace = observability.active_traces.get(state.get("trace_id"))
    
    try:
        answer = llm.answer_from_rag(question, rag_context, trace=trace)
        return {
            "rag_answer": answer,
            "final_answer": answer
        }
    except Exception as e:
        logger.error(f"RAG generation failed: {e}")
        err_msg = f"Failed to generate answer from documents: {str(e)}"
        return {
            "rag_answer": err_msg,
            "final_answer": err_msg
        }

def cache_save_node(state: AgentState) -> dict:
    """
    NODE 8: Saves successful results into the Redis cache.
    """
    question = state.get("question", "")
    logger.info("--- NODE 8: Saving Query Result to Cache ---")
    
    try:
        sql_res = state.get("sql_result")
        sql_res_serializable = None
        if sql_res is not None and isinstance(sql_res, pd.DataFrame):
            sql_res_serializable = sql_res.to_dict(orient="records")
            
        result_payload = {
            "final_answer": state.get("final_answer", ""),
            "sql_result": sql_res_serializable,
            "chart_type": state.get("chart_type", "table"),
            "sql_query": state.get("sql_query", ""),
            "intent": state.get("intent", "sql")
        }
        
        # Embed question
        question_vector = vector_store.embed(question)
        cache.save(question, question_vector, result_payload)
    except Exception as e:
        logger.warning(f"Failed to save result to cache: {e}")
        
    return {}
