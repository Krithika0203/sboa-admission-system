"""Super Admin — Configure Admission Rules + Class-wise Dates"""
import streamlit as st
import json, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

ALL_CLASSES = ["LKG","UKG","Class 1","Class 2","Class 3","Class 4","Class 5",
               "Class 6","Class 7","Class 8","Class 9","Class 10","Class 11","Class 12"]

DEFAULT_CONFIG = {
    "admission_dates": {"open": "2025-01-15", "close": "2025-02-28", "results": "2025-03-15"},
    "class_dates": {
        "LKG":     {"open":"2025-01-15","close":"2025-02-10","results":"2025-02-20"},
        "UKG":     {"open":"2025-01-15","close":"2025-02-10","results":"2025-02-20"},
        "Class 1": {"open":"2025-01-15","close":"2025-02-15","results":"2025-02-25"},
        "Class 6": {"open":"2025-01-20","close":"2025-02-20","results":"2025-03-05"},
        "Class 9": {"open":"2025-01-20","close":"2025-02-25","results":"2025-03-10"},
        "Class 11":{"open":"2025-02-01","close":"2025-02-28","results":"2025-03-15"},
    },
    "scoring_weights": {"distance":30,"sibling":25,"marks":20,"ews":10,"staff_child":15},
    "seat_limits": {"LKG":40,"UKG":40,"Class 1":45,"Class 6":50,"Class 9":50,"Class 11":60},
    "required_docs": {
        "LKG":     ["birth_certificate","aadhar","photos"],
        "Class 1": ["birth_certificate","aadhar","photos"],
        "Class 6": ["birth_certificate","aadhar","marksheet","transfer_certificate","photos"],
        "Class 9": ["birth_certificate","aadhar","marksheet","transfer_certificate","photos"],
        "Class 11":["birth_certificate","aadhar","marksheet","transfer_certificate","photos"],
    },
    "chatbot_languages": ["English","Hindi","Tamil"],
    "duplicate_detection": {"enabled":True,"fuzzy_threshold":85},
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        # ensure class_dates key exists in older saved configs
        if "class_dates" not in cfg:
            cfg["class_dates"] = DEFAULT_CONFIG["class_dates"]
        return cfg
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def show():
    st.title("⚙️ Configure Admission Rules")
    st.caption("Super Admin · Changes apply to all 13 schools immediately")

    cfg = load_config()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Global Dates", "📆 Class-wise Dates", "🏆 Scoring", "🪑 Seats & Docs", "🤖 AI Settings"
    ])

    # ── TAB 1: Global Dates ───────────────────────────────────────────────────
    with tab1:
        st.subheader("Global Admission Date Window")
        st.caption("These are fallback dates for classes not configured in Class-wise Dates.")
        c1, c2, c3 = st.columns(3)
        with c1:
            cfg["admission_dates"]["open"]    = st.text_input("Open Date",    cfg["admission_dates"]["open"])
        with c2:
            cfg["admission_dates"]["close"]   = st.text_input("Close Date",   cfg["admission_dates"]["close"])
        with c3:
            cfg["admission_dates"]["results"] = st.text_input("Results Date", cfg["admission_dates"]["results"])

    # ── TAB 2: Class-wise Dates ───────────────────────────────────────────────
    with tab2:
        st.subheader("Class-wise Admission Dates")
        st.caption("Set different open/close/results dates for each class. These show on the Apply Now form when a parent selects that class.")

        if "class_dates" not in cfg:
            cfg["class_dates"] = DEFAULT_CONFIG["class_dates"].copy()

        # Group classes into rows of 2
        for i in range(0, len(ALL_CLASSES), 2):
            pair = ALL_CLASSES[i:i+2]
            cols = st.columns(2)
            for col, cls in zip(cols, pair):
                with col:
                    st.markdown(f"**{cls}**")
                    if cls not in cfg["class_dates"]:
                        cfg["class_dates"][cls] = {"open":"","close":"","results":""}
                    cd = cfg["class_dates"][cls]
                    cc1, cc2, cc3 = st.columns(3)
                    with cc1:
                        cd["open"]    = st.text_input("Open",    cd.get("open",""),    key=f"o_{cls}")
                    with cc2:
                        cd["close"]   = st.text_input("Close",   cd.get("close",""),   key=f"c_{cls}")
                    with cc3:
                        cd["results"] = st.text_input("Results", cd.get("results",""), key=f"r_{cls}")
                    cfg["class_dates"][cls] = cd

        st.markdown("---")
        st.markdown("**Preview — what parents will see on Apply Now:**")
        import pandas as pd
        preview_rows = []
        for cls in ALL_CLASSES:
            cd = cfg["class_dates"].get(cls, {})
            preview_rows.append({
                "Class":   cls,
                "Open":    cd.get("open","—"),
                "Close":   cd.get("close","—"),
                "Results": cd.get("results","—"),
            })
        st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    # ── TAB 3: Scoring ────────────────────────────────────────────────────────
    with tab3:
        st.subheader("Scoring Weights (must total ≤ 100)")
        w = cfg["scoring_weights"]
        c1, c2 = st.columns(2)
        with c1:
            w["distance"]    = st.slider("Distance weight",    0, 40, w["distance"])
            w["sibling"]     = st.slider("Sibling weight",     0, 40, w["sibling"])
            w["marks"]       = st.slider("Marks weight",       0, 30, w["marks"])
        with c2:
            w["ews"]         = st.slider("EWS weight",         0, 20, w["ews"])
            w["staff_child"] = st.slider("Staff child weight", 0, 20, w["staff_child"])
        total = sum(w.values())
        st.error(f"⚠️ Total = {total} — exceeds 100!") if total > 100 else st.success(f"✅ Total = {total}/100")

    # ── TAB 4: Seats & Docs ───────────────────────────────────────────────────
    with tab4:
        st.subheader("Seat Limits per Class")
        seats = cfg["seat_limits"]
        c1, c2 = st.columns(2)
        for i, cls in enumerate(seats):
            with (c1 if i % 2 == 0 else c2):
                seats[cls] = st.number_input(f"Seats — {cls}", 10, 200, seats[cls], 5)

        st.markdown("---")
        st.subheader("Required Documents per Class")
        st.caption("Edit in JSON format below:")
        req_docs_text = st.text_area(
            "Required docs (JSON)",
            value=json.dumps(cfg.get("required_docs", {}), indent=2),
            height=200
        )
        try:
            cfg["required_docs"] = json.loads(req_docs_text)
            st.success("✅ Valid JSON")
        except Exception:
            st.error("❌ Invalid JSON — fix before saving")

    # ── TAB 5: AI Settings ────────────────────────────────────────────────────
    with tab5:
        st.subheader("Chatbot Languages")
        cfg["chatbot_languages"] = st.multiselect(
            "Active languages",
            ["English","Hindi","Tamil","Telugu","Kannada","Malayalam"],
            default=cfg.get("chatbot_languages", ["English","Hindi","Tamil"])
        )
        st.markdown("---")
        st.subheader("Fraud Detection")
        dup = cfg.get("duplicate_detection", {})
        dup["enabled"]         = st.toggle("Enable fraud/duplicate detection", value=dup.get("enabled", True))
        dup["fuzzy_threshold"] = st.slider("Fuzzy match threshold (higher = stricter)", 70, 100, dup.get("fuzzy_threshold", 85))
        cfg["duplicate_detection"] = dup

    st.markdown("---")
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        save_config(cfg)
        st.success("✅ All settings saved! Changes are live across all 13 schools.")
        st.balloons()


