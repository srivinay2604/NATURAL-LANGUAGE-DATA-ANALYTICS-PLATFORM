import os
import logging
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── Page config must be first Streamlit call ──────────────────────────────────
st.set_page_config(
    page_title="NL Analytics — Ask Your Data",
    layout="wide",
    page_icon="🦆",
    initial_sidebar_state="expanded",
)

# ── Environment & logging ─────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Internal imports ──────────────────────────────────────────────────────────
from services import database, vector_store, cache, observability, llm
from graph.workflow import get_workflow
from ui import components, charts
from utils.schema_extractor import extract_schema

# ── Inject CSS immediately (before anything renders) ─────────────────────────
components.inject_custom_css()

# ── Splash screen — shown once per browser session ───────────────────────────
if "app_loaded" not in st.session_state:
    components.render_splash_screen()
    st.session_state["app_loaded"] = True

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []

if "query_input" not in st.session_state:
    st.session_state.query_input = ""

if "trigger_run" not in st.session_state:
    st.session_state.trigger_run = False

if "csv_path" not in st.session_state:
    st.session_state.csv_path = os.getenv("DEFAULT_CSV_PATH", "data/sample_sales.csv")

# ─────────────────────────────────────────────────────────────────────────────
#  STARTUP SEQUENCE  (cached — runs once per server process)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def startup_sequence():
    """Executes the initial platform setup: indexing, cache, models, workflow."""
    logger.info("Executing startup sequence...")

    langfuse_ok = observability.langfuse_client is not None
    redis_ok    = cache.get_redis_client() is not None

    chroma_ok = True
    try:
        vector_store.get_embedding_model()
        vector_store.load_documents("documents")
    except Exception as e:
        logger.error(f"Vector DB init error: {e}")
        chroma_ok = False

    groq_ok = llm.client is not None

    workflow_app = None
    try:
        workflow_app = get_workflow()
    except Exception as e:
        logger.error(f"LangGraph compile error: {e}")

    return {
        "groq_ok":     groq_ok,
        "redis_ok":    redis_ok,
        "chroma_ok":   chroma_ok,
        "langfuse_ok": langfuse_ok,
        "workflow":    workflow_app,
    }


status = startup_sequence()

# Load active CSV into DuckDB
try:
    database.load_csv(st.session_state.csv_path)
    db_ok = True
except Exception as e:
    logger.error(f"Failed to load active CSV: {e}")
    db_ok = False

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

# Header
components.render_sidebar_header()
st.sidebar.markdown("---")

# CSV Upload
st.sidebar.markdown(
    '<div style="font-size:12px; font-weight:600; letter-spacing:2px; '
    'color:#555; text-transform:uppercase; margin-bottom:8px;">📤 Upload CSV</div>',
    unsafe_allow_html=True,
)
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file to analyze",
    type=["csv"],
    label_visibility="collapsed",
)

