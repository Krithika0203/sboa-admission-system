import streamlit as st

def show():
    st.markdown("""
    <div class="main-header">
        <h1>🏫 SBOA Admission System</h1>
        <p style="font-size:1.1rem; opacity:0.9;">Powered by Groq AI · 13 Schools · Smart Admissions</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏫 Schools", "13", "All Tamil Nadu")
    with col2:
        st.metric("📝 Applications", "1,240", "+120 this week")
    with col3:
        st.metric("✅ Approved", "380", "+42 today")
    with col4:
        st.metric("🤖 AI Verified Docs", "3,600", "98.2% accuracy")

    st.markdown("---")
    st.subheader("🤖 AI Features Available")

    features = [
        ("💬", "AI Chatbot", "24/7 admission assistant in English, Hindi, Tamil",       "Go to AI Assistant"),
        ("📄", "OCR + Doc AI","Extract data from birth certificates & marksheets",       "Upload Documents"),
        ("✍️", "Auto Form Fill","Auto-fill application from uploaded documents",          "Apply Now"),
        ("✅", "Doc Validation","AI checks completeness & authenticity of documents",    "Upload Documents"),
        ("🔍", "Fraud Detection","Detect duplicate & fake applications instantly",        "Admin: Fraud Detection"),
        ("🏆", "Smart Scoring", "AI ranks applicants by distance, sibling, marks",       "Admin: Scoring"),
        ("📈", "Forecasting",   "Predict admission demand and conversion rates",          "Super Admin: Analytics"),
    ]

    for i in range(0, len(features), 2):
        c1, c2 = st.columns(2)
        for col, feat in zip([c1, c2], features[i:i+2]):
            icon, title, desc, btn = feat
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <h3>{icon} {title}</h3>
                    <p style="color:#555; margin:0">{desc}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("👈 Use the sidebar to navigate between Parent, School Admin, and Super Admin views.")
