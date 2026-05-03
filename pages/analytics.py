"""Super Admin — Analytics & AI Forecasting (Feature 7)"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.groq_ai import generate_forecast
from utils.data_store import find_all, seed_demo_data

def show():
    st.title("📈 Analytics & AI Forecasting")
    st.caption("Predict admission demand · Drop-off analysis · Conversion rates")
    seed_demo_data()

    apps = find_all("applications")
    df   = pd.DataFrame(apps) if apps else pd.DataFrame()

    tab1, tab2 = st.tabs(["📊 Live Analytics", "🤖 AI Forecast"])

    # ── TAB 1: Live Analytics ────────────────────────────────────────────────
    with tab1:
        if df.empty:
            st.info("No data yet.")
            return

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Applications by Status")
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig = px.funnel(status_counts, x="Count", y="Status",
                            color_discrete_sequence=["#2d6a9f"])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Score Distribution")
            if "score" in df.columns and df["score"].sum() > 0:
                fig2 = px.histogram(df, x="score", nbins=10,
                                    color_discrete_sequence=["#28a745"],
                                    labels={"score": "Admission Score"})
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Run scoring first to see distribution.")

        # Conversion funnel
        st.subheader("📉 Admission Funnel")
        total    = len(df)
        reviewed = len(df[df.status.isin(["Under Review", "Approved", "Rejected"])])
        approved = len(df[df.status == "Approved"])

        fig3 = go.Figure(go.Funnel(
            y=["Applications Received", "Reviewed", "Approved"],
            x=[total, reviewed, approved],
            textinfo="value+percent initial",
            marker_color=["#2d6a9f", "#17a2b8", "#28a745"]
        ))
        st.plotly_chart(fig3, use_container_width=True)

        # School comparison table
        st.subheader("🏫 School-wise Stats")
        school_stats = df.groupby("school").agg(
            Applications=("_id", "count"),
            Approved=("status", lambda x: (x == "Approved").sum()),
            Pending=("status", lambda x: (x == "Pending").sum()),
        ).reset_index()
        school_stats["Conversion %"] = (
            school_stats["Approved"] / school_stats["Applications"] * 100
        ).round(1)
        st.dataframe(school_stats, use_container_width=True)

    # ── TAB 2: AI Forecast ───────────────────────────────────────────────────
    with tab2:
        st.subheader("🤖 Groq AI Admission Forecast")
        st.info("AI analyzes current data and predicts demand, drop-offs, and conversion rates.")

        # Build stats summary for AI
        if not df.empty:
            current_stats = {
                "total_applications": len(df),
                "by_status": df["status"].value_counts().to_dict(),
                "by_school": df["school"].value_counts().head(5).to_dict(),
                "by_class": df["class_applying"].value_counts().to_dict(),
                "avg_score": float(df["score"].mean()) if "score" in df.columns else 0,
                "sibling_count": int(df["has_sibling"].sum()) if "has_sibling" in df.columns else 0,
                "ews_count": int(df["is_ews"].sum()) if "is_ews" in df.columns else 0,
                "conversion_rate": round(
                    len(df[df.status == "Approved"]) / len(df) * 100, 1
                ),
            }
        else:
            current_stats = {"total_applications": 0, "note": "No data yet"}


        if st.button("🚀 Generate AI Forecast", type="primary", use_container_width=True):
            with st.spinner("🤖 Groq AI is analyzing data and generating forecast..."):
                forecast = generate_forecast(current_stats)

            if "error" in forecast:
                st.error(f"AI error: {forecast}")
                return

            # Demand Forecast
            st.markdown("---")
            st.subheader("📊 Demand Forecast")
            demand = forecast.get("demand_forecast", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("Expected Applications",
                      demand.get("expected_total_applications", "N/A"))
            c2.metric("Confidence",
                      demand.get("confidence", "N/A").upper())
            c3.metric("Peak Week",
                      demand.get("peak_week", "N/A"))

            fast_schools = demand.get("schools_filling_fast", [])
            if fast_schools:
                st.warning(f"🔥 Schools filling fast: **{', '.join(fast_schools)}**")

            # Drop-off Analysis
            st.subheader("📉 Drop-off Analysis")
            dropoff = forecast.get("drop_off_analysis", {})
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Highest Drop-off Stage",
                          dropoff.get("highest_drop_off_stage", "N/A"))
                st.metric("Drop-off Rate",
                          f"{dropoff.get('drop_off_percentage', 0)}%")
            with col2:
                fix = dropoff.get("suggested_fix", "")
                if fix:
                    st.info(f"💡 **Suggested Fix:** {fix}")

            # Conversion Forecast
            st.subheader("📈 Conversion Forecast")
            conv = forecast.get("conversion_forecast", {})
            c1, c2 = st.columns(2)
            c1.metric("Predicted Conversion Rate",
                      f"{conv.get('predicted_rate_percent', 0)}%")
            c2.metric("Trend", conv.get("trend", "stable").upper())

            # Alerts
            alerts = forecast.get("alerts", [])
            if alerts:
                st.subheader("🚨 Alerts")
                for alert in alerts:
                    st.error(f"• {alert}")

            # Recommendations
            recs = forecast.get("recommendations", [])
            if recs:
                st.subheader("✅ AI Recommendations")
                for i, rec in enumerate(recs, 1):
                    st.success(f"{i}. {rec}")