if uploaded_file is not None:
    file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_key") != file_key:
        try:
            upload_dir = "data/uploaded"
            os.makedirs(upload_dir, exist_ok=True)
            saved_path = os.path.join(upload_dir, uploaded_file.name)
            with open(saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            database.load_csv(saved_path)
            st.session_state.csv_path = saved_path
            st.session_state.last_uploaded_key = file_key
            st.sidebar.success(f"✅ Loaded: {uploaded_file.name}")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error loading CSV: {e}")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("📦 Sample Data", use_container_width=True, key="load_sample"):
        st.session_state.csv_path = "data/sample_sales.csv"
        database.load_csv("data/sample_sales.csv")
        st.session_state.last_uploaded_key = None
        st.sidebar.success("Loaded sample data!")
        st.rerun()
with col2:
    if st.button("🧹 Clear Cache", use_container_width=True, key="clear_cache"):
        cache.clear_all()
        st.sidebar.success("Cache cleared!")

st.sidebar.markdown("---")

# Schema info
schema_dict = database.get_schema(st.session_state.csv_path)
row_count = 0
if db_ok:
    try:
        row_count = database.get_connection().execute(
            "SELECT COUNT(*) FROM df"
        ).fetchone()[0]
    except Exception:
        pass

components.render_schema_info(schema_dict, row_count)
st.sidebar.markdown("---")

# System status
components.render_sidebar_status(
    groq_ok=status["groq_ok"],
    redis_ok=status["redis_ok"],
    chroma_ok=status["chroma_ok"],
    langfuse_ok=status["langfuse_ok"],
)

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────

# Hero header
components.render_hero()

# Divider
st.markdown('<hr style="margin: 0 0 24px;">', unsafe_allow_html=True)

# Example question chips
example_questions = [
    "Top 5 products by revenue",
    "Monthly sales trend 2024",
    "Which region has highest profit?",
    "Compare category performance",
    "What is our revenue policy?",
]

selected_chip = components.render_question_chips(example_questions)
if selected_chip:
    st.session_state.query_input = selected_chip
    st.session_state.trigger_run = True
    st.rerun()

# Query input form
st.markdown("<br>", unsafe_allow_html=True)
with st.form("query_form", clear_on_submit=False):
    user_query = st.text_input(
        "Your question",
        value=st.session_state.query_input,
        placeholder="e.g. What was total revenue in the West region last quarter?",
        label_visibility="collapsed",
    )
    submit_button = st.form_submit_button(
        "🔍  Search & Analyze",
        use_container_width=False,
    )

if submit_button:
    st.session_state.query_input = user_query
    st.session_state.trigger_run = True

# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.trigger_run and st.session_state.query_input:
    st.session_state.trigger_run = False
    question = st.session_state.query_input

    st.markdown('<hr style="margin: 24px 0;">', unsafe_allow_html=True)

    # Start observability trace
    trace    = observability.start_trace(question)
    trace_id = trace.id if trace else "no-trace"

    # Build schema text for LLM
    schema_text = extract_schema(st.session_state.csv_path)

    initial_state = {
        "question":     question,
        "intent":       "",
        "schema":       schema_text,
        "sql_query":    "",
        "sql_result":   None,
        "sql_error":    "",
        "retry_count":  0,
        "rag_context":  "",
        "rag_answer":   "",
        "chart_type":   "table",
        "final_answer": "",
        "cached":       False,
        "trace_id":     trace_id,
    }

    # Progress display
    progress_placeholder = st.empty()

    steps = {
        "cache":   "idle",
        "intent":  "idle",
        "sql_gen": "idle",
        "sql_exec":"idle",
        "rag_ret": "idle",
        "rag_ans": "idle",
    }

    STEP_LABELS = {
        "cache":   "Checking semantic cache",
        "intent":  "Classifying intent",
        "sql_gen": "Generating SQL query",
        "sql_exec":"Executing on DuckDB",
        "rag_ret": "Retrieving document context",
        "rag_ans": "Synthesizing RAG answer",
    }

    def render_all_steps():
        with progress_placeholder.container():
            components.render_pipeline_header()
            for key in ["cache", "intent", "sql_gen", "sql_exec", "rag_ret", "rag_ans"]:
                components.render_progress_step(STEP_LABELS[key], steps[key])

    steps["cache"] = "running"
    render_all_steps()

    # Run workflow
    final_state  = initial_state
    workflow_app = status["workflow"]

    if workflow_app is None:
        st.error("⚠️ Workflow compiler error: LangGraph workflow failed to assemble.")
    else:
        try:
            for event in workflow_app.stream(initial_state):
                for node_name, state_update in event.items():

                    if node_name == "cache_check":
                        if state_update.get("cached"):
                            for k in ["intent","sql_gen","sql_exec","rag_ret","rag_ans"]:
                                steps[k] = "skipped"
                            steps["cache"] = "completed"
                        else:
                            steps["cache"]  = "completed"
                            steps["intent"] = "running"

                    elif node_name == "intent_classifier":
                        steps["intent"] = "completed"
                        intent = state_update.get("intent", "sql")
                        if intent == "rag":
                            steps["sql_gen"]  = "skipped"
                            steps["sql_exec"] = "skipped"
                            steps["rag_ret"]  = "running"
                        else:
                            steps["sql_gen"]  = "running"
                            steps["rag_ret"]  = "skipped"
                            steps["rag_ans"]  = "skipped"

                    elif node_name == "sql_generator":
                        steps["sql_gen"]  = "failed" if state_update.get("sql_error") else "completed"
                        if not state_update.get("sql_error"):
                            steps["sql_exec"] = "running"

                    elif node_name == "sql_executor":
                        steps["sql_exec"] = "running" if state_update.get("sql_error") else "completed"

                    elif node_name == "sql_fix":
                        steps["sql_gen"]  = "completed"
                        steps["sql_exec"] = "running"

                    elif node_name == "rag_retriever":
                        steps["rag_ret"] = "completed"
                        steps["rag_ans"] = "running"

                    elif node_name == "rag_answer":
                        steps["rag_ans"] = "completed"

                    if isinstance(state_update, dict):
                        final_state = {**final_state, **state_update}
                    render_all_steps()

            # Clear pipeline steps
            progress_placeholder.empty()

            # ── Results ──────────────────────────────────────────────────────
            cached = final_state.get("cached", False)
            intent = final_state.get("intent", "sql")

            components.render_result_section_header(intent, cached)

            if intent == "rag":
                st.markdown(
                    '<div style="background:rgba(255,42,75,0.06); border:1px solid rgba(255,42,75,0.2);'
                    'border-radius:12px; padding:20px 24px; color:#e2e8f0; font-size:15px; line-height:1.7;">',
                    unsafe_allow_html=True,
                )
                st.write(final_state.get("final_answer"))
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                sql_err = final_state.get("sql_error")
                df_res  = final_state.get("sql_result")

                if sql_err and final_state.get("retry_count", 0) >= 3:
                    st.error(f"❌ SQL failed after 3 retries: `{sql_err}`")
                    st.warning("💡 Try rephrasing — be specific about column names.")

                elif df_res is not None:
                    with st.expander("🔍 View Generated SQL", expanded=False):
                        st.code(final_state.get("sql_query", ""), language="sql")

                    fig = charts.auto_chart(df_res, question)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ Showing raw table (no chart matched this data shape).")

                    st.markdown(
                        '<div style="font-size:12px; font-weight:600; letter-spacing:2px;'
                        'color:#555; text-transform:uppercase; margin:16px 0 8px;">Result Data</div>',
                        unsafe_allow_html=True,
                    )
                    st.dataframe(df_res, use_container_width=True)

                    csv_data = df_res.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name="query_results.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("No results returned for this query.")

            # Save to history
            ans = final_state.get("final_answer", "")
            if ans:
                item = {"question": question, "answer": ans}
                if item not in st.session_state.history:
                    st.session_state.history.insert(0, item)
                    st.session_state.history = st.session_state.history[:5]

            # End observability trace
            if trace:
                observability.end_trace(trace, ans, cached)
                if final_state.get("sql_error") and final_state.get("retry_count", 0) >= 3:
                    observability.log_error(trace, final_state["sql_error"])

        except Exception as flow_err:
            st.error(f"Unexpected error: {flow_err}")
            logger.error(f"Workflow crash: {flow_err}")
            if trace:
                observability.log_error(trace, str(flow_err))

# ─────────────────────────────────────────────────────────────────────────────
#  RECENT HISTORY
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.history:
    st.markdown('<hr style="margin: 32px 0 24px;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:12px; font-weight:600; letter-spacing:3px; '
        'color:#555; text-transform:uppercase; margin-bottom:16px;">🕒 &nbsp;Recent Queries</div>',
        unsafe_allow_html=True,
    )
    for idx, item in enumerate(st.session_state.history):
        col_a, col_b = st.columns([5, 1])
        with col_a:
            st.markdown(
                f'<div style="font-size:14px; font-weight:600; color:#ff6b81; '
                f'margin-bottom:4px;">Q: {item["question"]}</div>'
                f'<div style="font-size:13px; color:#718096; '
                f'margin-bottom:12px;">{item["answer"][:180]}{"…" if len(item["answer"]) > 180 else ""}</div>',
                unsafe_allow_html=True,
            )
        with col_b:
            if st.button("↩ Re-run", key=f"hist_btn_{idx}"):
                st.session_state.query_input = item["question"]
                st.session_state.trigger_run = True
                st.rerun()
