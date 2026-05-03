"""Features 2, 3, 4 — Multi-doc OCR, Auto Form Fill (all fields), Doc Validation"""
import streamlit as st
import base64, os, io
import pandas as pd
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
from services.groq_ai import parse_document, validate_document, _get_api_key

load_dotenv()
client = Groq(api_key=_get_api_key())

DOC_TYPES = {
    "birth_certificate":    "🟡 Birth Certificate",
    "marksheet":            "📊 Marksheet",
    "aadhar":               "🪪 Aadhar Card",
    "transfer_certificate": "📋 Transfer Certificate",
    "residence_proof":      "🏠 Residence Proof",
}

def pdf_to_image_bytes(pdf_bytes: bytes):
    try:
        import fitz
        doc  = fitz.open(stream=pdf_bytes, filetype="pdf")
        pix  = doc.load_page(0).get_pixmap(dpi=200)
        return pix.tobytes("jpeg")
    except Exception:
        try:
            img = Image.open(io.BytesIO(pdf_bytes)).convert("RGB")
            buf = io.BytesIO(); img.save(buf, format="JPEG"); return buf.getvalue()
        except Exception:
            return None

def read_image_with_groq(image_bytes: bytes, doc_type: str) -> str:
    from services.groq_ai import _get_api_key
    fresh_client = Groq(api_key=_get_api_key())
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = fresh_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role":"user","content":[
            {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}},
            {"type":"text","text":f"""This is a {doc_type.replace('_',' ')} document from India.
Extract EVERY piece of visible text — every field, value, name, date, number, address, stamp text.
Return raw extracted text exactly as it appears. Do not summarize or skip anything."""}
        ]}],
        max_tokens=1500,
    )
    return resp.choices[0].message.content

def merge_all_docs(docs_data: dict) -> dict:
    merged = {}
    priority = ["birth_certificate","aadhar","marksheet","transfer_certificate","residence_proof"]
    for dtype in priority:
        d = docs_data.get(dtype, {})
        if not d: continue
        for src, dst in [("student_name","student_name"),("name","student_name"),
                         ("date_of_birth","dob"),("dob","dob"),
                         ("gender","gender"),("father_name","father_name"),
                         ("mother_name","mother_name"),("address","address"),
                         ("aadhar_number","aadhar_number"),("percentage","percentage"),
                         ("grade","grade"),("school_name","prev_school"),
                         ("class","prev_class"),("tc_number","tc_number"),
                         ("leaving_date","leaving_date")]:
            if d.get(src) and not merged.get(dst):
                merged[dst] = d[src]
    return merged

