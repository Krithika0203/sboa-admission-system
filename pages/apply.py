"""Parent - Apply Now — full form with all fields + multi-doc auto-fill"""
import streamlit as st
import json, os
from utils.data_store import insert
from services.notifications import notify_on_submission

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

def load_class_dates():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("class_dates", {})
    return {}

def show():
    st.title("📝 Apply for Admission")
    st.caption("Fill the form below · AI auto-fill available after uploading documents")

    # ── Auto-fill banner ──────────────────────────────────────────────────────
    if st.session_state.get("parsed_doc"):
        parsed = st.session_state["parsed_doc"]
        num = len([v for v in parsed.values() if v])
        st.success(f"✅ {num} fields ready from uploaded documents.")
        c1, c2 = st.columns(2)
        if c1.button("✨ Auto-fill from uploaded documents", use_container_width=True):
            st.session_state["autofill"] = st.session_state["parsed_doc"].copy()
        if c2.button("🗑️ Clear auto-fill data", use_container_width=True):
            st.session_state.pop("parsed_doc", None)
            st.session_state.pop("autofill", None)

    af = st.session_state.get("autofill", {})

    # ── Class-wise admission dates info ──────────────────────────────────────
    class_dates = load_class_dates()

    # ── FORM ─────────────────────────────────────────────────────────────────
    with st.form("admission_form", clear_on_submit=False):

        # ── SECTION 1: Student Details ────────────────────────────────────────
        st.markdown("### 👤 Student Details")
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            student_name = st.text_input("Student Full Name *",
                value=af.get("student_name", ""))
        with r1c2:
            dob = st.text_input("Date of Birth (DD/MM/YYYY) *",
                value=af.get("dob", ""),
                placeholder="15/03/2019")
        with r1c3:
            gender_opts = ["", "Male", "Female", "Other"]
            af_gender   = af.get("gender", "")
            gender_idx  = gender_opts.index(af_gender) if af_gender in gender_opts else 0
            gender = st.selectbox("Gender *", gender_opts, index=gender_idx)

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            aadhar_number = st.text_input("Aadhar Number",
                value=af.get("aadhar_number", ""),
                placeholder="1234-5678-9012")
        with r2c2:
            blood_group = st.selectbox("Blood Group",
                ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        with r2c3:
            nationality = st.text_input("Nationality", value="Indian")

        r3c1, r3c2 = st.columns(2)
        with r3c1:
            religion = st.text_input("Religion", value="")
        with r3c2:
            caste = st.text_input("Caste / Community", value="")

        st.markdown("---")

        # ── SECTION 2: Admission Preference ──────────────────────────────────
        st.markdown("### 🏫 Admission Preference")
        r4c1, r4c2, r4c3 = st.columns(3)
        with r4c1:
            class_applying = st.selectbox("Class Applying For *", [
                "LKG","UKG","Class 1","Class 2","Class 3","Class 4","Class 5",
                "Class 6","Class 7","Class 8","Class 9","Class 10","Class 11","Class 12"
            ])
        with r4c2:
            school = st.selectbox("Preferred School *", [
                "SBOA Annanagar","SBOA Mogappair","SBOA Adyar","SBOA Tambaram",
                "SBOA Porur","SBOA Velachery","SBOA Sholinganallur","SBOA Chromepet",
                "SBOA Ambattur","SBOA Avadi","SBOA Poonamallee","SBOA Perambur","SBOA Kodambakkam"
            ])
        with r4c3:
            medium = st.selectbox("Medium of Instruction *", ["English", "Tamil"])

        r5c1, r5c2 = st.columns(2)
        with r5c1:
            distance_km = st.number_input("Distance from school (km) *", 0.1, 50.0, 5.0, 0.1)
        with r5c2:
            address = st.text_area("Residential Address *",
                value=af.get("address", ""), height=80)

        # Show class-specific admission date if configured
        if class_applying and class_dates.get(class_applying):
            cd = class_dates[class_applying]
            st.info(f"📅 **{class_applying} Admission Window:** Open: {cd.get('open','—')}  |  Close: {cd.get('close','—')}  |  Results: {cd.get('results','—')}")

        st.markdown("---")

        # ── SECTION 3: Parent / Guardian Details ─────────────────────────────
        st.markdown("### 👨‍👩‍👦 Parent / Guardian Details")
        r6c1, r6c2 = st.columns(2)
        with r6c1:
            father_name       = st.text_input("Father's Full Name *", value=af.get("father_name",""))
            father_occupation = st.text_input("Father's Occupation",  value="")
            father_phone      = st.text_input("Father's Mobile *",     value="", placeholder="9876543210")
        with r6c2:
            mother_name       = st.text_input("Mother's Full Name *",  value=af.get("mother_name",""))
            mother_occupation = st.text_input("Mother's Occupation",   value="")
            mother_phone      = st.text_input("Mother's Mobile",       value="")

        r7c1, r7c2 = st.columns(2)
        with r7c1:
            email          = st.text_input("Email Address *", placeholder="parent@email.com")
            annual_income  = st.text_input("Annual Family Income (₹)", value="")
        with r7c2:
            guardian_name  = st.text_input("Guardian Name (if different)", value="")
            guardian_phone = st.text_input("Guardian Mobile", value="")

        st.markdown("---")

        # ── SECTION 4: Previous Academic Details ─────────────────────────────
        st.markdown("### 📚 Previous Academic Details")
        r8c1, r8c2, r8c3 = st.columns(3)
        with r8c1:
            prev_school = st.text_input("Previous School Name",
                value=af.get("prev_school",""))
        with r8c2:
            prev_class = st.text_input("Class Last Studied",
                value=af.get("prev_class",""))
        with r8c3:
            percentage = st.number_input("Last Exam Percentage (0 if LKG/UKG)",
                0.0, 100.0, float(af.get("percentage", 0) or 0))

        r9c1, r9c2, r9c3 = st.columns(3)
        with r9c1:
            tc_number = st.text_input("Transfer Certificate Number",
                value=af.get("tc_number",""))
        with r9c2:
            leaving_date = st.text_input("Date of Leaving Previous School",
                value=af.get("leaving_date",""))
        with r9c3:
            grade = st.text_input("Grade / Rank", value=af.get("grade",""))

        st.markdown("---")

        # ── SECTION 5: Special Categories & Extras ───────────────────────────
        st.markdown("### 📋 Additional Information")
        r10c1, r10c2 = st.columns(2)
        with r10c1:
            has_sibling    = st.checkbox("Sibling studying in SBOA?")
            sibling_name   = st.text_input("Sibling Name (if yes)", "") if has_sibling else ""
            sibling_class  = st.text_input("Sibling Class", "") if has_sibling else ""
        with r10c2:
            is_ews         = st.checkbox("EWS / Economically Weaker Section")
            is_staff_child = st.checkbox("Staff ward / Child of SBOA employee")
            is_rte         = st.checkbox("RTE (Right to Education) Applicant")

        achievements = st.text_area(
            "Special Achievements (sports, arts, Olympiad, NCC etc.)",
            height=80, placeholder="e.g. State-level chess champion, CBSE merit rank...")

        medical_info = st.text_area(
            "Medical / Special Needs (if any)",
            height=80, placeholder="e.g. Hearing aid, wheelchair access needed...")

        declaration = st.checkbox(
            "✅ I declare that all information provided is true and correct to the best of my knowledge. *"
        )

        submitted = st.form_submit_button("🚀 Submit Application", type="primary", use_container_width=True)

    # ── On Submit ─────────────────────────────────────────────────────────────
    if submitted:
        errors = []
        if not student_name:    errors.append("Student Full Name")
        if not dob:             errors.append("Date of Birth")
        if not gender:          errors.append("Gender")
        if not father_name:     errors.append("Father's Name")
        if not mother_name:     errors.append("Mother's Name")
        if not father_phone:    errors.append("Father's Mobile")
        if not email:           errors.append("Email Address")
        if not address:         errors.append("Residential Address")
        if not declaration:     errors.append("Declaration checkbox")

        if errors:
            st.error(f"Please fill required fields: {', '.join(errors)}")
            return

        app_data = {
            # Student
            "student_name":   student_name,
            "dob":            dob,
            "gender":         gender,
            "aadhar_number":  aadhar_number,
            "blood_group":    blood_group,
            "nationality":    nationality,
            "religion":       religion,
            "caste":          caste,
            # Admission
            "class_applying": class_applying,
            "school":         school,
            "medium":         medium,
            "distance_km":    distance_km,
            "address":        address,
            # Parents
            "father_name":       father_name,
            "father_occupation": father_occupation,
            "father_phone":      father_phone,
            "mother_name":       mother_name,
            "mother_occupation": mother_occupation,
            "mother_phone":      mother_phone,
            "email":             email,
            "annual_income":     annual_income,
            "guardian_name":     guardian_name,
            "guardian_phone":    guardian_phone,
            # Academic
            "prev_school":   prev_school,
            "prev_class":    prev_class,
            "percentage":    percentage,
            "tc_number":     tc_number,
            "leaving_date":  leaving_date,
            "grade":         grade,
            # Categories
            "has_sibling":    has_sibling,
            "sibling_name":   sibling_name,
            "sibling_class":  sibling_class,
            "is_ews":         is_ews,
            "is_staff_child": is_staff_child,
            "is_rte":         is_rte,
            "achievements":   achievements,
            "medical_info":   medical_info,
            # System
            "status": "Pending",
            "score":  0,
            "phone":  father_phone,
        }

        app_id = insert("applications", app_data)

        # Send confirmation email to parent + copy to school admin
        with st.spinner("📨 Sending confirmation email..."):
            try:
                notif = notify_on_submission(app_data, app_id)
            except Exception as ex:
                notif = {"email": {"success": False, "error": str(ex)}}

        st.success(f"🎉 Application submitted! Your Application ID: **`{app_id}`**")
        st.info(f"📋 Save your Application ID **`{app_id}`** to track your application status.")

        # Email status
        email_result = notif.get("email", {})
        if email_result.get("success"):
            st.success(f"📧 Confirmation email sent to **{app_data.get('email','')}**")
        else:
            hint = email_result.get("hint", "")
            err  = email_result.get("error", "Unknown error")
            if hint:
                st.warning(f"📧 Email not sent — {hint}")
            else:
                st.warning(f"📧 Email not sent — {err}")

        st.balloons()
        st.session_state.pop("autofill", None)
