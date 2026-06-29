import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

langfuse_client = None
active_traces = {}

try:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
    
    if public_key and secret_key and "your_langfuse" not in public_key:
        from langfuse import Langfuse
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        logger.info("Langfuse initialized successfully.")
    else:
        logger.warning("Langfuse API keys missing or using placeholder values. Tracing is disabled.")
except Exception as e:
    logger.warning(f"Could not initialize Langfuse: {e}. Tracing is disabled.")

def start_trace(question: str):
    """
    Starts a Langfuse trace for the given user question.
    """
    if not langfuse_client:
        return None
    try:
        trace = langfuse_client.start_observation(
            as_type="trace",
            name="nl-analytics-query",
            input={"question": question}
        )
        if trace and hasattr(trace, "id"):
            active_traces[trace.id] = trace
        return trace
    except Exception as e:
        logger.warning(f"Error starting Langfuse trace: {e}")
        return None


def log_span(trace, name, input_data, output_data, latency=None):
    """
    Logs a span within the given trace.
    """
    if not langfuse_client or not trace:
        return
    try:
        span = trace.start_observation(
            as_type="span",
            name=name,
            input=input_data,
            output=output_data
        )
        # End the span immediately since we already have input and output
        # If latency is provided, we can log it in metadata
        if latency:
            span.update(metadata={"latency_seconds": latency})
        span.end()
    except Exception as e:
        logger.warning(f"Error logging Langfuse span '{name}': {e}")

def log_error(trace, error_message):
    """
    Logs an error to the trace.
    """
    if not langfuse_client or not trace:
        return
    try:
        trace.update(
            output={"error": error_message},
            tags=["error"]
        )
    except Exception as e:
        logger.warning(f"Error logging Langfuse trace error: {e}")

def end_trace(trace, final_answer, cached):
    """
    Ends the Langfuse trace with the final result.
    """
    if not langfuse_client or not trace:
        return
    try:
        trace.update(
            output={"final_answer": final_answer},
            metadata={"cached": cached}
        )
        trace.end()
    except Exception as e:
        logger.warning(f"Error ending Langfuse trace: {e}")

