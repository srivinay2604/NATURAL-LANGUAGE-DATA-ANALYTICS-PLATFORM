import os
import logging
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Set page config at the very beginning
st.set_page_config(
    page_title="NL Analytics — Ask Your Data",
    layout="wide",
    page_icon="🦆"
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from services import database, vector_store, cache, observability, llm
from graph.workflow import get_workflow
from ui import components, charts
from utils.schema_extractor import extract_schema

# ----------------- SESSION STATE SETUP -----------------

if "history" not in st.session_state:
    st.session_state.history = []

if "query_input" not in st.session_state:
    st.session_state.query_input = ""

if "trigger_run" not in st.session_state:
    st.session_state.trigger_run = False

if "csv_path" not in st.session_state:
    st.session_state.csv_path = os.getenv("DEFAULT_CSV_PATH", "data/sample_sales.csv")

# ----------------- STARTUP SEQUENCE -----------------

@st.cache_resource
def startup_sequence():
    """
    Executes the initial platform setup (indexing, cache, models).
    """
    logger.info("Executing startup sequence...")
    
    # 1. Initialize Langfuse
    langfuse_ok = observability.langfuse_client is not None
    
    # 2. Check Redis connection
    redis_ok = cache.get_redis_client() is not None
    
    # 3. Load embedding model and index documents
    chroma_ok = True
    try:
        vector_store.get_embedding_model()
        vector_store.load_documents("documents")
    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        chroma_ok = False
        
    # 4. Check Groq client
    groq_ok = llm.client is not None
    
    # 5. Compile LangGraph workflow
    workflow_app = None
    try:
        workflow_app = get_workflow()
    except Exception as e:
        logger.error(f"Failed to compile LangGraph workflow: {e}")
        
    return {
        "groq_ok": groq_ok,
        "redis_ok": redis_ok,
        "chroma_ok": chroma_ok,
        "langfuse_ok": langfuse_ok,
        "workflow": workflow_app
    }

# Run startup
status = startup_sequence()

# Ensure the database always has the active CSV registered
try:
    database.load_csv(st.session_state.csv_path)
    db_ok = True
except Exception as e:
    logger.error(f"Failed to load active CSV into DuckDB: {e}")
    db_ok = False

# ----------------- STYLING & CUSTOM CSS -----------------

components.inject_custom_css()

# ----------------- SIDEBAR -----------------

st.sidebar.markdown("# 🦆 NL Analytics")
st.sidebar.markdown("*Ask your data anything in plain English.*")
st.sidebar.markdown("---")

# CSV Uploader
st.sidebar.markdown("### 📤 Upload Custom CSV")
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file to analyze", 
    type=["csv"],
    help="Upload a custom dataset to query at runtime."
)

