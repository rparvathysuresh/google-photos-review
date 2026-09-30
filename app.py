import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Initialize backend services (bypassing FastAPI)
from backend.config import settings
from backend.db.database import SessionLocal, init_db
from backend.db.vector_store import vector_store
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode
from backend.services.rag.query_engine import query_engine
from backend.services.clustering.clusterer import clusterer
from backend.services.rag.embeddings import embedding_service
from backend.services.extraction.extractor import EpisodeExtractor
from backend.services.ingestion.appstore_adapter import AppStoreAdapter

# Configure Streamlit page
st.set_page_config(
    page_title="Discovery Engine",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Sidebar & Initialization ──────────────────────────────────────────

st.sidebar.title("🔍 Discovery Engine")
st.sidebar.markdown("AI-Powered Photo Retrieval Research")

# Ensure DB tables exist
init_db()

@st.cache_data(ttl=300)
def get_db_stats():
    """Get high-level stats from the database."""
    db = SessionLocal()
    try:
        feedback_count = db.query(FeedbackItem).count()
        episode_count = db.query(RetrievalEpisode).count()
        return feedback_count, episode_count
    finally:
        db.close()

feedback_count, episode_count = get_db_stats()

st.sidebar.divider()
st.sidebar.metric("Raw Reviews", feedback_count)
st.sidebar.metric("Extracted Episodes", episode_count)
st.sidebar.divider()

if st.sidebar.button("🚀 Re-Initialize Data"):
    with st.spinner("Fetching reviews from App Store..."):
        try:
            # 1. Fetch
            adapter = AppStoreAdapter()
            raw_data = adapter.fetch_data(limit=100)
            items = adapter.parse(raw_data)
            
            # 2. Save Feedback
            db = SessionLocal()
            for item in items:
                db.add(item)
            db.commit()
            
            # 3. Embed Feedback
            embedding_service.model  # Trigger lazy load
            embedding_service.embed_feedback_batch(items)
            
            # 4. Extract Episodes
            st.info(f"Extracting structured episodes from {len(items)} reviews using Groq...")
            extractor = EpisodeExtractor(db)
            extractor.process_batch(batch_size=len(items))
            
            # 5. Embed Episodes & Cluster
            episodes = db.query(RetrievalEpisode).all()
            if episodes:
                embedding_service.embed_episode_batch(episodes)
                st.info("Running UMAP clustering...")
                clusterer.run_clustering()
                
            st.success("Data initialization complete!")
            st.rerun()
        except Exception as e:
            st.error(f"Error during initialization: {e}")

# ── Main UI Navigation ────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🤖 Ask AI", "🧩 Problem Explorer"])

# ── TAB 1: Dashboard ──────────────────────────────────────────────────
with tab1:
    st.header("Research Dashboard")
    
    if episode_count == 0:
        st.info("No data found. Please click 'Re-Initialize Data' in the sidebar.")
    else:
        db = SessionLocal()
        episodes = db.query(RetrievalEpisode).all()
        db.close()
        
        if episodes:
            df = pd.DataFrame([
                {
                    "Cluster": ep.problem_cluster,
                    "Memory Type": ep.memory_type,
                    "Success": ep.retrieval_success
                } for ep in episodes
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Problem Clusters")
                cluster_counts = df['Cluster'].value_counts().reset_index()
                cluster_counts.columns = ['Cluster', 'Count']
                fig = px.pie(cluster_counts, values='Count', names='Cluster', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("Memory Types")
                mem_counts = df['Memory Type'].value_counts().reset_index()
                mem_counts.columns = ['Memory Type', 'Count']
                fig = px.bar(mem_counts, x='Memory Type', y='Count')
                st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: Ask AI ─────────────────────────────────────────────────────
with tab2:
    st.header("Ask the Research Engine")
    st.markdown("Query the vectorized extraction episodes using RAG.")
    
    # Sample Questions
    st.markdown("**Sample Questions:**")
    col_a, col_b = st.columns(2)
    sample_1 = "What kinds of old photos do users struggle to retrieve?"
    sample_2 = "What information do people actually remember about a photo?"
    sample_3 = "What information have they forgotten?"
    sample_4 = "How do users formulate searches when their memory is incomplete?"
    
    if col_a.button(sample_1):
        st.session_state.query = sample_1
    if col_a.button(sample_2):
        st.session_state.query = sample_2
    if col_b.button(sample_3):
        st.session_state.query = sample_3
    if col_b.button(sample_4):
        st.session_state.query = sample_4
        
    query = st.text_input("Enter your research question:", key="query")
    
    if st.button("Search") and query:
        with st.spinner("Searching vectors and generating answer..."):
            try:
                response = query_engine.ask(query)
                
                st.markdown("### Answer")
                st.write(response.answer)
                
                st.markdown(f"**Confidence:** {response.confidence} (Based on {response.evidence_count} sources)")
                
                with st.expander("View Citations & Evidence"):
                    for i, cit in enumerate(response.citations):
                        st.markdown(f"**Source {i+1}**")
                        st.markdown(f"> {cit.text_snippet}")
                        st.divider()
            except Exception as e:
                st.error(f"Failed to generate answer: {e}")

# ── TAB 3: Problem Explorer ───────────────────────────────────────────
with tab3:
    st.header("Problem Cluster Explorer")
    st.markdown("Browse raw user feedback grouped by semantic UMAP clusters.")
    
    if episode_count > 0:
        db = SessionLocal()
        episodes = db.query(RetrievalEpisode).all()
        db.close()
        
        clusters = list(set([ep.problem_cluster for ep in episodes if ep.problem_cluster]))
        
        selected_cluster = st.selectbox("Select a Cluster", ["All"] + clusters)
        
        filtered_eps = [ep for ep in episodes if selected_cluster == "All" or ep.problem_cluster == selected_cluster]
        
        st.write(f"Showing {len(filtered_eps)} episodes.")
        
        for ep in filtered_eps:
            with st.container():
                st.markdown(f"**Cluster:** `{ep.problem_cluster}` | **Success:** `{ep.retrieval_success}`")
                st.markdown(f"**Evidence:** {ep.supporting_evidence}")
                st.markdown(f"**Clues:** {', '.join(ep.remembered_clues) if ep.remembered_clues else 'None'}")
                st.divider()
    else:
        st.info("No clusters available. Please initialize data.")
