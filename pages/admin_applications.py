"""School Admin — Applications management"""
import streamlit as st
import pandas as pd
from utils.data_store import find_all, update_by_id, seed_demo_data

def show():
    st.title("📋 Manage Applications")
    seed_demo_data()

    apps = find_all("applications")
    df = pd.DataFrame(apps)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        school_filter = st.selectbox("Filter by School", ["All"] + sorted(df["school"].unique().tolist()))
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Under Review", "Approved", "Rejected"])
    with col3:
        class_filter = st.selectbox("Filter by Class", ["All"] + sorted(df["class_applying"].unique().tolist()))

    filtered = df.copy()
    if school_filter != "All": filtered = filtered[filtered.school == school_filter]
    if status_filter != "All": filtered = filtered[filtered.status == status_filter]
    if class_filter != "All": filtered = filtered[filtered.class_applying == class_filter]

    st.markdown(f"**Showing {len(filtered)} applications**")

    # Display
    display_cols = ["_id", "student_name", "class_applying", "school", "status", "score", "created_at"]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[available], use_container_width=True, height=350)

    # Quick action
    st.markdown("---")
    st.subheader("⚡ Quick Action")
    app_ids = filtered["_id"].tolist()
    if app_ids:
        selected_id = st.selectbox("Select Application ID", app_ids)
        new_status = st.selectbox("Change Status to", ["Pending", "Under Review", "Approved", "Rejected"])
        if st.button("✅ Update Status", type="primary"):
            update_by_id("applications", selected_id, {"status": new_status})
            st.success(f"Application {selected_id} updated to **{new_status}**")
            st.rerun()
