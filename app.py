import streamlit as st
from dotenv import load_dotenv
load_dotenv()  # MUST run before importing local modules that reference environment variables

import time
import os
import shutil

# Local Module Imports
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question
from utils.pdf_generator import generate_meeting_pdf
from utils.history_manager import save_meeting, list_meetings, load_meeting, delete_meeting

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS (Glassmorphism & Neon Glow) ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* Global Reset & Base Setup */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #040408 !important;
    color: #e2e8f0 !important;
}

.stApp {
    background: linear-gradient(135deg, #040408 0%, #0c0c16 100%) !important;
}

/* Background animated glow overlay */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: 
        radial-gradient(circle at 80% 20%, rgba(124, 58, 237, 0.07) 0%, transparent 40%),
        radial-gradient(circle at 15% 80%, rgba(6, 182, 212, 0.07) 0%, transparent 40%),
        linear-gradient(rgba(255, 255, 255, 0.01) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.01) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 30px 30px, 30px 30px;
    pointer-events: none;
    z-index: 0;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: rgba(8, 8, 16, 0.9) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.15) !important;
    backdrop-filter: blur(20px);
}

[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: #ffffff !important;
}

/* Hero Title */
.glow-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    line-height: 1.1;
    background: linear-gradient(135deg, #ffffff 10%, #a78bfa 50%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.1rem;
    text-shadow: 0 0 40px rgba(167, 139, 250, 0.1);
}

.glow-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #7070a0;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* Glass Cards & Containers */
.glass-card {
    background: rgba(18, 18, 28, 0.65) !important;
    border: 1px solid rgba(124, 58, 237, 0.12) !important;
    border-radius: 16px !important;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
    transition: all 0.3s ease-in-out;
}

.glass-card:hover {
    border-color: rgba(124, 58, 237, 0.35) !important;
    box-shadow: 0 8px 32px 0 rgba(124, 58, 237, 0.08);
    transform: translateY(-2px);
}

.card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.9rem;
    line-height: 1.7;
    color: #e2e8f0;
}

/* Accent Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.badge-purple { background: rgba(124, 58, 237, 0.15); color: #c084fc; border: 1px solid rgba(124, 58, 237, 0.3); }
.badge-cyan   { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
.badge-green  { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-orange { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

/* Progress Overrides */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #7c3aed, #06b6d4) !important;
}

/* Form Controls & Buttons */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background: rgba(26, 26, 38, 0.8) !important;
    border: 1px solid rgba(124, 58, 237, 0.2) !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #4c1d95 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.55rem 1.6rem !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2) !important;
    transition: all 0.3s ease !important;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.45) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
}

.stButton > button[kind="secondary"] {
    background: rgba(18, 18, 28, 0.6) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(124, 58, 237, 0.3) !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"]:hover {
    background: rgba(124, 58, 237, 0.12) !important;
    color: #ffffff !important;
    border-color: #7c3aed !important;
}

/* Tabs selectors style */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(18, 18, 28, 0.5);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid rgba(124, 58, 237, 0.1);
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    background-color: transparent;
    border-radius: 8px;
    color: #94a3b8 !important;
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    transition: all 0.2s ease;
    border: none;
    padding: 0 18px;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #ffffff !important;
    background-color: rgba(255, 255, 255, 0.03);
}

.stTabs [aria-selected="true"] {
    background-color: rgba(124, 58, 237, 0.15) !important;
    color: #c084fc !important;
    border: 1px solid rgba(124, 58, 237, 0.3) !important;
}

/* Sidebar Pipeline Steps Indicator */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.65rem 0.85rem;
    background: rgba(26, 26, 38, 0.6);
    border-radius: 8px;
    margin: 0.35rem 0;
    border: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.78rem;
}

