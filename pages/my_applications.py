"""Parent - My Applications page"""
import streamlit as st
from utils.data_store import find_all, seed_demo_data

STATUS_COLORS = {
    "Pending":      ("🟡", "badge-orange"),
    "Under Review": ("🔵", "badge-blue"),
    "Approved":     ("🟢", "badge-green"),
    "Rejected":     ("🔴", "badge-red"),
}

def show():
    st.title("📄 My Applications")
    seed_demo_data()

    search = st.text_input("🔍 Search by student name or phone")
    apps = find_all("applications")

    if search:
        apps = [a for a in apps if
                search.lower() in a.get("student_name", "").lower() or
                search in a.get("phone", "")]

    if not apps:
        st.info("No applications found. Go to 'Apply Now' to submit one.")
        return

    st.markdown(f"**{len(apps)} application(s) found**")

    for app in apps[:10]:  # show latest 10
        emoji, css = STATUS_COLORS.get(app.get("status", "Pending"), ("🟡", "badge-orange"))
        with st.expander(f"{emoji} {app.get('student_name', 'N/A')} — {app.get('class_applying')} @ {app.get('school')}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Application ID:** `{app.get('_id')}`")
                st.markdown(f"**School:** {app.get('school')}")
                st.markdown(f"**Class:** {app.get('class_applying')}")
            with c2:
                st.markdown(f"**Status:** {app.get('status')}")
                st.markdown(f"**Score:** {app.get('score', 'N/A')}/100")
                st.markdown(f"**Applied:** {str(app.get('created_at', ''))[:10]}")
            with c3:
                st.markdown(f"**Phone:** {app.get('phone')}")
                st.markdown(f"**Email:** {app.get('email')}")
