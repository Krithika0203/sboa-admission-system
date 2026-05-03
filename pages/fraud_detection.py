"""Admin — Fraud & Duplicate Detection (Feature 5)"""
import streamlit as st
import json
from services.groq_ai import detect_fraud
from utils.data_store import find_all, seed_demo_data

def show():
    st.title("🔍 Fraud & Duplicate Detection")
    st.caption("AI fuzzy matching · Handles spelling variations · Real-time check")
    seed_demo_data()

    tab1, tab2 = st.tabs(["🔎 Check New Application", "📋 Scan All Applications"])

    with tab1:
        st.subheader("Check a new application for duplicates")
        with st.form("fraud_check_form"):
            c1, c2 = st.columns(2)
            with c1:
                student_name = st.text_input("Student Name *", value="Rahul Sharma")
                dob          = st.text_input("Date of Birth", value="15/03/2019")
                class_app    = st.selectbox("Class Applying", ["LKG", "Class 1", "Class 6"])
            with c2:
                parent_phone = st.text_input("Parent Phone *", value="9876543210")
                parent_email = st.text_input("Parent Email", value="parent@email.com")
                school       = st.selectbox("School", ["SBOA Annanagar", "SBOA Mogappair", "SBOA Adyar"])

            submitted = st.form_submit_button("🔍 Run Fraud Check", type="primary", use_container_width=True)

        if submitted:
            new_app = {
                "student_name": student_name,
                "dob": dob,
                "class_applying": class_app,
                "phone": parent_phone,
                "email": parent_email,
                "school": school,
            }

            existing = find_all("applications")

            with st.spinner("🤖 AI is checking for duplicates and fraud..."):
                result = detect_fraud(new_app, existing)

            is_dup = result.get("is_duplicate", False)
            is_sus = result.get("is_suspicious", False)
            conf   = result.get("confidence", 0)

            if is_dup:
                st.error(f"🚨 DUPLICATE DETECTED — Confidence: {conf}%")
                st.error(f"Matched application ID: `{result.get('matched_id', 'N/A')}`")
            elif is_sus:
                st.warning(f"⚠️ SUSPICIOUS APPLICATION — Confidence: {conf}%")
            else:
                st.success(f"✅ No duplicates found — Confidence: {conf}%")

            flags = result.get("flags", [])
            if flags:
                st.markdown("**🚩 Red Flags:**")
                for flag in flags:
                    st.warning(f"• {flag}")

            st.info(f"📝 **Reason:** {result.get('reason', 'No issues detected')}")



    with tab2:
        st.subheader("Batch scan all applications")
        st.info("This runs AI fraud check on all pending applications.")

        apps = find_all("applications")
        pending = [a for a in apps if a.get("status") == "Pending"]
        st.write(f"**{len(pending)} pending applications** to scan")

        if st.button("🚀 Scan All Pending Applications", type="primary"):
            results = []
            progress = st.progress(0)
            status_text = st.empty()

            for i, app in enumerate(pending[:10]):  # limit to 10 for demo
                status_text.text(f"Checking {app.get('student_name')}...")
                others = [a for a in apps if a.get("_id") != app.get("_id")]
                result = detect_fraud(app, others)
                results.append({
                    "Name": app.get("student_name"),
                    "School": app.get("school"),
                    "Duplicate": "🚨 Yes" if result.get("is_duplicate") else "✅ No",
                    "Suspicious": "⚠️ Yes" if result.get("is_suspicious") else "✅ No",
                    "Confidence": f"{result.get('confidence', 0)}%",
                })
                progress.progress((i + 1) / min(len(pending), 10))

            status_text.text("Scan complete!")
            import pandas as pd
            st.dataframe(pd.DataFrame(results), use_container_width=True)
