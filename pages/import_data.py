"""
pages/import_data.py
Import student admission data from Excel file into the data store.
Supports the SBOA Google Form export format.
"""
import streamlit as st
import pandas as pd
import io, os, uuid
from datetime import datetime
from utils.data_store import insert, find_all

# ── Column mapping: Excel column → internal field name ───────────────────────
COL_MAP = {
    "Student's Name":                  "student_name",
    "Name of the Father / Guardian":   "father_name",
    "Email Address":                   "email",
    "Admission sought for the class":  "class_applying",
    "Father/Guardian's Mobile Number": "father_phone",
    "Mother's Mobile Number":          "mother_phone",
    "DOB":                             "dob",
    "Gender":                          "gender",
    "Address":                         "address",
    "Message":                         "message",
    "Counsellor Remarks":              "counsellor_remarks",
    "Next Follow-Up Date":             "next_followup",
    "Timestamp":                       "submitted_at",
}

# Class name normalisation
CLASS_NORM = {
    "PRE-KG": "Pre-KG", "PREKG": "Pre-KG",
    "LKG": "LKG", "UKG": "UKG",
    "STD I":   "Class 1",  "STD 1":  "Class 1",  "I":   "Class 1",
    "STD II":  "Class 2",  "STD 2":  "Class 2",  "II":  "Class 2",
    "STD III": "Class 3",  "STD 3":  "Class 3",  "III": "Class 3",
    "STD IV":  "Class 4",  "STD 4":  "Class 4",  "IV":  "Class 4",
    "STD V":   "Class 5",  "STD 5":  "Class 5",  "V":   "Class 5",
    "STD VI":  "Class 6",  "STD 6":  "Class 6",  "VI":  "Class 6",
    "STD VII": "Class 7",  "STD 7":  "Class 7",  "VII": "Class 7",
    "STD VIII":"Class 8",  "STD 8":  "Class 8",  "VIII":"Class 8",
    "STD IX":  "Class 9",  "STD 9":  "Class 9",  "IX":  "Class 9",
    "STD X":   "Class 10", "STD 10": "Class 10", "X":   "Class 10",
    "STD XI":  "Class 11", "STD 11": "Class 11", "XI":  "Class 11",
    "STD XII": "Class 12", "STD 12": "Class 12", "XII": "Class 12",
}

def normalise_class(val: str) -> str:
    if not val:
        return ""
    v = str(val).strip().upper()
    return CLASS_NORM.get(v, val.strip())

def normalise_phone(val) -> str:
    if pd.isna(val) or val == "" or val is None:
        return ""
    phone = str(val).strip().replace(".0", "").replace(" ", "").replace("-", "")
    if len(phone) >= 10:
        return phone[-10:]  # take last 10 digits
    return phone

def normalise_dob(val) -> str:
    if pd.isna(val) or val == "":
        return ""
    try:
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime("%d/%m/%Y")
        return str(val)[:10]
    except Exception:
        return str(val)

def normalise_date(val) -> str:
    if pd.isna(val) or val == "":
        return ""
    try:
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime("%d/%m/%Y")
        return str(val)
    except Exception:
        return ""

def row_to_application(row: pd.Series, school: str = "SBOA") -> dict:
    """Convert one Excel row to an application dict."""
    app = {}
    for excel_col, field in COL_MAP.items():
        val = row.get(excel_col, "")
        app[field] = "" if pd.isna(val) or val is None else val

    # Normalise fields
    app["class_applying"]  = normalise_class(app.get("class_applying", ""))
    app["father_phone"]    = normalise_phone(app.get("father_phone", ""))
    app["mother_phone"]    = normalise_phone(app.get("mother_phone", ""))
    app["phone"]           = app["father_phone"]
    app["dob"]             = normalise_dob(app.get("dob", ""))
    app["next_followup"]   = normalise_date(app.get("next_followup", ""))
    app["submitted_at"]    = normalise_date(app.get("submitted_at", ""))
    app["school"]          = school
    app["status"]          = "Pending"
    app["score"]           = 0
    app["source"]          = "excel_import"

    # Convert any remaining non-string values
    for k, v in app.items():
        if isinstance(v, float) and pd.isna(v):
            app[k] = ""
        elif not isinstance(v, (str, int, float, bool)) and v is not None:
            app[k] = str(v)

    return app