if uploaded_file is not None:
    file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_key") != file_key:
        try:
            # Create folder if it doesn't exist
            upload_dir = "data/uploaded"
            os.makedirs(upload_dir, exist_ok=True)
            
            saved_path = os.path.join(upload_dir, uploaded_file.name)
            with open(saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Register new CSV
            database.load_csv(saved_path)
            st.session_state.csv_path = saved_path
            st.session_state.last_uploaded_key = file_key
            st.sidebar.success(f"Loaded: {uploaded_file.name}")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error loading CSV: {e}")

# Load default sample sales data
if st.sidebar.button("📦 Load Sample Sales Data", use_container_width=True):
    st.session_state.csv_path = "data/sample_sales.csv"
    database.load_csv("data/sample_sales.csv")
    st.session_state.last_uploaded_key = None
    st.sidebar.success("Loaded default sample sales data!")
    st.rerun()

# Clear cache
if st.sidebar.button("🧹 Clear Semantic Cache", use_container_width=True):
    cache.clear_all()
    st.sidebar.success("Cache cleared!")

# Active schema visualization
schema_dict = database.get_schema(st.session_state.csv_path)
row_count = 0
if db_ok:
    try:
        row_count = database.get_connection().execute("SELECT COUNT(*) FROM df").fetchone()[0]
    except Exception:
        pass

components.render_schema_info(schema_dict, row_count)

# Status Indicators
components.render_sidebar_status(
    groq_ok=status["groq_ok"],
    redis_ok=status["redis_ok"],
    chroma_ok=status["chroma_ok"],
    langfuse_ok=status["langfuse_ok"]
)

# ----------------- MAIN AREA -----------------

st.markdown("# 🦆 Ask anything about your data")
st.markdown("##### Powered by Llama 3.1 · DuckDB · LangGraph · ChromaDB")

# Interactive Example Chips
example_questions = [
    "Top 5 products by revenue",
    "Monthly sales trend 2024",
    "Which region has highest profit?",
    "Compare category performance",
    "What is our revenue policy?"
]

selected_chip = components.render_question_chips(example_questions)
if selected_chip:
    st.session_state.query_input = selected_chip
    st.session_state.trigger_run = True
    st.rerun()

# Query Input Form
with st.form("query_form", clear_on_submit=False):
    user_query = st.text_input(
        "Type your question here...",
        value=st.session_state.query_input,
        help="Type a natural language question (e.g., 'What was our total profit in West region?')"
    )
    submit_button = st.form_submit_button("Search & Analyze")

if submit_button:
    st.session_state.query_input = user_query
    st.session_state.trigger_run = True

# ----------------- CORE EXECUTION FLOW -----------------

if st.session_state.trigger_run and st.session_state.query_input:
    # Reset trigger flag immediately to avoid infinite reruns
    st.session_state.trigger_run = False
    question = st.session_state.query_input
    
    st.markdown("---")
    
    # 1. Initialize trace
    trace = observability.start_trace(question)
    trace_id = trace.id if trace else "no-trace"
    
    # 2. Extract schema text for the model
    schema_text = extract_schema(st.session_state.csv_path)
    
    initial_state = {
        "question": question,
        "intent": "",
        "schema": schema_text,
        "sql_query": "",
        "sql_result": None,
        "sql_error": "",
        "retry_count": 0,
        "rag_context": "",
        "rag_answer": "",
        "chart_type": "table",
        "final_answer": "",
        "cached": False,
        "trace_id": trace_id
    }
    
    # Render progress indicators
    progress_placeholder = st.empty()
    
    steps = {
        "cache": "idle",
        "intent": "idle",
        "sql_gen": "idle",
        "sql_exec": "idle",
        "rag_ret": "idle",
        "rag_ans": "idle",
    }
    
    def render_all_steps():
        with progress_placeholder.container():
            st.markdown("#### ⚙️ Pipeline Execution Steps")
            components.render_progress_step("Checking cache...", steps["cache"])
            components.render_progress_step("Classifying intent...", steps["intent"])
            components.render_progress_step("Generating SQL query...", steps["sql_gen"])
            components.render_progress_step("Running query on DuckDB...", steps["sql_exec"])
            components.render_progress_step("Retrieving documents from vector store...", steps["rag_ret"])
            components.render_progress_step("Synthesizing RAG answer...", steps["rag_ans"])
            st.markdown("---")

    steps["cache"] = "running"
    render_all_steps()
    
    # Execute workflow and stream updates
    final_state = initial_state
    workflow_app = status["workflow"]
    
    if workflow_app is None:
        st.error("Workflow compiler error: Platform failed to assemble the LangGraph workflow.")
    else:
        try:
            for event in workflow_app.stream(initial_state):
                for node_name, state_update in event.items():
                    if node_name == "cache_check":
                        if state_update.get("cached"):
                            steps["cache"] = "completed"
                            steps["intent"] = "skipped"
                            steps["sql_gen"] = "skipped"
                            steps["sql_exec"] = "skipped"
                            steps["rag_ret"] = "skipped"
                            steps["rag_ans"] = "skipped"
                        else:
                            steps["cache"] = "completed"
                            steps["intent"] = "running"
                        
                    elif node_name == "intent_classifier":
                        steps["intent"] = "completed"
                        intent = state_update.get("intent", "sql")
                        if intent == "rag":
                            steps["rag_ret"] = "running"
                            steps["sql_gen"] = "skipped"
                            steps["sql_exec"] = "skipped"
                        else:
                            steps["sql_gen"] = "running"
                            steps["rag_ret"] = "skipped"
                            steps["rag_ans"] = "skipped"
                            
                    elif node_name == "sql_generator":
                        if state_update.get("sql_error"):
                            steps["sql_gen"] = "failed"
                        else:
                            steps["sql_gen"] = "completed"
                            steps["sql_exec"] = "running"
                            
                    elif node_name == "sql_executor":
                        if state_update.get("sql_error"):
                            # This means it will loop to fix
                            steps["sql_exec"] = "running"
                        else:
                            steps["sql_exec"] = "completed"
                            
                    elif node_name == "sql_fix":
                        # Repairing SQL
                        steps["sql_gen"] = "completed"
                        steps["sql_exec"] = "running"
                        
                    elif node_name == "rag_retriever":
                        steps["rag_ret"] = "completed"
                        steps["rag_ans"] = "running"
                        
                    elif node_name == "rag_answer":
                        steps["rag_ans"] = "completed"
                        
                    if isinstance(state_update, dict):
                        final_state = {**final_state, **state_update}
                    render_all_steps()
                    
            # Clear steps display after completion to keep screen clean, or display completion summary
            progress_placeholder.empty()
            
            # ----------------- DISPLAY RESULTS -----------------
            
            cached = final_state.get("cached", False)
            intent = final_state.get("intent", "sql")
            
            if cached:
                st.markdown('<div class="badge-cached">⚡ Answered from cache</div>', unsafe_allow_html=True)
            elif intent == "rag":
                st.markdown('<div class="badge-rag">📄 Answered from documents</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="badge-sql">📊 Answered via SQL query</div>', unsafe_allow_html=True)
                
            # Render main result
            if intent == "rag":
                st.markdown(f"### Answer")
                st.write(final_state.get("final_answer"))
            else:
                # SQL result
                sql_err = final_state.get("sql_error")
                df_res = final_state.get("sql_result")
                
                if sql_err and final_state.get("retry_count", 0) >= 3:
                    st.error(f"❌ SQL Execution failed after 3 retries:\n`{sql_err}`")
                    st.warning("💡 Tip: Try rephrasing your question to be more specific (e.g. referencing column names clearly).")
                elif df_res is not None:
                    # View SQL query in expander
                    with st.expander("🔍 View Executed SQL Query", expanded=False):
                        st.code(final_state.get("sql_query"), language="sql")
                        
                    # Auto chart
                    fig = charts.auto_chart(df_res, question)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ No specific visualization matched. Showing raw tabular results.")
                        
                    # Show DataFrame
                    st.markdown("#### Raw Result Data")
                    st.dataframe(df_res, use_container_width=True)
                    
                    # Download CSV
                    csv_data = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv_data,
                        file_name="query_results.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No results returned.")
            
            # Save to chat history if valid final answer exists
            ans = final_state.get("final_answer", "")
            if ans:
                # Add to history and truncate to 5
                history_item = {"question": question, "answer": ans}
                if history_item not in st.session_state.history:
                    st.session_state.history.insert(0, history_item)
                    st.session_state.history = st.session_state.history[:5]
            
            # End Trace
            if trace:
                observability.end_trace(trace, ans, cached)
                if final_state.get("sql_error") and final_state.get("retry_count", 0) >= 3:
                    observability.log_error(trace, final_state["sql_error"])
                    
        except Exception as flow_err:
            st.error(f"An unexpected error occurred during execution: {flow_err}")
            logger.error(f"Workflow execution crash: {flow_err}")
            if trace:
                observability.log_error(trace, str(flow_err))

# ----------------- CHAT HISTORY -----------------

if st.session_state.history:
    st.markdown("---")
    st.markdown("### 🕒 Recent Analytics History")
    for idx, item in enumerate(st.session_state.history):
        # Clickable header
        if st.button(f"🔄 {item['question']}", key=f"hist_btn_{idx}", use_container_width=True):
            st.session_state.query_input = item['question']
            st.session_state.trigger_run = True
            st.rerun()
        st.markdown(f"*{item['answer']}*")
        st.markdown("---")
