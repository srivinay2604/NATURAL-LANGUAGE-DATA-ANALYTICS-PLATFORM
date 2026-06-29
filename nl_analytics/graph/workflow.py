import logging
from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from graph.nodes import (
    cache_check_node,
    intent_classifier_node,
    sql_generator_node,
    sql_executor_node,
    sql_fix_node,
    rag_retriever_node,
    rag_answer_node,
    cache_save_node
)

logger = logging.getLogger(__name__)

# Routing Functions
def route_cache_check(state: AgentState) -> str:
    """
    Routes from cache check to END if cached, otherwise to intent classifier.
    """
    if state.get("cached", False):
        logger.info("Routing to END (Cached).")
        return "end"
    logger.info("Routing to intent_classifier (Cache Miss).")
    return "intent_classifier"

def route_intent(state: AgentState) -> str:
    """
    Routes to RAG or SQL based on classified intent.
    """
    intent = state.get("intent", "sql")
    if intent == "rag":
        logger.info("Routing to RAG retriever.")
        return "rag_retriever"
    logger.info("Routing to SQL generator.")
    return "sql_generator"

def route_sql_execute(state: AgentState) -> str:
    """
    Routes to cache_save if successful, to sql_fix if failed and under retry limit,
    otherwise to END.
    """
    error = state.get("sql_error", "")
    retry_count = state.get("retry_count", 0)
    
    if not error:
        logger.info("SQL successful. Routing to cache_save.")
        return "cache_save"
        
    if retry_count < 3:
        logger.info(f"SQL failed with error: {error}. Routing to sql_fix (Retry {retry_count + 1}).")
        return "sql_fix"
        
    logger.info("SQL failed and retry limit reached. Routing to END.")
    return "end"

# Build Graph
def get_workflow():
    """
    Builds and compiles the LangGraph analytics workflow.
    """
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("cache_check", cache_check_node)
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("sql_generator", sql_generator_node)
    workflow.add_node("sql_executor", sql_executor_node)
    workflow.add_node("sql_fix", sql_fix_node)
    workflow.add_node("rag_retriever", rag_retriever_node)
    workflow.add_node("rag_answer", rag_answer_node)
    workflow.add_node("cache_save", cache_save_node)
    
    # Define Edges
    workflow.add_edge(START, "cache_check")
    
    # Conditional edge from cache check
    workflow.add_conditional_edges(
        "cache_check",
        route_cache_check,
        {
            "end": END,
            "intent_classifier": "intent_classifier"
        }
    )
    
    # Conditional edge from intent classification
    workflow.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "sql_generator": "sql_generator",
            "rag_retriever": "rag_retriever"
        }
    )
    
    # SQL generation -> execution
    workflow.add_edge("sql_generator", "sql_executor")
    
    # Conditional edge from SQL execution (retries or save)
    workflow.add_conditional_edges(
        "sql_executor",
        route_sql_execute,
        {
            "cache_save": "cache_save",
            "sql_fix": "sql_fix",
            "end": END
        }
    )
    
    # SQL fix loops back to execution
    workflow.add_edge("sql_fix", "sql_executor")
    
    # RAG route: retriever -> answer -> cache save
    workflow.add_edge("rag_retriever", "rag_answer")
    workflow.add_edge("rag_answer", "cache_save")
    
    # Cache save leads to the end
    workflow.add_edge("cache_save", END)
    
    # Compile
    compiled_graph = workflow.compile()
    logger.info("Successfully compiled LangGraph workflow.")
    return compiled_graph
