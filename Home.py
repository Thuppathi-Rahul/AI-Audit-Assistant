import streamlit as st
from dotenv import load_dotenv

# Load environment variables at the very start
load_dotenv()

st.set_page_config(
    page_title="AI Audit Assistant Home",
    page_icon="🤖",
    layout="wide"
)

# --- Custom CSS for the OpenAI-inspired theme with colors ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Main background and font styling */
    .stApp {
        background: linear-gradient(180deg, #F9FAFB 0%, #FFFFFF 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Main content container */
    .main-container {
        padding: 2rem 4rem;
    }
    
    /* Main heading for the left column */
    .main-heading {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827; /* Very dark gray */
        line-height: 1.3;
    }
    
    /* Main paragraph for the left column */
    .main-paragraph {
        font-size: 1.1rem;
        color: #4B5563; /* Medium gray */
        margin-top: 1rem;
        line-height: 1.6;
    }

    /* "Get Started" card on the right */
    .get-started-card {
        background-color: #eef2ff; /* Light Indigo background */
        border: 1px solid #dbeafe; /* Light Blue border */
        border-radius: 12px;
        padding: 2rem;
        height: 100%;
    }
    .get-started-card h3 {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e3a8a; /* Dark Blue */
    }
    .get-started-card ol {
        padding-left: 25px;
    }
    .get-started-card li {
        font-size: 1rem;
        color: #374151;
        margin-bottom: 0.75rem;
        line-height: 1.5;
    }
    .get-started-card li::marker {
        color: #4338ca; /* Indigo marker color */
    }

    /* "Core Features" section */
    .features-header {
        font-size: 1.75rem;
        font-weight: 600;
        color: #111827;
        margin-top: 4rem;
        margin-bottom: 1.5rem;
    }

    /* Individual feature cards */
    .feature-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1.5rem;
        transition: box-shadow 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .feature-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .feature-card h4 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1E3A8A; /* Dark blue */
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .feature-card .icon {
        font-size: 1.2rem;
        margin-right: 0.5rem;
        color: #60a5fa; /* Lighter Blue */
    }

</style>
""", unsafe_allow_html=True)


# --- Main Container ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# --- Top Section: Introduction & Get Started ---
col1, col2 = st.columns([1.2, 1], gap="large")

with col1:
    st.markdown('<h1 class="main-heading">AI Audit Assistant Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-paragraph">An integrated suite of tools to automate, manage, and report on your entire audit workflow. Use the sidebar to navigate between the core functions of the application.</p>', unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="get-started-card">
        <h3>Get started</h3>
        <p>Follow these steps to complete your first AI-powered audit:</p>
        <ol>
            <li><strong>Schedule Audit:</strong> Select your project and define the audit scope.</li>
            <li><strong>Run Audit:</strong> Upload documents and start the AI analysis.</li>
            <li><strong>Summary Dashboard:</strong> View high-level scores and charts.</li>
            <li><strong>Review & Report:</strong> Drill down into details and download reports.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# --- Bottom Section: Core Features ---
st.markdown('<h2 class="features-header">Core Features</h2>', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4><span class="icon">🗓️</span>Audit Scheduling</h4>
        <p>Dynamically manage projects and define a precise scope for every audit.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="feature-card">
        <h4><span class="icon">🚀</span>AI-Powered Analysis</h4>
        <p>Leverage a powerful AI agent to analyze documents against a 41-point checklist.</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="feature-card">
        <h4><span class="icon">📊</span>Visual Dashboards</h4>
        <p>Track compliance scores and answer distributions with interactive charts.</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="feature-card">
        <h4><span class="icon">📝</span>Actionable Reports</h4>
        <p>Generate formatted Excel and Word documents for final review and remediation.</p>
    </div>
    """, unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True) # End main container
st.sidebar.success("Select a page above to begin.")

