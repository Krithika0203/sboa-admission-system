"""Super Admin — Cross-school dashboard"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_store import find_all, seed_demo_data

def show():
    st.title("🌐 Super Admin Dashboard")
    st.caption("Head office view · All 13 SBOA schools · Real-time")
    seed_demo_data()

    apps = find_all("applications")
    if not apps:
        st.warning("No data yet.")
        return

    df = pd.DataFrame(apps)

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🏫 Schools",        "13")
    c2.metric("📝 Total Apps",     len(df))
    c3.metric("✅ Approved",       len(df[df.status == "Approved"]))
    c4.metric("⏳ Pending",        len(df[df.status == "Pending"]))
    c5.metric("📊 Avg Score",      f"{df['score'].mean():.0f}" if "score" in df.columns else "N/A")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 School-wise Applications")
        school_df = df.groupby(["school", "status"]).size().reset_index(name="count")
        fig = px.bar(school_df, x="school", y="count", color="status",
                     barmode="stack",
                     color_discrete_map={
                         "Approved": "#28a745", "Pending": "#ffc107",
                         "Under Review": "#17a2b8", "Rejected": "#dc3545"
                     })
        fig.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📚 Class-wise Demand")
        class_df = df["class_applying"].value_counts().reset_index()
        class_df.columns = ["class", "count"]
        fig2 = px.pie(class_df, names="class", values="count",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🏆 School Performance Comparison")
    perf = df.groupby("school").agg(
        Total=("_id", "count"),
        Approved=("status", lambda x: (x == "Approved").sum()),
        Avg_Score=("score", "mean")
    ).reset_index()
    perf["Conversion %"] = (perf["Approved"] / perf["Total"] * 100).round(1)
    perf["Avg_Score"] = perf["Avg_Score"].round(1)
    st.dataframe(perf.sort_values("Total", ascending=False), use_container_width=True)

    st.subheader("🗺️ Score Distribution Across All Schools")
    if "score" in df.columns:
        fig3 = px.box(df, x="school", y="score", color="school",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig3.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
