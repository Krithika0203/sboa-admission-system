"""School Admin — Dashboard"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_store import find_all, seed_demo_data

def show():
    st.title("📊 School Admin Dashboard")
    seed_demo_data()

    apps = find_all("applications")
    if not apps:
        st.warning("No applications yet.")
        return

    df = pd.DataFrame(apps)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Applications", len(df))
    c2.metric("Pending", len(df[df.status == "Pending"]))
    c3.metric("Approved", len(df[df.status == "Approved"]))
    c4.metric("Rejected", len(df[df.status == "Rejected"]))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Applications by Status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Applications by School")
        school_counts = df["school"].value_counts().reset_index()
        school_counts.columns = ["school", "count"]
        fig2 = px.bar(school_counts, x="count", y="school", orientation="h",
                      color="count", color_continuous_scale="Blues")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Applications by Class")
    class_counts = df["class_applying"].value_counts().reset_index()
    class_counts.columns = ["class", "count"]
    fig3 = px.bar(class_counts, x="class", y="count",
                  color="count", color_continuous_scale="Teal")
    st.plotly_chart(fig3, use_container_width=True)
