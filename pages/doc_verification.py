"""Admin — Document Verification: fetch by Application ID + AI check"""
import streamlit as st
import base64, os, io
import pandas as pd
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
from services.groq_ai import validate_document, parse_document, _get_api_key
from utils.data_store import find_all, find_by, update_by_id

load_dotenv()
client = Groq(api_key=_get_api_key())

DOC_TYPES = {
    "birth_certificate":    "🟡 Birth Certificate",
    "marksheet":            "📊 Marksheet",
    "aadhar":               "🪪 Aadhar Card",
    "transfer_certificate": "📋 Transfer Certificate",
    "residence_proof":      "🏠 Residence Proof",
}

def read_image_with_groq(image_bytes: bytes, doc_type: str) -> str:
    from services.groq_ai import _get_api_key
    fresh_client = Groq(api_key=_get_api_key())
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = fresh_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role":"user","content":[
            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
            {"type":"text","text":f"Extract ALL text from this {doc_type.replace('_',' ')} document. Return raw text only."}
        ]}],
        max_tokens=1200,
    )
    return resp.choices[0].message.content

def show():
    st.title("✅ Document Verification")
    st.caption("Fetch by Application ID · Upload document image · AI authenticity check")

    tab_fetch, tab_manual = st.tabs(["🔍 Verify by Application ID", "📋 Manual Verification"])

    # ── TAB 1: Fetch by Application ID ───────────────────────────────────────
    with tab_fetch:
        st.subheader("Fetch Application & Verify Documents")

        col_search, col_btn = st.columns([3, 1])
        with col_search:
            app_id_input = st.text_input(
                "Enter Application ID",
                placeholder="e.g. abc12345",
                label_visibility="collapsed"
            )
        with col_btn:
            fetch_clicked = st.button("🔍 Fetch Application", use_container_width=True)

        # Also show a dropdown of all pending applications for convenience
        with st.expander("Or pick from pending applications"):
            all_apps = find_all("applications")
            pending  = [a for a in all_apps if a.get("status") in ["Pending","Under Review"]]
            if pending:
                labels  = {a["_id"]: f"{a['_id']} — {a.get('student_name','')} ({a.get('class_applying','')} @ {a.get('school','')})"
                           for a in pending}
                picked  = st.selectbox("Select Application", [""] + list(labels.keys()),
                                       format_func=lambda x: labels.get(x, "— Select —") if x else "— Select —")
                if picked and st.button("Use this Application ID"):
                    st.session_state["verify_app_id"] = picked
                    st.rerun()

        # Trigger fetch
        if fetch_clicked and app_id_input.strip():
            st.session_state["verify_app_id"] = app_id_input.strip()

        # Show application details
        verify_id = st.session_state.get("verify_app_id","")
        if not verify_id:
            st.info("Enter an Application ID above to begin verification.")
        else:
            matches = [a for a in find_all("applications") if a.get("_id") == verify_id]
            if not matches:
                st.error(f"No application found with ID: `{verify_id}`")
            else:
                app = matches[0]
                st.markdown("---")
                st.markdown(f"### 📋 Application: `{verify_id}`")

                # Display application details in a clean grid
                info_cols = st.columns(3)
                fields = [
                    ("Student Name",  app.get("student_name","")),
                    ("DOB",           app.get("dob","")),
                    ("Gender",        app.get("gender","")),
                    ("Class",         app.get("class_applying","")),
                    ("School",        app.get("school","")),
                    ("Father",        app.get("father_name","")),
                    ("Mother",        app.get("mother_name","")),
                    ("Phone",         app.get("father_phone", app.get("phone",""))),
                    ("Email",         app.get("email","")),
                    ("Aadhar",        app.get("aadhar_number","")),
                    ("Address",       app.get("address","")),
                    ("Prev School",   app.get("prev_school","")),
                    ("Percentage",    str(app.get("percentage",""))),
                    ("TC Number",     app.get("tc_number","")),
                    ("Status",        app.get("status","")),
                    ("Score",         str(app.get("score",""))),
                    ("EWS",           "Yes" if app.get("is_ews") else "No"),
                    ("Sibling",       "Yes" if app.get("has_sibling") else "No"),
                ]
                for i, (label, val) in enumerate(fields):
                    with info_cols[i % 3]:
                        st.markdown(f"**{label}:** {val or '—'}")

                # Check what docs are required for this class
                class_applying = app.get("class_applying","")
                try:
                    import json
                    config_path = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")
                    with open(config_path) as f:
                        cfg = json.load(f)
                    req_docs = cfg.get("required_docs", {}).get(class_applying, ["birth_certificate","aadhar"])
                except Exception:
                    req_docs = ["birth_certificate","aadhar"]

                st.markdown("---")
                st.markdown(f"**Required docs for {class_applying}:** {', '.join(req_docs)}")

                # Existing verifications
                existing_verif = app.get("verifications", {})
                if existing_verif:
                    st.markdown("**Previously verified:**")
                    v_rows = [{"Document": DOC_TYPES.get(dt,dt),
                               "Score": f"{v.get('confidence_score',0)}/100",
                               "Decision": v.get("recommendation","—"),
                               "Date": v.get("verified_at","—")}
                              for dt, v in existing_verif.items()]
                    st.dataframe(pd.DataFrame(v_rows), use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("### 📤 Upload & Verify a Document for this Application")

                vc1, vc2 = st.columns(2)
                with vc1:
                    doc_type = st.selectbox("Document Type",
                        [d for d in DOC_TYPES.keys()],
                        format_func=lambda x: DOC_TYPES[x],
                        key="verify_doc_type")
                with vc2:
                    upload_method = st.radio("Input method",
                        ["Upload Image/PDF", "Paste Text"],
                        horizontal=True, key="verify_method")

                doc_text = ""
                if upload_method == "Upload Image/PDF":
                    up_file = st.file_uploader("Upload document", type=["jpg","jpeg","png","pdf"],
                                                key="verify_upload")
                    if up_file:
                        if up_file.type != "application/pdf":
                            st.image(Image.open(up_file), width=300)
                            up_file.seek(0)
                        if st.button("👁️ Read with AI Vision", key="verify_read"):
                            with st.spinner("Reading..."):
                                up_file.seek(0)
                                img_bytes = up_file.read()
                                if up_file.type == "application/pdf":
                                    try:
                                        import fitz
                                        fdoc = fitz.open(stream=img_bytes, filetype="pdf")
                                        img_bytes = fdoc.load_page(0).get_pixmap(dpi=200).tobytes("jpeg")
                                    except Exception:
                                        pass
                                try:
                                    doc_text = read_image_with_groq(img_bytes, doc_type)
                                    st.session_state["verify_doc_text"] = doc_text
                                    st.success("Text extracted!")
                                except Exception as e:
                                    st.error(f"Vision error: {e}")

                    raw = st.text_area("Extracted text (editable)",
                        value=st.session_state.get("verify_doc_text",""),
                        height=150, key="verify_text_area")
                    doc_text = raw
                else:
                    doc_text = st.text_area("Paste document text here", height=180,
                                             placeholder="Paste OCR text...", key="verify_paste")

                if st.button("🔍 Verify Document with AI", type="primary",
                             use_container_width=True, key="verify_run"):
                    if not doc_text.strip():
                        st.warning("Please upload or paste document text first.")
                    else:
                        with st.spinner("AI is analyzing..."):
                            result     = validate_document(doc_text, doc_type, class_applying)
                            parsed_doc = parse_document(doc_text, doc_type)

                        score = result.get("confidence_score", 0)
                        rec   = result.get("recommendation","manual_review")
                        is_v  = result.get("is_valid", False)

                        if rec == "accept" and is_v:
                            st.success(f"✅ ACCEPTED — Confidence: {score}/100")
                        elif rec == "reject":
                            st.error(f"❌ REJECTED — Confidence: {score}/100")
                        else:
                            st.warning(f"⚠️ MANUAL REVIEW — Confidence: {score}/100")

                        st.progress(score / 100)

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Issues:**")
                            for iss in result.get("issues",[]): st.error(f"• {iss}")
                            if not result.get("issues"): st.success("None found")
                        with c2:
                            st.markdown("**Missing Fields:**")
                            for mf in result.get("missing_fields",[]): st.warning(f"• {mf}")
                            if not result.get("missing_fields"): st.success("All present")

                        # Show extracted fields from this document
                        if "error" not in parsed_doc:
                            st.markdown("**Extracted Fields from Document:**")
                            ex_cols = st.columns(2)
                            items = list(parsed_doc.items())
                            for i, (k,v) in enumerate(items):
                                with ex_cols[i % 2]:
                                    st.markdown(f"**{k.replace('_',' ').title()}:** {v or '—'}")

                        # Save verification result to application record
                        from datetime import datetime
                        existing_verif = app.get("verifications", {})
                        existing_verif[doc_type] = {
                            **result,
                            "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }
                        update_by_id("applications", verify_id, {"verifications": existing_verif})
                        st.success("✅ Verification result saved to application record.")



    # ── TAB 2: Manual Verification ────────────────────────────────────────────
    with tab_manual:
        st.subheader("Quick Manual Document Check")
        st.caption("Verify a document without linking to an application ID")

        mc1, mc2 = st.columns(2)
        with mc1:
            m_doc_type      = st.selectbox("Document Type", list(DOC_TYPES.keys()),
                                            format_func=lambda x: DOC_TYPES[x], key="m_dtype")
            m_class         = st.selectbox("Class Applying", ["LKG","UKG","Class 1","Class 6","Class 9","Class 11"],
                                            key="m_class")
        with mc2:
            m_applicant     = st.text_input("Applicant Name (reference)", key="m_name")

        m_text = st.text_area("Paste document text", height=180,
                              placeholder="Paste OCR text here...", key="m_text")

        if st.button("🔍 Verify with AI", type="primary", key="m_verify"):
            if not m_text.strip():
                st.warning("Please paste document text.")
                return
            with st.spinner("Analyzing..."):
                res = validate_document(m_text, m_doc_type, m_class)

            score = res.get("confidence_score", 0)
            rec   = res.get("recommendation","manual_review")
            badge = {"accept":"✅ ACCEPTED","reject":"❌ REJECTED","manual_review":"⚠️ REVIEW"}
            fn    = {st.success: "accept", st.error: "reject", st.warning: "manual_review"}
            for fn_call, val in fn.items():
                if rec == val:
                    fn_call(f"{badge[val]} — Confidence: {score}/100")

            st.progress(score/100)
            ca, cb = st.columns(2)
            with ca:
                st.markdown("**Issues:**")
                for i in res.get("issues",[]): st.error(f"• {i}")
                if not res.get("issues"): st.success("None")
            with cb:
                st.markdown("**Missing:**")
                for m in res.get("missing_fields",[]): st.warning(f"• {m}")
                if not res.get("missing_fields"): st.success("All present")


