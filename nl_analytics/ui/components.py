import streamlit as st
import pandas as pd


# ─────────────────────────────────────────────
#  SPLASH / LANDING SCREEN
# ─────────────────────────────────────────────

def render_splash_screen():
    """
    Renders a full-screen cinematic loading splash with the project name,
    animated spinner, and auto-dismiss after ~3 seconds.
    Only called once per browser session via st.session_state.
    """
    splash_html = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800;900&display=swap');

      /* ── Splash container ── */
      #nl-splash {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: #0b0c10;
        z-index: 2147483647;          /* max z-index */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0;
        font-family: 'Outfit', sans-serif;
        animation: splashFadeOut 0.7s cubic-bezier(0.4, 0, 0.2, 1) 3.0s forwards;
        overflow: hidden;
      }

      /* Subtle animated grid background */
      #nl-splash::before {
        content: '';
        position: absolute;
        inset: 0;
        background-image:
          linear-gradient(rgba(255,42,75,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,42,75,0.04) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: gridPan 8s linear infinite;
      }

      @keyframes gridPan {
        from { background-position: 0 0; }
        to   { background-position: 50px 50px; }
      }

      /* Radial glow behind the title */
      #nl-splash::after {
        content: '';
        position: absolute;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(255,42,75,0.12) 0%, transparent 70%);
        border-radius: 50%;
        animation: glowPulse 2.5s ease-in-out infinite;
      }

      @keyframes glowPulse {
        0%, 100% { transform: scale(1); opacity: 0.6; }
        50%       { transform: scale(1.15); opacity: 1; }
      }

      /* ── Logo / Icon ── */
      .splash-icon {
        font-size: 72px;
        line-height: 1;
        margin-bottom: 24px;
        position: relative;
        z-index: 1;
        animation: floatIcon 3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(255,42,75,0.6));
      }

      @keyframes floatIcon {
        0%, 100% { transform: translateY(0px) rotate(-3deg); }
        50%       { transform: translateY(-12px) rotate(3deg); }
      }

      /* ── Project Name ── */
      .splash-title {
        font-size: 68px;
        font-weight: 900;
        letter-spacing: -2px;
        line-height: 1;
        margin-bottom: 12px;
        position: relative;
        z-index: 1;
        background: linear-gradient(
          100deg,
          #ffffff 0%,
          #ff6b81 40%,
          #ff2a4b 60%,
          #cc0022 100%
        );
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmerText 2.5s linear infinite;
      }

      @keyframes shimmerText {
        0%   { background-position: 0% center; }
        100% { background-position: 200% center; }
      }

      /* ── Tagline ── */
      .splash-tagline {
        font-size: 15px;
        font-weight: 400;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #555;
        margin-bottom: 56px;
        position: relative;
        z-index: 1;
        animation: fadeInUp 0.8s ease-out 0.3s both;
      }

      @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
      }

      /* ── Spinner ring ── */
      .splash-spinner-wrap {
        position: relative;
        width: 64px;
        height: 64px;
        margin-bottom: 28px;
        z-index: 1;
        animation: fadeInUp 0.6s ease-out 0.5s both;
      }

      .splash-ring {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        border: 3px solid transparent;
        animation: ringRotate 1.1s linear infinite;
      }

      .splash-ring-outer {
        border-top-color: #ff2a4b;
        border-right-color: rgba(255,42,75,0.3);
        border-bottom-color: transparent;
        border-left-color: transparent;
        filter: drop-shadow(0 0 8px rgba(255,42,75,0.8));
        animation-duration: 1.1s;
      }

      .splash-ring-inner {
        inset: 10px;
        border-top-color: transparent;
        border-right-color: transparent;
        border-bottom-color: rgba(255,42,75,0.6);
        border-left-color: rgba(255,42,75,0.2);
        animation-direction: reverse;
        animation-duration: 0.75s;
      }

      @keyframes ringRotate {
        to { transform: rotate(360deg); }
      }

      /* ── Loading dots text ── */
      .splash-loading-text {
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #ff2a4b;
        position: relative;
        z-index: 1;
        animation: fadeInUp 0.6s ease-out 0.7s both;
      }

      .splash-dots::after {
        content: '';
        animation: dots 1.8s steps(4, end) infinite;
      }

      @keyframes dots {
        0%   { content: ''; }
        25%  { content: '.'; }
        50%  { content: '..'; }
        75%  { content: '...'; }
        100% { content: ''; }
      }

      /* ── Progress bar at bottom ── */
      .splash-progress {
        position: absolute;
        bottom: 0; left: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, #ff2a4b, #ff6b81, transparent);
        animation: progressBar 3.0s ease-in-out forwards;
        box-shadow: 0 0 12px rgba(255,42,75,0.8);
      }

      @keyframes progressBar {
        from { width: 0%; }
        to   { width: 100%; }
      }

      /* ── Corner accents ── */
      .splash-corner {
        position: absolute;
        width: 32px; height: 32px;
        border-color: rgba(255,42,75,0.4);
        border-style: solid;
        z-index: 1;
      }
      .splash-corner-tl { top: 32px; left: 32px; border-width: 2px 0 0 2px; }
      .splash-corner-tr { top: 32px; right: 32px; border-width: 2px 2px 0 0; }
      .splash-corner-bl { bottom: 32px; left: 32px; border-width: 0 0 2px 2px; }
      .splash-corner-br { bottom: 32px; right: 32px; border-width: 0 2px 2px 0; }

      /* ── Fade out animation ── */
      @keyframes splashFadeOut {
        from { opacity: 1; transform: scale(1); }
        to   { opacity: 0; transform: scale(1.03); pointer-events: none; visibility: hidden; }
      }
    </style>

    <div id="nl-splash">
      <!-- Corner accents -->
      <div class="splash-corner splash-corner-tl"></div>
      <div class="splash-corner splash-corner-tr"></div>
      <div class="splash-corner splash-corner-bl"></div>
      <div class="splash-corner splash-corner-br"></div>

      <!-- Animated progress bar -->
      <div class="splash-progress"></div>

      <!-- Content -->
      <div class="splash-icon">🦆</div>
      <div class="splash-title">NL Analytics</div>
      <div class="splash-tagline">Natural Language · Data Analytics Platform</div>

      <!-- Spinner -->
      <div class="splash-spinner-wrap">
        <div class="splash-ring splash-ring-outer"></div>
        <div class="splash-ring splash-ring-inner"></div>
      </div>

      <!-- Loading text -->
      <div class="splash-loading-text">
        Initializing AI Systems<span class="splash-dots"></span>
      </div>
    </div>

    <script>
      // Remove splash from DOM after animation completes
      setTimeout(function() {
        var splash = document.getElementById('nl-splash');
        if (splash) { splash.remove(); }
      }, 3800);
    </script>
    """
    st.markdown(splash_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  GLOBAL CSS INJECTION
# ─────────────────────────────────────────────

def inject_custom_css():
    """
    Injects the full premium cyberpunk dark-red design system.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

        /* ─── Reset & Base ─── */
        html, body, [class*="css"], .stApp {
            font-family: 'Outfit', sans-serif !important;
            background-color: #0b0c10 !important;
            color: #e2e8f0 !important;
        }

        /* ─── Animated background scan line ─── */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(255,42,75,0.01) 2px,
                rgba(255,42,75,0.01) 4px
            );
            pointer-events: none;
            z-index: 0;
        }

        /* ─── Scrollbar ─── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0b0c10; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #ff2a4b, #800016);
            border-radius: 3px;
        }

        /* ─── Sidebar ─── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d0e13 0%, #0b0c10 100%) !important;
            border-right: 1px solid rgba(255,42,75,0.18) !important;
        }
        /* Sidebar text — default only, allows inline overrides */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #cbd5e0;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            background: linear-gradient(90deg, #ffffff 0%, #ff2a4b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
        }

        /* ─── Main content padding ─── */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
            max-width: 1100px !important;
        }

        /* ─── Headings ─── */
        h1 {
            font-size: 2.8rem !important;
            font-weight: 800 !important;
            letter-spacing: -1px !important;
            background: linear-gradient(100deg, #ffffff 0%, #ff6b81 45%, #ff2a4b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.2rem !important;
        }
        h2 {
            font-weight: 700 !important;
            background: linear-gradient(90deg, #f1f1f1 0%, #ff2a4b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        h3 {
            font-weight: 600 !important;
            color: #e2e8f0 !important;
            -webkit-text-fill-color: #e2e8f0 !important;
        }
        h5 {
            color: #718096 !important;
            font-weight: 400 !important;
            font-size: 1rem !important;
            letter-spacing: 1px !important;
        }

        /* ─── Pulsing keyframe for cards ─── */
        @keyframes borderPulse {
            0%   { border-color: rgba(255,42,75,0.25); }
            50%  { border-color: rgba(255,42,75,0.55); }
            100% { border-color: rgba(255,42,75,0.25); }
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* ─── Analytics card ─── */
        .analytics-card {
            background: rgba(14,15,20,0.92);
            border: 1px solid rgba(255,42,75,0.25);
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
            animation: borderPulse 4s ease-in-out infinite, slideUp 0.5s ease-out both;
            transition: transform 0.3s cubic-bezier(0.25,0.8,0.25,1), box-shadow 0.3s ease;
            backdrop-filter: blur(10px);
        }
        .analytics-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(255,42,75,0.25);
        }

        /* ─── Hero section wrapper ─── */
        .hero-section {
            text-align: center;
            padding: 20px 0 32px;
            animation: slideUp 0.5s ease-out both;
        }
        .hero-divider {
            width: 80px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #ff2a4b, transparent);
            margin: 16px auto 0;
            border-radius: 2px;
            box-shadow: 0 0 10px rgba(255,42,75,0.6);
        }

        /* ─── Powered by badge ─── */
        .powered-by {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,42,75,0.06);
            border: 1px solid rgba(255,42,75,0.2);
            border-radius: 999px;
            padding: 6px 18px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 1px;
            color: #888 !important;
            text-transform: uppercase;
            margin-top: 10px;
            margin-bottom: 28px;
        }
        .powered-by span {
            color: #ff6b81 !important;
            font-weight: 600;
        }

        /* ─── Chip buttons (example questions) ─── */
        div[data-testid="column"] div.stButton > button {
            background: rgba(255,42,75,0.06) !important;
            color: #ff6b81 !important;
            border: 1px solid rgba(255,42,75,0.3) !important;
            border-radius: 999px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 8px 14px !important;
            transition: all 0.25s cubic-bezier(0.25,0.8,0.25,1) !important;
            white-space: nowrap;
            overflow: hidden;
        }
        div[data-testid="column"] div.stButton > button:hover {
            background: linear-gradient(135deg, #ff2a4b 0%, #a8001a 100%) !important;
            color: #fff !important;
            border-color: #ff2a4b !important;
            transform: translateY(-2px) scale(1.03) !important;
            box-shadow: 0 6px 20px rgba(255,42,75,0.4) !important;
        }

        /* ─── Sidebar buttons ─── */
        div.stButton > button {
            background: linear-gradient(135deg, #1a0f12 0%, #0f0b0c 100%) !important;
            color: #ff6b81 !important;
            border: 1px solid rgba(255,42,75,0.35) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            transition: all 0.3s cubic-bezier(0.25,0.8,0.25,1) !important;
        }
        div.stButton > button:hover {
            background: linear-gradient(135deg, #ff2a4b 0%, #a8001a 100%) !important;
            color: #ffffff !important;
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 24px rgba(255,42,75,0.5) !important;
        }

        /* ─── Text inputs ─── */
        .stTextInput > div > div > input,
        .stTextInput input {
            background-color: #0f1016 !important;
            border: 1px solid rgba(255,42,75,0.25) !important;
            border-radius: 10px !important;
            color: #f1f1f1 !important;
            font-family: 'Outfit', sans-serif !important;
            font-size: 15px !important;
            padding: 12px 16px !important;
            transition: border-color 0.25s, box-shadow 0.25s !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextInput input:focus {
            border-color: #ff2a4b !important;
            box-shadow: 0 0 0 3px rgba(255,42,75,0.15), 0 0 20px rgba(255,42,75,0.2) !important;
            outline: none !important;
        }

        /* ─── Form submit button ─── */
        div[data-testid="stForm"] div.stButton > button,
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #ff2a4b 0%, #cc001f 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 10px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            padding: 12px 28px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 20px rgba(255,42,75,0.35) !important;
        }
        div[data-testid="stForm"] div.stButton > button:hover,
        .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #ff4d6a 0%, #ff2a4b 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(255,42,75,0.55) !important;
        }

        /* ─── Metric values ─── */
        .metric-label {
            font-size: 13px;
            color: #718096;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .metric-val {
            font-size: 40px;
            color: #ff2a4b;
            font-weight: 800;
            text-shadow: 0 0 20px rgba(255,42,75,0.5);
            line-height: 1;
        }

        /* ─── Badges ─── */
        .badge-cached {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(16,185,129,0.1);
            color: #34d399;
            border: 1px solid rgba(52,211,153,0.3);
            font-size: 12px; font-weight: 600;
            padding: 5px 14px; border-radius: 999px;
            margin-bottom: 16px;
            letter-spacing: 0.5px;
        }
        .badge-rag {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(255,42,75,0.1);
            color: #ff6b81;
            border: 1px solid rgba(255,42,75,0.3);
            font-size: 12px; font-weight: 600;
            padding: 5px 14px; border-radius: 999px;
            margin-bottom: 16px;
            letter-spacing: 0.5px;
        }
        .badge-sql {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(239,68,68,0.1);
            color: #fca5a5;
            border: 1px solid rgba(239,68,68,0.3);
            font-size: 12px; font-weight: 600;
            padding: 5px 14px; border-radius: 999px;
            margin-bottom: 16px;
            letter-spacing: 0.5px;
        }

        /* ─── Expander ─── */
        .streamlit-expanderHeader {
            background: rgba(255,42,75,0.06) !important;
            border: 1px solid rgba(255,42,75,0.2) !important;
            border-radius: 8px !important;
            color: #ff6b81 !important;
            font-weight: 600 !important;
        }
        .streamlit-expanderContent {
            background: rgba(10,11,15,0.8) !important;
            border: 1px solid rgba(255,42,75,0.15) !important;
            border-top: none !important;
        }

        /* ─── DataFrames ─── */
        .stDataFrame { border-radius: 10px !important; overflow: hidden; }
        .stDataFrame th {
            background: rgba(255,42,75,0.12) !important;
            color: #ff6b81 !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            font-size: 11px !important;
            letter-spacing: 1px !important;
        }
        .stDataFrame td { color: #e2e8f0 !important; }

        /* ─── Download button ─── */
        .stDownloadButton > button {
            background: rgba(255,42,75,0.08) !important;
            color: #ff6b81 !important;
            border: 1px solid rgba(255,42,75,0.3) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
        }
        .stDownloadButton > button:hover {
            background: rgba(255,42,75,0.18) !important;
            box-shadow: 0 4px 16px rgba(255,42,75,0.3) !important;
        }

        /* ─── File uploader ─── */
        .stFileUploader {
            background: rgba(255,42,75,0.04) !important;
            border: 1px dashed rgba(255,42,75,0.3) !important;
            border-radius: 10px !important;
        }

        /* ─── Alerts / Info boxes ─── */
        .stAlert {
            background: rgba(255,42,75,0.07) !important;
            border: 1px solid rgba(255,42,75,0.25) !important;
            border-radius: 10px !important;
            color: #fca5a5 !important;
        }

        /* ─── Step progress items ─── */
        .step-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            font-size: 14px;
            border-bottom: 1px solid rgba(255,42,75,0.07);
            animation: slideUp 0.3s ease-out both;
        }
        .step-icon { width: 22px; text-align: center; flex-shrink: 0; }
        .step-label { flex: 1; color: #a0aec0; }
        .step-label.running  { color: #fcd34d; font-weight: 600; }
        .step-label.done     { color: #6ee7b7; font-weight: 600; }
        .step-label.failed   { color: #fc8181; font-weight: 600; }
        .step-label.skipped  { color: #4a5568; }

        /* ─── Horizontal rule ─── */
        hr {
            border: none !important;
            border-top: 1px solid rgba(255,42,75,0.15) !important;
            margin: 24px 0 !important;
        }

        /* ─── Code blocks ─── */
        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
            background: rgba(255,42,75,0.06) !important;
            border-radius: 6px !important;
        }

        /* ─── Sidebar divider ─── */
        section[data-testid="stSidebar"] hr {
            border-top: 1px solid rgba(255,42,75,0.2) !important;
        }

        /* ─── Status dot animation ─── */
        @keyframes statusPing {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.4; }
        }
        .status-dot-live { animation: statusPing 2s ease-in-out infinite; }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
#  SIDEBAR COMPONENTS
# ─────────────────────────────────────────────

def render_sidebar_header():
    """Renders a styled sidebar header with logo and tagline."""
    st.sidebar.markdown(
        """
        <div style="padding: 8px 0 16px;">
          <div style="font-size: 28px; font-weight: 900; letter-spacing: -0.5px;
                      background: linear-gradient(90deg, #ffffff 0%, #ff2a4b 100%);
                      -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🦆 NL Analytics
          </div>
          <div style="font-size: 12px; color: #555; letter-spacing: 2px;
                      text-transform: uppercase; margin-top: 4px;">
            Ask Your Data Anything
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_status(groq_ok: bool, redis_ok: bool, chroma_ok: bool, langfuse_ok: bool):
    """Renders visual connection indicators for core system services."""
    st.sidebar.markdown(
        '<p style="font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:8px;">'
        '🔌 System Status</p>',
        unsafe_allow_html=True,
    )

    services = [
        ("Groq · Llama 3.1",  groq_ok),
        ("Redis Cache",        redis_ok),
        ("ChromaDB",           chroma_ok),
        ("Langfuse Traces",    langfuse_ok),
    ]

    for name, ok in services:
        dot_color    = "#22c55e" if ok else "#ef4444"
        label_color  = "#6ee7b7" if ok else "#fc8181"
        status_text  = "Online"  if ok else "Offline"
        # Render each service as its own markdown call — avoids Streamlit HTML truncation
        st.sidebar.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px;
                        padding:7px 12px; margin-bottom:4px;
                        background:rgba(255,42,75,0.04);
                        border:1px solid rgba(255,42,75,0.12);
                        border-radius:8px;">
              <div style="width:8px; height:8px; border-radius:50%;
                          background:{dot_color};
                          box-shadow:0 0 6px {dot_color};
                          flex-shrink:0;"></div>
              <div style="flex:1; font-size:13px; color:#a0aec0;">{name}</div>
              <div style="font-size:11px; font-weight:700; color:{label_color};
                          text-transform:uppercase; letter-spacing:1px;">{status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_schema_info(schema_dict: dict, row_count: int):
    """Renders the active CSV schema in an expandable sidebar card."""
    if not schema_dict:
        st.sidebar.warning("No active schema loaded.")
        return

    st.sidebar.markdown(
        f"""
        <div style="margin-bottom:8px;">
          <div style="font-size:13px; font-weight:600; color:#718096;
                      text-transform:uppercase; letter-spacing:1px;">Active Table</div>
          <div style="font-size:18px; font-weight:700; color:#ff6b81;
                      font-family:'JetBrains Mono',monospace;">df</div>
          <div style="font-size:12px; color:#555;">
            {row_count:,} rows · {len(schema_dict)} columns
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar.expander("📋 View Column Schema", expanded=False):
        schema_df = pd.DataFrame(
            [{"Column": col, "Type": dtype} for col, dtype in schema_dict.items()]
        )
        st.dataframe(schema_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  MAIN AREA COMPONENTS
# ─────────────────────────────────────────────

def render_hero():
    """Renders the main hero header section."""
    st.markdown(
        """
        <div class="hero-section">
          <div style="font-size:13px; font-weight:500; letter-spacing:3px; color:#555;
                      text-transform:uppercase; margin-bottom:12px;">
            ✦ AI-Powered Analytics
          </div>
          <h1 style="margin:0;">🦆 NL Analytics</h1>
          <div class="hero-divider"></div>
          <p style="color:#718096; font-size:16px; margin-top:16px; margin-bottom:16px;
                    font-weight:400; max-width:600px; margin-left:auto; margin-right:auto;">
            Ask anything about your data in plain English.
            No SQL. No code. Just answers.
          </p>
          <div class="powered-by">
            Powered by &nbsp;
            <span>Llama 3.1</span> · <span>DuckDB</span> · <span>LangGraph</span> · <span>ChromaDB</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_question_chips(questions: list):
    """Renders clickable question chip buttons in a horizontal row."""
    st.markdown(
        '<div style="text-align:center; font-size:13px; color:#555; '
        'letter-spacing:1px; text-transform:uppercase; margin-bottom:10px;">'
        '✦ &nbsp;Try asking&nbsp; ✦</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(questions))
    selected = None
    for idx, q in enumerate(questions):
        if cols[idx].button(q, key=f"chip_{idx}", use_container_width=True):
            selected = q
    return selected


def render_progress_step(name: str, status: str):
    """Renders a styled pipeline step row."""
    icons = {
        "running":   "⏳",
        "completed": "✅",
        "failed":    "❌",
        "skipped":   "◽",
        "idle":      "○",
    }
    icon = icons.get(status, "○")
    label_class = {"running": "running", "completed": "done",
                   "failed": "failed", "skipped": "skipped"}.get(status, "")
    st.markdown(
        f'<div class="step-row">'
        f'  <div class="step-icon">{icon}</div>'
        f'  <div class="step-label {label_class}">{name}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_pipeline_header():
    """Renders the pipeline execution section header."""
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
          <div style="width:3px; height:20px; background:linear-gradient(180deg,#ff2a4b,transparent);
                      border-radius:2px; flex-shrink:0;"></div>
          <div style="font-size:14px; font-weight:600; color:#a0aec0;
                      text-transform:uppercase; letter-spacing:2px;">
            Pipeline Execution
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_section_header(intent: str, cached: bool):
    """Renders the result area badge."""
    if cached:
        badge = '<div class="badge-cached">⚡ &nbsp;Answered from cache</div>'
    elif intent == "rag":
        badge = '<div class="badge-rag">📄 &nbsp;Answered from documents</div>'
    else:
        badge = '<div class="badge-sql">📊 &nbsp;Answered via SQL</div>'
    st.markdown(badge, unsafe_allow_html=True)
