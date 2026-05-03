import streamlit as st

st.set_page_config(
    page_title="SBOA Admission System",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebarNav"] { display: none; }
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .feature-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    .feature-card:hover { border-color: #2d6a9f; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .metric-box {
        background: #f0f7ff;
        border-left: 4px solid #2d6a9f;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-green { background: #d4edda; color: #155724; }
    .badge-orange { background: #fff3cd; color: #856404; }
    .badge-red { background: #f8d7da; color: #721c24; }
    .badge-blue { background: #cce5ff; color: #004085; }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        padding: 0.9rem 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 0.5rem;
    ">
        <div style="font-size: 1.6rem;">🏫</div>
        <div style="color: white; font-weight: 700; font-size: 1rem; letter-spacing: 0.05em;">SBOA Schools</div>
        <div style="color: #a8c8f0; font-size: 0.75rem; margin-top: 2px;">Admission Portal</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🏫 Navigation")

    role = st.selectbox("Login as", ["Parent", "School Admin", "Super Admin"], key="role")
    st.markdown("---")

    if role == "Parent":
        pages = {
            "🏠 Home": "home",
            "📝 Apply Now": "apply",
            "📄 My Applications": "my_applications",
            "🤖 AI Assistant": "chatbot",
            "📤 Upload Documents": "documents",
        }
    elif role == "School Admin":
        pages = {
            "📊 Dashboard": "admin_dashboard",
            "📋 Applications": "admin_applications",
            "✅ Doc Verification": "doc_verification",
            "🔍 Fraud Detection": "fraud_detection",
            "🏆 Scoring": "scoring",
            "📥 Import Data": "import_data",
        }
    else:
        pages = {
            "🌐 Super Dashboard": "super_dashboard",
            "📈 Analytics & Forecast": "analytics",
            "⚙️ Configure Rules": "config",
        }

    selected = st.radio("", list(pages.keys()), label_visibility="collapsed")
    page = pages[selected]

    st.markdown("---")
    st.caption("Powered by **Groq AI** 🤖")
    st.caption("llama-3.3-70b-versatile")


# Route to pages
if page == "home":
    from pages import home
    home.show()
elif page == "apply":
    from pages import apply
    apply.show()
elif page == "my_applications":
    from pages import my_applications
    my_applications.show()
elif page == "chatbot":
    from pages import chatbot
    chatbot.show()
elif page == "documents":
    from pages import documents
    documents.show()
elif page == "admin_dashboard":
    from pages import admin_dashboard
    admin_dashboard.show()
elif page == "admin_applications":
    from pages import admin_applications
    admin_applications.show()
elif page == "doc_verification":
    from pages import doc_verification
    doc_verification.show()
elif page == "fraud_detection":
    from pages import fraud_detection
    fraud_detection.show()
elif page == "scoring":
    from pages import scoring
    scoring.show()
elif page == "super_dashboard":
    from pages import super_dashboard
    super_dashboard.show()
elif page == "analytics":
    from pages import analytics
    analytics.show()
elif page == "config":
    from pages import config
    config.show()
elif page == "import_data":
    from pages import import_data
    import_data.show()