def show():
    st.title("📤 Upload & Verify Documents")
    st.caption("Multi-document · PDF + Image · AI Vision OCR · Auto form fill · Validation")

    tab_upload, tab_results = st.tabs(["📤 Upload Documents", "✅ Validation Results"])

    with tab_upload:
        st.markdown("### Step 1 — Upload Documents")
        st.info("Upload multiple documents at once. Supported formats: **JPG, PNG, PDF**")

        uploaded_files = st.file_uploader(
            "Select files (hold Ctrl/Cmd to select multiple)",
            type=["png","jpg","jpeg","pdf"],
            accept_multiple_files=True,
        )

        class_applying = st.selectbox("Applying for Class", [
            "LKG","UKG","Class 1","Class 2","Class 3","Class 4","Class 5",
            "Class 6","Class 7","Class 8","Class 9","Class 10","Class 11","Class 12"
        ])

        if not uploaded_files:
            st.markdown("---")
            st.caption("No files uploaded yet. Upload above to begin.")
            return

        # Preview
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        cols = st.columns(min(len(uploaded_files), 3))
        for i, uf in enumerate(uploaded_files):
            with cols[i % 3]:
                if uf.type == "application/pdf":
                    st.markdown(f"📄 **{uf.name}**")
                    st.caption("PDF")
                else:
                    try:
                        st.image(Image.open(uf), caption=uf.name, use_container_width=True)
                    except Exception:
                        st.markdown(f"🖼️ {uf.name}")
                uf.seek(0)

        # Type assignment
        st.markdown("---")
        st.markdown("### Step 2 — Assign Document Types")
        doc_assignments = {}
        for uf in uploaded_files:
            c1, c2 = st.columns([2,2])
            c1.markdown(f"**{uf.name}**")
            with c2:
                doc_assignments[uf.name] = st.selectbox(
                    "Type", list(DOC_TYPES.keys()),
                    format_func=lambda x: DOC_TYPES[x],
                    key=f"dt_{uf.name}"
                )

        # Process button
        st.markdown("---")
        st.markdown("### Step 3 — Process with AI")
        if st.button("👁️ Read All Documents with AI Vision", type="primary", use_container_width=True):
            all_parsed    = {}
            all_validated = {}
            all_extracted = {}
            prog   = st.progress(0)
            status = st.empty()

            for idx, uf in enumerate(uploaded_files):
                dtype = doc_assignments[uf.name]
                status.text(f"Reading {uf.name} ({idx+1}/{len(uploaded_files)})...")
                uf.seek(0)
                raw_bytes = uf.read()

                if uf.type == "application/pdf":
                    img_bytes = pdf_to_image_bytes(raw_bytes)
                    if img_bytes is None:
                        st.warning(f"Could not convert {uf.name}. Please convert to JPG manually.")
                        prog.progress((idx+1)/len(uploaded_files))
                        continue
                else:
                    img_bytes = raw_bytes

                try:
                    raw_text = read_image_with_groq(img_bytes, dtype)
                    all_extracted[uf.name] = {"text": raw_text, "type": dtype}
                    all_parsed[dtype]      = parse_document(raw_text, dtype)
                    all_validated[dtype]   = {"filename": uf.name,
                                              **validate_document(raw_text, dtype, class_applying)}
                except Exception as e:
                    st.error(f"Error on {uf.name}: {e}")
                prog.progress((idx+1)/len(uploaded_files))

            status.text("✅ All documents processed!")
            merged = merge_all_docs(all_parsed)
            st.session_state.update({
                "all_parsed": all_parsed,
                "all_validated": all_validated,
                "all_extracted": all_extracted,
                "parsed_doc": merged,
                "validation_result": list(all_validated.values())[0] if all_validated else {},
            })
            st.success(f"✅ {len(all_parsed)} document(s) processed and merged!")
            st.rerun()

        # Show extracted results
        if st.session_state.get("all_parsed"):
            st.markdown("---")
            st.markdown("### 📋 Extracted Fields Per Document")
            for dtype, parsed in st.session_state["all_parsed"].items():
                with st.expander(f"{DOC_TYPES.get(dtype, dtype)}", expanded=True):
                    if "error" not in parsed:
                        for k, v in parsed.items():
                            if isinstance(v, list):
                                st.markdown(f"**{k.replace('_',' ').title()}:**")
                                try: st.dataframe(v, use_container_width=True)
                                except: st.write(v)
                            else:
                                a, b = st.columns([1,2])
                                a.markdown(f"**{k.replace('_',' ').title()}**")
                                b.text(v or "—")
                    else:
                        st.error(str(parsed.get("raw","Parse failed"))[:300])

            st.markdown("---")
            st.markdown("### 🔗 Merged Auto-Fill Data (sent to Apply Now)")
            merged = st.session_state.get("parsed_doc", {})
            if merged:
                c1, c2 = st.columns(2)
                items = list(merged.items())
                mid   = max(1, len(items)//2)
                for col, chunk in [(c1, items[:mid]), (c2, items[mid:])]:
                    with col:
                        for k, v in chunk:
                            st.markdown(f"**{k.replace('_',' ').title()}:** {v or '—'}")
                st.success("💡 Go to **Apply Now** → click 'Auto-fill from uploaded documents'")

    # TAB 2 — Validation
    with tab_results:
        all_validated = st.session_state.get("all_validated", {})
        if not all_validated:
            st.info("⬅️ Process documents in the Upload tab first.")
            return

        rows = [{"Document": DOC_TYPES.get(dt, dt), "File": v.get("filename",""),
                 "Valid": "✅ Yes" if v.get("is_valid") else "❌ No",
                 "Score": f"{v.get('confidence_score',0)}/100",
                 "Decision": {"accept":"✅ Accept","reject":"❌ Reject",
                              "manual_review":"⚠️ Review"}.get(v.get("recommendation",""),"—")}
                for dt, v in all_validated.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.markdown("---")

        for dtype, v in all_validated.items():
            score = v.get("confidence_score", 0)
            with st.expander(f"{DOC_TYPES.get(dtype,dtype)} — {score}/100", expanded=True):
                c1,c2,c3 = st.columns(3)
                c1.metric("Valid",      "✅ YES" if v.get("is_valid") else "❌ NO")
                c2.metric("Confidence", f"{score}/100")
                c3.metric("Decision",   {"accept":"✅ Accept","reject":"❌ Reject",
                                          "manual_review":"⚠️ Review"}.get(v.get("recommendation",""),"—"))
                st.progress(score/100)
                ca, cb = st.columns(2)
                with ca:
                    st.markdown("**Issues:**")
                    for i in v.get("issues",[]): st.error(f"• {i}")
                    if not v.get("issues"): st.success("None found")
                with cb:
                    st.markdown("**Missing Fields:**")
                    for m in v.get("missing_fields",[]): st.warning(f"• {m}")
                    if not v.get("missing_fields"): st.success("All present")