.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active   { background: #a78bfa; box-shadow: 0 0 8px #a78bfa; animation: pulse 1.5s infinite; }
.dot-done     { background: #10b981; }
.dot-pending  { background: rgba(255,255,255,0.1); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* Chat container & bubble styles */
.chat-container {
    background: rgba(12, 12, 22, 0.8);
    border: 1px solid rgba(124, 58, 237, 0.15);
    border-radius: 16px;
    padding: 1.25rem;
    max-height: 400px;
    overflow-y: auto;
    margin-bottom: 1.25rem;
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
}

.chat-bubble-row {
    display: flex;
    margin-bottom: 1rem;
    align-items: flex-start;
}

.chat-bubble-row.user {
    justify-content: flex-end;
}

.chat-bubble-row.assistant {
    justify-content: flex-start;
}

.chat-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    margin-right: 0.75rem;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.chat-bubble-row.user .chat-avatar {
    margin-right: 0;
    margin-left: 0.75rem;
    order: 2;
    background: linear-gradient(135deg, #7c3aed, #6366f1);
}

.chat-bubble-row.assistant .chat-avatar {
    background: linear-gradient(135deg, #06b6d4, #0891b2);
}

.chat-content-box {
    max-width: 75%;
    display: flex;
    flex-direction: column;
}

.chat-bubble {
    padding: 0.7rem 1.1rem;
    border-radius: 12px;
    font-size: 0.88rem;
    line-height: 1.6;
    color: #e2e8f0;
}

.chat-bubble-row.user .chat-bubble {
    background: rgba(124, 58, 237, 0.18);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-top-right-radius: 2px;
}

.chat-bubble-row.assistant .chat-bubble {
    background: rgba(6, 182, 212, 0.12);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-top-left-radius: 2px;
}

.chat-meta {
    font-size: 0.65rem;
    color: #64748b;
    margin-top: 0.25rem;
    padding: 0 0.5rem;
}

.chat-bubble-row.user .chat-meta {
    text-align: right;
}

/* Transcript scroll box */
.transcript-box {
    background: rgba(10, 10, 15, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 1.25rem;
    font-size: 0.88rem;
    line-height: 1.8;
    max-height: 350px;
    overflow-y: auto;
    color: #94a3b8;
    white-space: pre-wrap;
    word-break: break-word;
}

.highlight {
    background-color: rgba(245, 158, 11, 0.28);
    color: #fcd34d;
    border-bottom: 1px solid #fbbf24;
    padding: 0 2px;
    border-radius: 2px;
}

/* Custom scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(8, 8, 16, 0.4);
}
::-webkit-scrollbar-thumb {
    background: rgba(124, 58, 237, 0.25);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(124, 58, 237, 0.5);
}
</style>
""", unsafe_allow_html=True)

# ─── Helper Functions ───────────────────────────────────────────────────────────
def clear_vector_db():
    """Wipes the local Chroma DB collection programmatically to prevent readonly DB locks on Windows."""
    try:
        from core.vector_store import load_vector_store
        db = load_vector_store()
        db.delete_collection()
        print("Chroma collection cleared successfully via delete_collection().")
    except Exception as e:
        print(f"Warning: Could not clear Chroma collection: {e}")
        # Fallback to shutil.rmtree if the programmatic clear fails
        if os.path.exists("vector_db"):
            try:
                shutil.rmtree("vector_db", ignore_errors=True)
            except Exception as re:
                print(f"Warning: Could not wipe vector_db directory: {re}")

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
    "loaded_meeting_id": None,
    "chip_question": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Sidebar Area ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="glow-title" style="font-size:1.6rem">🎬 AI Video</div>', unsafe_allow_html=True)
    st.markdown('<div class="glow-sub" style="margin-bottom:1rem">Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(124,58,237,0.15)'/>", unsafe_allow_html=True)

    # ── History Loader ──
    meetings = list_meetings()
    if meetings:
        st.markdown('<span class="badge badge-purple">📁 Reload Previous Session</span>', unsafe_allow_html=True)
        meeting_titles = [f"{m['title']} ({m['timestamp'][:10]})" for m in meetings]
        selected_option = st.selectbox(
            "Select past analysis",
            ["-- Choose Saved Meeting --"] + meeting_titles,
            label_visibility="collapsed"
        )
        
        if selected_option != "-- Choose Saved Meeting --":
            selected_idx = meeting_titles.index(selected_option)
            selected_meeting = meetings[selected_idx]
            
            if st.session_state.loaded_meeting_id != selected_meeting["meeting_id"]:
                try:
                    with st.spinner("Loading meeting history..."):
                        meeting_data = load_meeting(selected_meeting["meeting_id"])
                        st.session_state.result = meeting_data
                        st.session_state.loaded_meeting_id = selected_meeting["meeting_id"]
                        st.session_state.chat_history = []
                        st.session_state.pipeline_done = True
                        
                        # Rebuild vector store dynamically for historical items so RAG is functional
                        clear_vector_db()
                        st.session_state.result["rag_chain"] = build_rag_chain(meeting_data["transcript"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading meeting: {e}")
            
            # Delete Button
            if st.button("🗑️ Delete Selected Session", type="secondary", use_container_width=True):
                delete_meeting(selected_meeting["meeting_id"])
                if st.session_state.loaded_meeting_id == selected_meeting["meeting_id"]:
                    st.session_state.result = None
                    st.session_state.loaded_meeting_id = None
                    st.session_state.chat_history = []
                    st.session_state.pipeline_done = False
                st.success("Deleted successfully!")
                time.sleep(1)
                st.rerun()
                
        st.markdown("<hr style='border-color:rgba(124,58,237,0.15)'/>", unsafe_allow_html=True)

    # ── Input Settings ──
    st.markdown('<span class="badge badge-cyan">📥 Source Settings</span>', unsafe_allow_html=True)
    
    source_type = st.radio("Media Location", ["YouTube URL", "Local Upload", "Local File Path"], index=0)
    
    source_val = ""
    uploaded_file = None
    
    if source_type == "YouTube URL":
        source_val = st.text_input("YouTube Link", placeholder="https://youtube.com/watch?v=...")
    elif source_type == "Local Upload":
        uploaded_file = st.file_uploader("Upload Audio/Video File", type=["mp3", "mp4", "wav", "m4a", "avi"])
    else:
        source_val = st.text_input("Server File Path", placeholder="C:/meetings/finance_sync.mp4")

    language = "english"
    
    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    run_btn = st.button("⚡ Analyse Meeting", use_container_width=True)

    # ── Live Pipeline Tracker ──
    if st.session_state.pipeline_done or st.session_state.processing:
        st.markdown("<hr style='border-color:rgba(124,58,237,0.15)'/>", unsafe_allow_html=True)
        st.markdown('<span class="badge badge-green">⚙️ Pipeline Status</span>', unsafe_allow_html=True)
        
        steps_list = [
            ("audio",      "🔊 Audio Processing"),
            ("transcript", "📝 Speech Transcription"),
            ("title",      "🏷️ Title Generation"),
            ("summary",    "📋 Summarisation"),
            ("extract",    "🔍 Insight Extraction"),
            ("rag",        "🧠 RAG Vector Build"),
        ]
        
        for step, label in steps_list:
            s = st.session_state.pipeline_steps.get(step, "pending")
            dot_class = "dot-pending"
            if s == "active":  dot_class = "dot-active"
            elif s == "done":  dot_class = "dot-done"
            
            st.markdown(f"""
            <div class="status-bar">
                <div class="status-dot {dot_class}"></div>
                <span>{label}</span>
            </div>""", unsafe_allow_html=True)

# ─── Main Content Workspace ─────────────────────────────────────────────────────
st.markdown('<div class="glow-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="glow-sub">Transcribe · Summarise · Extract Action Items · Chat with Meetings</div>', unsafe_allow_html=True)

# ── Formulate and Run Pipeline ──────────────────────────────────────────────────
if run_btn:
    # Setup inputs
    is_valid = True
    input_source = ""
    
    if source_type == "YouTube URL" and not source_val.strip():
        st.error("Please enter a valid YouTube URL.")
        is_valid = False
    elif source_type == "Local File Path" and not source_val.strip():
        st.error("Please enter a valid local file path.")
        is_valid = False
    elif source_type == "Local Upload" and not uploaded_file:
        st.error("Please upload an audio or video file.")
        is_valid = False
        
    if is_valid:
        st.session_state.processing = True
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {k: "pending" for k in ["audio", "transcript", "title", "summary", "extract", "rag"]}
        st.session_state.loaded_meeting_id = None
        
        progress_msg = st.empty()
        
        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state
            
        try:
            # Handle Local Upload file saving
            if source_type == "Local Upload" and uploaded_file:
                progress_msg.info("💾 Saving uploaded file to local server...")
                os.makedirs("downloads", exist_ok=True)
                local_path = os.path.join("downloads", uploaded_file.name)
                with open(local_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                input_source = local_path
            else:
                input_source = source_val.strip()

            with progress_msg.container():
                st.info("⚙️ Initializing meeting analyzer pipeline. Check sidebar for active stages.")

            # Stage 1: Audio acquisition/processing
            update_step("audio", "active")
            chunks = process_input(input_source)
            update_step("audio", "done")

            # Stage 2: Local speech transcription
            update_step("transcript", "active")
            transcript = transcribe_all(chunks, language)
            update_step("transcript", "done")

            # Stage 3: Title Generation
            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            # Stage 4: Meeting Summary
            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            # Stage 5: Extracts
            update_step("extract", "active")
            action_items = extract_action_items(transcript)
            decisions    = extract_key_decisions(transcript)
            questions    = extract_questions(transcript)
            update_step("extract", "done")

            # Stage 6: RAG DB Setup
            update_step("rag", "active")
            clear_vector_db()  # Make sure we clean old Chroma collection
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            # Consolidate results
            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "source": input_source,
            }
            
            # Save meeting results to local history database
            meeting_id = save_meeting(st.session_state.result)
            st.session_state.loaded_meeting_id = meeting_id
            
            # Save the active chain object inside session state
            st.session_state.result["rag_chain"] = rag_chain
            
            st.session_state.pipeline_done = True
            st.session_state.processing = False
            
            progress_msg.success("🎉 Meeting analysis completed successfully!")
            time.sleep(1)
            progress_msg.empty()
            st.rerun()

        except Exception as e:
            st.session_state.processing = False
            for k in ["audio", "transcript", "title", "summary", "extract", "rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_msg.error(f"❌ Pipeline failed: {e}")

# ─── Render Results Dashboard ──────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    
    # Quick Check: Ensure RAG vector store is active
    if "rag_chain" not in r or r["rag_chain"] is None:
        clear_vector_db()
        with st.spinner("Initializing Chat Vector DB for selected session..."):
            r["rag_chain"] = build_rag_chain(r["transcript"])

    # Title Card
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid #7c3aed !important;">
        <span class="badge badge-purple">📌 Meeting Session</span>
        <div style="font-family:'Outfit',sans-serif; font-size:1.6rem; font-weight:700; color:#ffffff; margin-top:0.25rem;">
            {r['title']}
        </div>
        <div style="font-size:0.75rem; color:#7070a0; margin-top:0.35rem; font-family:'JetBrains Mono', monospace;">
            Source Location: {r['source']}
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Workspace Tabbed Interface ──
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Executive Summary", 
        "📋 Action Items", 
        "🔑 Key Decisions", 
        "❓ Open Questions",
        "📝 Transcript Explorer", 
        "💬 Chat Assistant"
    ])

    with tab1:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        col_main, col_side = st.columns([3, 2], gap="large")
        
        with col_main:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-title">📋 Executive Summary</div>
                <div class="card-content">{r['summary']}</div>
            </div>""", unsafe_allow_html=True)
            
        with col_side:
            # Video or Audio Player depending on type
            source_path = r['source']
            is_yt = source_path.startswith("http")
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🎬 Media Player</div>', unsafe_allow_html=True)
            if is_yt:
                st.video(source_path)
            elif source_path.endswith((".mp4", ".avi", ".mov", ".mkv")):
                if os.path.exists(source_path):
                    st.video(source_path)
                else:
                    st.warning("Video file not found at the original path.")
            elif source_path.endswith((".mp3", ".wav", ".m4a", ".aac")):
                if os.path.exists(source_path):
                    st.audio(source_path)
                else:
                    st.warning("Audio file not found at the original path.")
            else:
                st.info("No playable media file or external URL is configured.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Quick Stats Panel
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-title">📊 Session Details</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:0.82rem; line-height: 1.8;">
                    • <b>Status:</b> Analyzed<br>
                    • <b>RAG DB:</b> Active (k=4)<br>
                    • <b>Embedding Model:</b> all-MiniLM-L6-v2<br>
                    • <b>Summarizer Model:</b> mistral-small-latest<br>
                </div>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #10b981 !important;">
            <div class="card-title" style="color:#10b981">✅ Action Items Checklist</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #06b6d4 !important;">
            <div class="card-title" style="color:#06b6d4">🔑 Key Decisions Logged</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with tab4:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="border-left: 4px solid #f59e0b !important;">
            <div class="card-title" style="color:#f59e0b">❓ Open Questions & Follow-ups</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    with tab5:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown("### 📝 Search Transcript")
        search_query = st.text_input("Search term", placeholder="Type keywords to filter and highlight...", label_visibility="collapsed")
        
        raw_transcript = r["transcript"]
        
        if search_query.strip():
            import re
            escaped_query = re.escape(search_query.strip())
            # Replace case-insensitive matches with highlight wrapper
            highlighted_transcript = re.sub(
                f"({escaped_query})",
                r'<span class="highlight">\1</span>',
                raw_transcript,
                flags=re.IGNORECASE
            )
            st.markdown(f'<div class="transcript-box">{highlighted_transcript}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="transcript-box">{raw_transcript}</div>', unsafe_allow_html=True)

    with tab6:
        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
        st.markdown("### 💬 Chat with your Meeting Assistant")
        st.caption("Ask questions about the content of this meeting transcript. The AI answer is grounded in the transcript context.")

        # Suggestion chips processing
        if "chip_question" in st.session_state and st.session_state.chip_question:
            q = st.session_state.chip_question
            st.session_state.chip_question = None
            with st.spinner("Analyzing transcript for answers..."):
                answer = ask_question(r["rag_chain"], q)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        # Render suggestion chips UI
        st.markdown("<div style='font-size:0.75rem; color:#7070a0; font-weight:700; text-transform:uppercase;'>💡 Quick Prompts</div>", unsafe_allow_html=True)
        chip_col1, chip_col2, chip_col3 = st.columns(3)
        with chip_col1:
            if st.button("📋 Summarise meeting key points", key="chip_key_1", type="secondary"):
                st.session_state.chip_question = "Summarize the core points discussed during this meeting."
                st.rerun()
        with chip_col2:
            if st.button("✅ List action items & owners", key="chip_key_2", type="secondary"):
                st.session_state.chip_question = "List all action items, who is responsible for each, and deadlines if mentioned."
                st.rerun()
        with chip_col3:
            if st.button("🔑 What were the main decisions?", key="chip_key_3", type="secondary"):
                st.session_state.chip_question = "List the key decisions made during the meeting."
                st.rerun()

        # Render chat history
        if st.session_state.chat_history:
            chat_html = '<div class="chat-container">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    chat_html += f"""
                    <div class="chat-bubble-row user">
                        <div class="chat-avatar">👤</div>
                        <div class="chat-content-box">
                            <div class="chat-bubble">{msg['content']}</div>
                            <div class="chat-meta">You</div>
                        </div>
                    </div>"""
                else:
                    chat_html += f"""
                    <div class="chat-bubble-row assistant">
                        <div class="chat-avatar">🤖</div>
                        <div class="chat-content-box">
                            <div class="chat-bubble">{msg['content']}</div>
                            <div class="chat-meta">AI Assistant</div>
                        </div>
                    </div>"""
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center; padding:2.5rem 1rem;">
                <div style="font-size:2.5rem; margin-bottom:0.75rem;">💬</div>
                <div style="font-size:0.95rem; font-weight:600; color:#ffffff; margin-bottom:0.25rem;">Start the Conversation</div>
                <div style="color:#7070a0; font-size:0.8rem; max-width:350px; margin:0 auto;">Ask any questions, seek clarifications, or request email drafts based on this meeting.</div>
            </div>""", unsafe_allow_html=True)

        # Form text box to avoid double-firing or text retention
        with st.form("chat_box_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns([5, 1], gap="small")
            with f_col1:
                chat_input = st.text_input("Chat Query", placeholder="Ask a question about the meeting...", label_visibility="collapsed")
            with f_col2:
                chat_submit = st.form_submit_button("Send →")

        if chat_submit and chat_input.strip():
            q = chat_input.strip()
            with st.spinner("Analyzing transcript for answers..."):
                answer = ask_question(r["rag_chain"], q)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()

    # ── Export & Report Section ──
    st.markdown("<hr style='border-color:rgba(124,58,237,0.15)'/>", unsafe_allow_html=True)
    st.markdown("### 📤 Export & Generate Reports")
    st.write("Download formatted report outputs from the processed meeting.")
    
    # Generate PDF bytes
    pdf_bytes = generate_meeting_pdf(
        title=r["title"],
        summary=r["summary"],
        action_items=r["action_items"],
        decisions=r["key_decisions"],
        questions=r["open_questions"],
        transcript=r["transcript"]
    )
    
    # Markdown text representation
    md_report = f"""# Meeting Analysis: {r['title']}
    
## Executive Summary
{r['summary']}

## Action Items
{r['action_items']}

## Key Decisions
{r['key_decisions']}

## Open Questions
{r['open_questions']}

---
*Report generated automatically by AI Video Assistant.*
"""

    # JSON representation
    import json
    json_repr = json.dumps({
        "title": r["title"],
        "summary": r["summary"],
        "action_items": r["action_items"],
        "key_decisions": r["key_decisions"],
        "open_questions": r["open_questions"],
        "transcript": r["transcript"],
        "source": r["source"]
    }, indent=4)

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"Meeting_Report_{st.session_state.loaded_meeting_id}.pdf",
            mime="application/pdf"
        )
    with dl_col2:
        st.download_button(
            label="📝 Download Markdown Summary",
            data=md_report,
            file_name=f"Meeting_Summary_{st.session_state.loaded_meeting_id}.md",
            mime="text/markdown"
        )
    with dl_col3:
        st.download_button(
            label="⚙️ Download Raw JSON Data",
            data=json_repr,
            file_name=f"Meeting_Metadata_{st.session_state.loaded_meeting_id}.json",
            mime="application/json"
        )

else:
    # ── Empty Landing Page State ──
    st.markdown("""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:6rem 2rem; text-align:center;">
        <div style="font-size:4.5rem; margin-bottom:1.5rem; filter: drop-shadow(0 0 15px rgba(124,58,237,0.3));">🎬</div>
        <div style="font-family:'Outfit',sans-serif; font-size:1.8rem; font-weight:800; color:#ffffff; margin-bottom:0.75rem;">
            Ready to Begin Analysis
        </div>
        <div style="color:#7070a0; font-size:0.92rem; max-width:440px; line-height:1.8; margin-bottom:2rem;">
            Upload a local meeting file, paste a YouTube link, or supply a local file path in the sidebar, then hit <strong>Analyse Meeting</strong> to convert meeting audio into structured, interactive intelligence.
        </div>
        <div style="display:flex; gap:0.75rem; flex-wrap:wrap; justify-content:center;">
            <span class="badge badge-purple">🔊 Audio Processing</span>
            <span class="badge badge-cyan">📝 Transcription</span>
            <span class="badge badge-green">🧠 RAG Chat Assistant</span>
        </div>
    </div>""", unsafe_allow_html=True)