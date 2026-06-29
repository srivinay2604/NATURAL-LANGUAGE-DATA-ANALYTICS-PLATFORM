import streamlit as st
import pandas as pd

def inject_custom_css():
    """
    Injects custom Google fonts and sleek cyberpunk black/red CSS rules to enhance layout,
    neon gradients, transitions, pulsing glows, and dynamic hover animations.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Global Background & Typography */
        html, body, [class*="css"], .stApp {
            font-family: 'Outfit', sans-serif;
            background-color: #0b0c10 !important;
            color: #f1f1f1 !important;
        }
        
        /* Animated pulsing glow for key highlights */
        @keyframes redPulse {
            0% { box-shadow: 0 0 10px rgba(255, 42, 75, 0.3), inset 0 0 5px rgba(255, 42, 75, 0.2); }
            50% { box-shadow: 0 0 25px rgba(255, 42, 75, 0.6), inset 0 0 10px rgba(255, 42, 75, 0.4); }
            100% { box-shadow: 0 0 10px rgba(255, 42, 75, 0.3), inset 0 0 5px rgba(255, 42, 75, 0.2); }
        }
        
        /* Sidebar container styling */
        section[data-testid="stSidebar"] {
            background-color: #121318 !important;
            border-right: 1px solid #2d1217 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }
        
        /* Headers with Crimson Neon Gradients */
        h1, h2, h3 {
            background: linear-gradient(90deg, #ffffff 0%, #ff2a4b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
        }
        
        /* Custom card styling with glassmorphism & red borders */
        .analytics-card {
            background: rgba(18, 19, 24, 0.85);
            border: 1px solid rgba(255, 42, 75, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            animation: redPulse 4s infinite;
            transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), border-color 0.3s ease;
        }
        .analytics-card:hover {
            transform: translateY(-4px);
            border-color: #ff2a4b;
        }
        
        /* Interactive Buttons & Question Chips */
        div.stButton > button {
            background: linear-gradient(135deg, #1f1317 0%, #150f11 100%) !important;
            color: #ff2a4b !important;
            border: 1px solid #ff2a4b !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #ff2a4b 0%, #a8001a 100%) !important;
            color: #ffffff !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 8px 20px rgba(255, 42, 75, 0.5) !important;
        }
        
        /* Premium metric values styling */
        .metric-label {
            font-size: 14px;
            color: #a0aec0;
            font-weight: 500;
            margin-bottom: 4px;
        }
        .metric-val {
            font-size: 34px;
            color: #ff2a4b;
            font-weight: 700;
            text-shadow: 0 0 12px rgba(255, 42, 75, 0.4);
        }
        
        /* Text inputs styling */
        .stTextInput input, .stTextArea textarea {
            background-color: #161822 !important;
            border: 1px solid #3d1b24 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #ff2a4b !important;
            box-shadow: 0 0 12px rgba(255, 42, 75, 0.5) !important;
        }
        
        /* Styled alerts/badges */
        .badge-cached {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid #059669;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 12px;
        }
        .badge-rag {
            background-color: rgba(255, 42, 75, 0.15);
            color: #ff6b81;
            border: 1px solid #ff2a4b;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 12px;
        }
        .badge-sql {
            background-color: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border: 1px solid #ef4444;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_sidebar_status(groq_ok: bool, redis_ok: bool, chroma_ok: bool, langfuse_ok: bool):
    """
    Renders visual connection indicators for core system services.
    """
    st.sidebar.markdown("### 🔌 System Status")
    
    def get_badge(is_ok):
        return "🟢 Connected" if is_ok else "🔴 Offline"
        
    st.sidebar.markdown(f"**Groq Llama 3.1**: {get_badge(groq_ok)}")
    st.sidebar.markdown(f"**Redis Cache**: {get_badge(redis_ok)}")
    st.sidebar.markdown(f"**FAISS Vector Store**: {get_badge(chroma_ok)}")
    st.sidebar.markdown(f"**Langfuse Observability**: {get_badge(langfuse_ok)}")
    st.sidebar.markdown("---")

def render_schema_info(schema_dict: dict, row_count: int):
    """
    Renders the active CSV table structure in an expandable sidebar component.
    """
    if not schema_dict:
        st.sidebar.warning("No active schema loaded.")
        return
        
    st.sidebar.markdown("### 📊 Active Data Table: `df`")
    st.sidebar.markdown(f"**Row Count**: `{row_count}` rows")
    
    with st.sidebar.expander("Show Column Schema", expanded=False):
        schema_df = pd.DataFrame([
            {"Column Name": col, "Data Type": dtype}
            for col, dtype in schema_dict.items()
        ])
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

def render_question_chips(questions: list) -> str or None:
    """
    Renders clickable buttons acting as query templates/chips.
    """
    st.markdown("💡 **Try asking:**")
    cols = st.columns(len(questions))
    selected = None
    for idx, q in enumerate(questions):
        if cols[idx].button(q, key=f"chip_{idx}", use_container_width=True):
            selected = q
    return selected

def render_progress_step(name: str, status: str):
    """
    Renders a single line representing the execution steps in the pipeline.
    """
    if status == "running":
        st.markdown(f"⏳ **{name}**...")
    elif status == "completed":
        st.markdown(f"✅ **{name}**")
    elif status == "failed":
        st.markdown(f"❌ **{name}** (Failed)")
    elif status == "skipped":
        st.markdown(f"◽ **{name}** (Skipped)")