def show():
    st.title("📥 Import Student Data")
    st.caption("Import admission enquiries from Excel · Google Form export · Bulk upload")

    tab_import, tab_view = st.tabs(["📤 Import Excel", "📋 Imported Records"])

    # ── TAB 1: Import ─────────────────────────────────────────────────────────
    with tab_import:
        st.markdown("### Upload Excel File")
        st.info(
            "Supports the **SBOA Google Form export format** (13 columns: "
            "Timestamp, Student Name, Father, Email, Class, Father Phone, "
            "Mother Phone, DOB, Gender, Address, Message, Counsellor Remarks, Follow-up Date)"
        )

        uploaded = st.file_uploader(
            "Choose Excel file (.xlsx)",
            type=["xlsx", "xls"],
            help="Export your Google Form responses as Excel and upload here"
        )

        school = st.selectbox("Assign to School", [
            "SBOA Annanagar", "SBOA Mogappair", "SBOA Adyar", "SBOA Tambaram",
            "SBOA Porur", "SBOA Velachery", "SBOA Sholinganallur", "SBOA Chromepet",
            "SBOA Ambattur", "SBOA Avadi", "SBOA Poonamallee", "SBOA Perambur",
            "SBOA Kodambakkam"
        ])

        skip_duplicates = st.checkbox(
            "Skip duplicate entries (same name + phone already in system)",
            value=True
        )
        skip_remarks = st.multiselect(
            "Skip rows with these counsellor remarks",
            ["COPY", "TEST MAIL", "fake message", "NO RESPONSE", "Wrong enquiry"],
            default=["COPY", "TEST MAIL"]
        )

        if not uploaded:
            st.caption("No file uploaded yet.")
            return

        # Read Excel
        try:
            df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Could not read file: {e}")
            return

        st.success(f"✅ File read: **{len(df)} rows**, **{len(df.columns)} columns**")

        # Column validation
        expected = set(COL_MAP.keys())
        found    = set(df.columns)
        missing  = expected - found
        if missing:
            st.warning(f"⚠️ Some expected columns not found: {missing}")
            st.markdown("**Columns in your file:**")
            st.write(list(df.columns))

        # Preview
        with st.expander("👀 Preview first 5 rows"):
            st.dataframe(df.head(5), use_container_width=True)

        st.markdown("---")
        if st.button("🚀 Import All Records", type="primary", use_container_width=True):
            existing = find_all("applications")
            existing_keys = set()
            for a in existing:
                name  = a.get("student_name", "").lower().strip()
                phone = a.get("father_phone", "").strip()
                if name and phone:
                    existing_keys.add(f"{name}_{phone}")

            results = {"imported": 0, "skipped_dup": 0, "skipped_remark": 0,
                       "skipped_empty": 0, "errors": 0}
            imported_records = []

            prog = st.progress(0)
            status = st.empty()

            for idx, row in df.iterrows():
                status.text(f"Processing row {idx+1}/{len(df)}...")
                prog.progress((idx + 1) / len(df))

                # Skip rows with blocked remarks
                remark = str(row.get("Counsellor Remarks", "")).strip().upper()
                if any(skip.upper() in remark for skip in skip_remarks):
                    results["skipped_remark"] += 1
                    continue

                # Skip empty student names
                name = str(row.get("Student's Name", "")).strip()
                if not name or name.lower() in ["nan", "test", ""]:
                    results["skipped_empty"] += 1
                    continue

                # Convert row
                try:
                    app = row_to_application(row, school)
                except Exception as e:
                    results["errors"] += 1
                    continue

                # Check duplicate
                if skip_duplicates:
                    key = f"{app['student_name'].lower().strip()}_{app['father_phone']}"
                    if key in existing_keys:
                        results["skipped_dup"] += 1
                        continue
                    existing_keys.add(key)

                # Insert
                try:
                    app_id = insert("applications", app)
                    imported_records.append({**app, "_id": app_id})
                    results["imported"] += 1
                except Exception as e:
                    results["errors"] += 1

            prog.progress(1.0)
            status.text("✅ Import complete!")

            # Results summary
            st.markdown("---")
            st.markdown("### Import Results")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("✅ Imported",    results["imported"])
            c2.metric("⚠️ Duplicates",  results["skipped_dup"])
            c3.metric("🚫 Skipped",     results["skipped_remark"])
            c4.metric("📭 Empty Names", results["skipped_empty"])
            c5.metric("❌ Errors",      results["errors"])

            if imported_records:
                st.success(f"🎉 Successfully imported {results['imported']} records!")
                st.markdown("**Imported records preview:**")
                preview_df = pd.DataFrame(imported_records)[
                    ["_id","student_name","class_applying","father_phone","email","status"]
                ]
                preview_df.columns = ["App ID","Student","Class","Phone","Email","Status"]
                st.dataframe(preview_df, use_container_width=True)

                # Download imported as CSV
                csv = preview_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download imported records (CSV)",
                    csv, "imported_records.csv", "text/csv"
                )

    # ── TAB 2: View imported records ──────────────────────────────────────────
    with tab_view:
        st.markdown("### All Imported Records")
        all_apps = find_all("applications")
        imported = [a for a in all_apps if a.get("source") == "excel_import"]

        if not imported:
            st.info("No records imported yet. Use the Import Excel tab to upload data.")
            return

        st.metric("Total imported records", len(imported))

        df_view = pd.DataFrame(imported)
        show_cols = ["_id","student_name","class_applying","school",
                     "father_phone","email","status","counsellor_remarks"]
        show_cols = [c for c in show_cols if c in df_view.columns]

        # Filters
        c1, c2 = st.columns(2)
        with c1:
            class_f = st.selectbox("Filter by Class", ["All"] + sorted(df_view["class_applying"].unique().tolist()))
        with c2:
            status_f = st.selectbox("Filter by Status", ["All","Pending","Under Review","Approved","Rejected"])

        filtered = df_view.copy()
        if class_f != "All":
            filtered = filtered[filtered.class_applying == class_f]
        if status_f != "All":
            filtered = filtered[filtered.status == status_f]

        st.dataframe(filtered[show_cols], use_container_width=True, height=400)
        st.caption(f"Showing {len(filtered)} of {len(imported)} imported records")
