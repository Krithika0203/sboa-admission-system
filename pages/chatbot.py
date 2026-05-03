"""Feature 1 — AI Chatbot with dynamic language config + language shift testing"""
import streamlit as st
import json, os
from services.groq_ai import chatbot_reply

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

def get_languages():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            langs = cfg.get("chatbot_languages", ["English","Hindi","Tamil"])
            return langs if langs else ["English","Hindi","Tamil"]
        except Exception:
            pass
    return ["English","Hindi","Tamil"]

LANG_FLAGS = {
    "English":   "🇬🇧 English",
    "Hindi":     "🇮🇳 Hindi",
    "Tamil":     "🇮🇳 Tamil",
    "Telugu":    "🇮🇳 Telugu",
    "Kannada":   "🇮🇳 Kannada",
    "Malayalam": "🇮🇳 Malayalam",
}

QUICK_QUESTIONS = {
    "English": [
        "What are the fees for Class 1?",
        "What documents are required?",
        "When does admission open?",
        "Age limit for LKG?",
        "How many schools are there?",
        "Contact information?",
    ],
    "Hindi": [
        "Class 1 की फीस क्या है?",
        "कौन से दस्तावेज़ चाहिए?",
        "एडमिशन कब शुरू होता है?",
        "LKG के लिए आयु सीमा?",
        "कितने स्कूल हैं?",
        "संपर्क जानकारी?",
    ],
    "Tamil": [
        "Class 1 கட்டணம் என்ன?",
        "என்ன ஆவணங்கள் தேவை?",
        "சேர்க்கை எப்போது தொடங்கும்?",
        "LKG வயது வரம்பு என்ன?",
        "எத்தனை பள்ளிகள் உள்ளன?",
        "தொடர்பு தகவல்?",
    ],
    "Telugu": [
        "Class 1 ఫీజు ఎంత?",
        "ఏ పత్రాలు అవసరం?",
        "అడ్మిషన్ ఎప్పుడు ప్రారంభమవుతుంది?",
        "LKG వయో పరిమితి?",
    ],
    "Kannada": [
        "Class 1 ಶುಲ್ಕ ಎಷ್ಟು?",
        "ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
        "ಪ್ರವೇಶ ಯಾವಾಗ ಪ್ರಾರಂಭವಾಗುತ್ತದೆ?",
    ],
    "Malayalam": [
        "Class 1 ഫീസ് എത്ര?",
        "ഏതൊക്കെ രേഖകൾ വേണം?",
        "അഡ്മിഷൻ എപ്പോൾ തുടങ്ങും?",
    ],
}

def show():
    st.title("🤖 AI Admission Assistant")

    languages = get_languages()

    # ── Language selector + shift test ───────────────────────────────────────
    col_lang, col_test = st.columns([2, 1])
    with col_lang:
        language = st.selectbox(
            "Language / भाषा / மொழி",
            languages,
            format_func=lambda x: LANG_FLAGS.get(x, x)
        )
    with col_test:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        run_shift_test = st.button("🧪 Language Shift Test", help="Test chatbot in all active languages")

    # ── Language Shift Test ───────────────────────────────────────────────────
    if run_shift_test:
        st.markdown("---")
        st.subheader("🧪 Language Shift Test Results")
        st.caption("Sending the same question in all active languages to verify correct language response.")
        test_q = "What are the fees for Class 1 and what documents are needed?"

        for lang in languages:
            with st.expander(f"{LANG_FLAGS.get(lang, lang)}", expanded=True):
                with st.spinner(f"Testing {lang}..."):
                    try:
                        reply = chatbot_reply(test_q, [], lang)
                        st.success(f"✅ Response in {lang}:")
                        st.write(reply)
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")
        st.markdown("---")

    st.caption(f"Active languages: {' · '.join([LANG_FLAGS.get(l,l) for l in languages])} · Powered by Groq llama-3.3-70b")

    # ── Quick questions ───────────────────────────────────────────────────────
    quick_qs = QUICK_QUESTIONS.get(language, QUICK_QUESTIONS["English"])
    st.markdown("**Quick questions:**")
    q_cols = st.columns(3)
    for i, q in enumerate(quick_qs):
        with q_cols[i % 3]:
            if st.button(q, key=f"quick_{language}_{i}", use_container_width=True):
                st.session_state.setdefault("chat_history", [])
                st.session_state.chat_history.append({"role": "user", "content": q})
                with st.spinner("Thinking..."):
                    reply = chatbot_reply(q, st.session_state.chat_history[:-1], language)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

    st.markdown("---")

    # ── Chat history ──────────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        st.info(f"👋 Hello! Ask me anything about SBOA admissions in {LANG_FLAGS.get(language, language)}.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # ── Input ─────────────────────────────────────────────────────────────────
    placeholder_map = {
        "English":   "Ask about fees, eligibility, documents, dates...",
        "Hindi":     "फीस, पात्रता, दस्तावेज़ के बारे में पूछें...",
        "Tamil":     "கட்டணம், தகுதி, ஆவணங்கள் பற்றி கேளுங்கள்...",
        "Telugu":    "ఫీజు, అర్హత, పత్రాల గురించి అడగండి...",
        "Kannada":   "ಶುಲ್ಕ, ಅರ್ಹತೆ, ದಾಖಲೆಗಳ ಬಗ್ಗೆ ಕೇಳಿ...",
        "Malayalam": "ഫീസ്, യോഗ്യത, രേഖകൾ എന്നിവ ചോദിക്കൂ...",
    }
    user_input = st.chat_input(placeholder_map.get(language, "Ask a question..."))
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("🤖 Thinking..."):
            reply = chatbot_reply(user_input, st.session_state.chat_history[:-1], language)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    col1, col2 = st.columns(2)
    if st.session_state.chat_history:
        if col1.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
    col2.caption(f"💬 {len(st.session_state.get('chat_history',[]))} messages in this session")
