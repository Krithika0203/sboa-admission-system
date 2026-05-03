"""Admin — Applicant Scoring / Smart Prioritization (Feature 6)"""
import streamlit as st
import pandas as pd
import plotly.express as px
from services.groq_ai import score_applicant
from utils.data_store import find_all, update_by_id, seed_demo_data

def show():
    st.title("🏆 Applicant Scoring & Prioritization")
    st.caption("Rule-based + Groq AI · Distance · Sibling · Marks · EWS")
    seed_demo_data()

    tab1, tab2 = st.tabs(["🎯 Score Single Applicant", "📊 Score All Applications"])

    with tab1:
        st.subheader("Score an applicant manually")
        with st.form("score_form"):
            c1, c2 = st.columns(2)
            with c1:
                student_name  = st.text_input("Student Name", "Priya Sharma")
                distance_km   = st.number_input("Distance from school (km)", 0.1, 20.0, 1.5, 0.1)
                percentage    = st.number_input("Last exam percentage", 0.0, 100.0, 88.0)
            with c2:
                has_sibling   = st.checkbox("Has sibling in SBOA", value=True)
                is_ews        = st.checkbox("EWS candidate")
                is_staff_child= st.checkbox("Staff child")
                achievements  = st.text_input("Achievements (optional)", "State-level chess champion")

            submitted = st.form_submit_button("🤖 Calculate AI Score", type="primary", use_container_width=True)

        if submitted:
            application = {
                "student_name": student_name,
                "distance_km": distance_km,
                "percentage": percentage,
                "has_sibling": has_sibling,
                "is_ews": is_ews,
                "is_staff_child": is_staff_child,
                "achievements": achievements,
            }

            with st.spinner("🤖 AI is scoring this applicant..."):
                result = score_applicant(application)

            final = result.get("final_score", 0)
            rec   = result.get("recommendation", "medium")
            rec_colors = {"high_priority": "🟢", "medium": "🟡", "low": "🔴"}

            c1, c2, c3 = st.columns(3)
            c1.metric("Final Score", f"{final}/100")
            c2.metric("Rule Score", f"{result.get('rule_score', 0)}/85")
            c3.metric("AI Bonus", f"+{result.get('ai_bonus', 0)}/20")

            st.progress(final / 100)

            priority_label = {"high_priority": "🟢 HIGH PRIORITY", "medium": "🟡 MEDIUM", "low": "🔴 LOW"}.get(rec, rec)
            st.markdown(f"### Priority: {priority_label}")
            st.info(f"📝 Admin Note: {result.get('admin_note', '')}")

            # Breakdown chart
            breakdown = result.get("breakdown", [])
            if breakdown:
                df_b = pd.DataFrame(breakdown)
                fig = px.bar(df_b, x="points", y="criteria", orientation="h",
                             title="Score Breakdown",
                             color="points", color_continuous_scale="Teal")
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Score all applications at once")
        apps = find_all("applications")
        pending = [a for a in apps if a.get("status") == "Pending"]
        st.info(f"**{len(pending)} pending applications** will be scored")

        if st.button("🚀 Score All Pending Applications", type="primary"):
            results = []
            prog = st.progress(0)
            txt  = st.empty()

            for i, app in enumerate(pending[:10]):
                txt.text(f"Scoring {app.get('student_name')}...")
                res = score_applicant(app)
                update_by_id("applications", app["_id"], {"score": res["final_score"]})
                results.append({
                    "ID":          app.get("_id"),
                    "Name":        app.get("student_name"),
                    "Class":       app.get("class_applying"),
                    "School":      app.get("school"),
                    "Final Score": res["final_score"],
                    "Priority":    res["recommendation"],
                    "Admin Note":  res["admin_note"],
                })
                prog.progress((i + 1) / min(len(pending), 10))

            txt.text("Done!")
            df_r = pd.DataFrame(results).sort_values("Final Score", ascending=False)
            st.dataframe(df_r, use_container_width=True)

            fig = px.histogram(df_r, x="Final Score", nbins=10,
                               title="Score Distribution", color_discrete_sequence=["#2d6a9f"])
            st.plotly_chart(fig, use_container_width=True)
