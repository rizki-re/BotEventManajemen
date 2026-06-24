"""
app.py — Entry point EventBot Streamlit
Jalankan: streamlit run app.py
"""
import copy
import streamlit as st
import os

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="EventBot — Platform Event & Konferensi",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded",
)

from fsm import (
    DEFAULT_EVENTS, STATS, FEATURES, STEPS, FAQ,
    format_price, quota_pct, is_full, State, FSM, STATE_META
)
from engine import fsm_step, keyword_fallback, MAIN_MENU_CHIPS

# ─────────────────────────────────────────────
#  SHARED UI HELPERS
# ─────────────────────────────────────────────
NAV_PAGES = [
    ("🏠", "Beranda", "home"),
    ("✨", "Fitur", "features"),
    ("📅", "Event", "events"),
    ("💬", "Chatbot", "chatbot"),
    ("❓", "FAQ", "faq"),
]

def navigate_to(page: str):
    """Set the active page and trigger a Streamlit rerun."""
    st.session_state.page = page
    st.rerun()

def section_header(tag: str, title: str, subtitle: str = ""):
    """Render a consistent section header block."""
    sub_html = f'<p class="section-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="section-tag">{tag}</div>'
        f'<h2 class="section-title">{title}</h2>{sub_html}',
        unsafe_allow_html=True,
    )

def render_grid_rows(items: list, cols_per_row: int, render_fn):
    """Lay out *items* in rows of *cols_per_row*, calling render_fn(item, col, index)."""
    for row_start in range(0, len(items), cols_per_row):
        row = items[row_start:row_start + cols_per_row]
        cols = st.columns(len(row))
        for col, (item, idx) in zip(cols, [(it, row_start + j) for j, it in enumerate(row)]):
            render_fn(item, col, idx)

# ─────────────────────────────────────────────
#  INJEKSI CSS & FONTS (Load dari file terpisah)
# ─────────────────────────────────────────────
GOOGLE_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
"""

def inject_styles():
    # Load Google Fonts
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    
    # Baca external CSS file
    css_file_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    try:
        with open(css_file_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ File CSS (assets/style.css) tidak ditemukan.")

# ─────────────────────────────────────────────
#  KOMPONEN UI (Dari components.py)
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.5rem">
              <div style="width:38px;height:38px;border-radius:10px;
                          background:linear-gradient(135deg,#7c5ce0,#a855f7);
                          display:flex;align-items:center;justify-content:center;font-size:1.1rem">🎪</div>
              <span style="font-family:'Syne',sans-serif;font-weight:700;
                           font-size:1.2rem;color:#f0ecfc">EventBot</span>
            </div>
            """, unsafe_allow_html=True
        )

        pages = NAV_PAGES
        current = st.session_state.get("page", "home")

        st.markdown("""
        <style>
        [data-testid="stSidebar"] .stButton > button { background: transparent !important; color: #b09cd4 !important; border: 1px solid transparent !important; border-radius: 10px !important; text-align: left !important; padding: 10px 14px !important; font-size: .9rem !important; box-shadow: none !important; transition: background .2s, color .2s !important; }
        [data-testid="stSidebar"] .stButton > button:hover { background: rgba(124,92,224,0.12) !important; color: #f0ecfc !important; border-color: rgba(124,92,224,0.25) !important; transform: none !important; }
        [data-testid="stSidebar"] div:has(> div > button[kind="secondary"]) button { background: rgba(124,92,224,0.2) !important; color: #f0ecfc !important; border-color: rgba(124,92,224,0.45) !important; }
        </style>
        """, unsafe_allow_html=True)

        for icon, label, key in pages:
            is_active = current == key
            if is_active:
                st.markdown(
                    f"""<div style="background:rgba(124,92,224,0.18);border:1px solid rgba(124,92,224,0.4);border-radius:10px;padding:10px 14px;margin-bottom:4px;cursor:default;display:flex;align-items:center;gap:8px;">
                        <span>{icon}</span><span style="font-size:.9rem;font-weight:600;color:#f0ecfc;">{label}</span>
                        <span style="margin-left:auto;width:6px;height:6px;border-radius:50%;background:#a78bfa;"></span>
                    </div>""", unsafe_allow_html=True)
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                    navigate_to(key)

        st.markdown("<hr style='border-color:#2d2050;margin:1.2rem 0'>", unsafe_allow_html=True)

        if current == "chatbot" and "fsm" in st.session_state:
            fsm = st.session_state.fsm
            if fsm.registrations:
                st.markdown("<p style='font-size:.72rem;color:#7460a8;margin-bottom:.5rem;'>🎫 PENDAFTARAN AKTIF</p>", unsafe_allow_html=True)
                for code, reg in fsm.registrations.items():
                    st.markdown(
                        f"<div style='background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:.75rem;'>"
                        f"<strong style='color:#34d399'>{code}</strong><br><span style='color:#b09cd4'>{reg['name']}</span><br>"
                        f"<span style='color:#7460a8'>{reg['event']['title'][:30]}...</span></div>", unsafe_allow_html=True)
            
            emoji, color = STATE_META.get(fsm.state, ("⚪", "#888"))
            st.markdown(
                f"<div style='background:rgba(36,26,61,.8);border:1px solid #2d2050;border-radius:8px;padding:8px 12px;margin-top:8px;'>"
                f"<span style='font-size:.68rem;color:#7460a8;'>FSM STATE</span><br>"
                f"<span style='font-size:.8rem;font-weight:600;color:{color};'>{emoji} {fsm.state.value}</span></div>", unsafe_allow_html=True)

        st.markdown("<p style='font-size:.68rem;color:#7460a8;text-align:center;margin-top:1rem'>Powered by FSM &amp; Kata Kunci</p>", unsafe_allow_html=True)

def render_topnav():
    pages = NAV_PAGES
    current = st.session_state.get("page", "home")
    cols = st.columns([1, 1, 1, 1, 1, 3])
    for col, (icon, label, key) in zip(cols, pages):
        with col:
            is_active = current == key
            css_class = "nav-active" if is_active else ""
            btn_label = f"{icon} {label}"
            if is_active:
                st.markdown(f'<div class="top-navbar"><span class="{css_class}" style="background:rgba(124,92,224,0.2);color:#f0ecfc;border:1px solid rgba(124,92,224,0.45);border-radius:8px;padding:7px 14px;font-size:.88rem;font-weight:600;display:inline-block;">{btn_label}</span></div>', unsafe_allow_html=True)
            else:
                if st.button(btn_label, key=f"topnav_{key}", use_container_width=True):
                    navigate_to(key)
    st.markdown("<hr style='border-color:#2d2050;margin:0 0 1rem 0'>", unsafe_allow_html=True)

def render_hero():
    st.markdown(
        """
        <div class="hero-section">
          <div class="hero-badge"><span class="badge-dot"></span>Platform Manajemen Event &amp; Konferensi Modern</div>
          <h1 class="hero-title">Event Management<br><span>Chatbot</span></h1>
          <p class="hero-sub">Kelola dan daftarkan diri ke berbagai seminar, workshop, dan konferensi dengan mudah melalui chatbot interaktif berbasis <strong style="color:#f0ecfc">Finite State Automata</strong> yang diperkuat <strong style="color:#f0ecfc">AI</strong>.</p>
        </div>
        """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🤖 Mulai Chat", key="hero_chat", use_container_width=True):
                navigate_to("chatbot")
        with col_b:
            if st.button("📅 Lihat Event", key="hero_event", use_container_width=True):
                navigate_to("events")

    cols = st.columns(len(STATS))
    for col, stat in zip(cols, STATS):
        with col:
            st.markdown(f'<div class="stat-item"><div class="stat-num">{stat["num"]}</div><div class="stat-label">{stat["label"]}</div></div>', unsafe_allow_html=True)

def _render_feature_card(feat: dict, col, _idx: int):
    COLOR_CLASS = {"purple":"fi-purple","pink":"fi-pink","cyan":"fi-cyan","green":"fi-green","amber":"fi-amber","red":"fi-red"}
    cc = COLOR_CLASS.get(feat["color"], "fi-purple")
    with col:
        st.markdown(f'<div class="feat-card"><div class="feat-icon {cc}">{feat["icon"]}</div><div class="feat-title">{feat["title"]}</div><p class="feat-desc">{feat["desc"]}</p></div>', unsafe_allow_html=True)

def render_features():
    section_header("Fitur Utama", "Semua yang Anda Butuhkan", "Ditenagai logika FSM + AI — percakapan terarah sekaligus cerdas dan natural.")
    render_grid_rows(FEATURES, 3, _render_feature_card)

def render_event_card(ev: dict, col, idx: int):
    pct = quota_pct(ev)
    full = is_full(ev)
    harga = format_price(ev["price"])
    badges = '<span class="badge badge-free">FREE</span>' if ev["free"] else '<span class="badge badge-paid">BERBAYAR</span>'
    if full: badges += '<span class="badge badge-full">PENUH</span>'
    badges += f'<span class="badge badge-cat">{ev["category"]}</span>'
    if ev["type"] == "Online": badges += '<span class="badge badge-online">Online</span>'

    with col:
        st.markdown(
            f'<div class="event-card"><div class="event-banner" style="background:{ev["color"]}"><span style="font-size:2.3rem">{ev["emoji"]}</span><span class="event-type-badge">{ev["type"]}</span></div>'
            f'<div class="event-body"><div class="event-badges">{badges}</div><div class="event-title">{ev["title"]}</div>'
            f'<div class="event-meta"><span>📅 {ev["date"]}</span><br><span>🕐 {ev["time"]}</span><br><span>📍 {ev["location"]}</span></div>'
            f'<div class="quota-bar"><div class="quota-fill" style="width:{pct}%"></div></div><div class="quota-txt">{ev["registered"]}/{ev["quota"]} peserta ({pct}%)</div></div>'
            f'<div class="event-footer"><span class="event-price">{harga}</span></div></div>', unsafe_allow_html=True)
        label = "❌ Event Penuh" if full else "✍️ Daftar Sekarang"
        if st.button(label, key=f"daftar_{ev['id']}", disabled=full, use_container_width=True):
            st.session_state.pending_event_idx = idx
            navigate_to("chatbot")

def render_events_grid(events: list[dict]):
    section_header("Daftar Event", "Event yang Tersedia", "Pilih event sesuai minat Anda. Daftar langsung via chatbot.")
    render_grid_rows(events, 3, lambda ev, col, idx: render_event_card(ev, col, idx + 1))

def _init_chat():
    if "fsm" not in st.session_state: st.session_state.fsm = FSM()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [("bot", "👋 Halo! Saya **EventBot**, asisten untuk manajemen event & konferensi.\n\nSaya bisa membantu Anda:\n- 📋 Cari dan lihat semua event tersedia\n- ✍️ Daftar ke event pilihan Anda\n- 🔍 Cek status pendaftaran\n- ❌ Batalkan pendaftaran\n- 💬 Tanya tentang harga, jadwal, lokasi, dan rekomendasi event!\n\nKetik apa saja atau klik tombol di bawah untuk mulai 😊")]
        st.session_state.chat_chips = MAIN_MENU_CHIPS

def _send(text: str):
    if not text.strip(): return
    fsm = st.session_state.fsm
    events = st.session_state.events
    history = st.session_state.chat_history
    history.append(("user", text))
    resp, chips, needs_fallback = fsm_step(fsm, text, events)
    if needs_fallback or not resp:
        resp = keyword_fallback(text, events)
    history.append(("bot", resp))
    st.session_state.chat_chips = chips

def render_chatbot_page():
    _init_chat()
    if "pending_event_idx" in st.session_state:
        idx = st.session_state.pop("pending_event_idx")
        if st.session_state.fsm.state == State.IDLE: _send("lihat event")
        _send(str(idx))

    left, right = st.columns([1, 1.6], gap="large")
    with left:
        section_header("Chatbot Interaktif", "Tanya Apa Saja!", "EventBot berbasis kata kunci — bisa menjawab pertanyaan seputar event, beri rekomendasi, dan bantu pendaftaran.")
        features_info = [("🔑", "Kata Kunci Pintar", "Ketik 'harga', 'jadwal', 'lokasi', atau 'rekomendasi' dan EventBot langsung menjawab!"), ("📋", "Lihat Semua Event", "Ketik 'lihat event' untuk daftar lengkap dengan detail harga dan kuota."), ("✍️", "Panduan Pendaftaran", "Bot memandu step-by-step: nama → email → HP → konfirmasi → kode registrasi."), ("🎫", "Kode Registrasi Instan", "Dapat kode EVT-XXXXX langsung setelah konfirmasi pendaftaran."), ("🔍", "Cek & Kelola Pendaftaran", "Cek status atau batalkan kapan saja menggunakan kode registrasi.")]
        for icon, title, desc in features_info:
            st.markdown(f'<div style="display:flex;align-items:flex-start;gap:12px;padding:12px 16px;margin-bottom:8px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius)"><div style="width:34px;height:34px;border-radius:9px;background:rgba(124,92,224,0.15);display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0">{icon}</div><div><div style="font-size:.85rem;font-weight:600;color:#f0ecfc;margin-bottom:2px">{title}</div><div style="font-size:.76rem;color:#b09cd4;line-height:1.45">{desc}</div></div></div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="chat-header"><div class="chat-avatar">🤖</div><div><div class="chat-name">EventBot</div><span class="online-dot">Online · Aktif</span></div></div>', unsafe_allow_html=True)
        chat_container = st.container(height=440, border=False)
        with chat_container:
            for role, text in st.session_state.chat_history:
                av = "🤖" if role == "bot" else "👤"
                with st.chat_message("assistant" if role == "bot" else "user", avatar=av): st.markdown(text)

        fsm = st.session_state.fsm
        emoji, color = STATE_META.get(fsm.state, ("⚪", "#888"))
        st.markdown(f'<div class="state-bar">FSM State:&nbsp;<span class="state-pill" style="background:rgba(128,128,128,.12);color:{color};">{emoji} {fsm.state.value}</span></div>', unsafe_allow_html=True)

        chips = st.session_state.get("chat_chips", [])
        if chips:
            visible_chips = chips[:5]
            cols = st.columns(len(visible_chips))
            for col, chip in zip(cols, visible_chips):
                with col:
                    if st.button(chip, key=f"chip_{chip}_{len(st.session_state.chat_history)}", use_container_width=True):
                        _send(chip)
                        st.rerun()

        if prompt := st.chat_input("Ketik apa saja..."):
            _send(prompt)
            st.rerun()

        if st.button("🔄 Reset Chat", key="btn_reset_chat"):
            for k in ("fsm", "chat_history", "chat_chips"):
                st.session_state.pop(k, None)
            st.rerun()

def render_how_it_works():
    st.markdown('<div style="text-align:center"><div class="section-tag" style="justify-content:center">Cara Penggunaan</div><h2 class="section-title">5 Langkah Mudah</h2><p class="section-sub" style="margin:0 auto 2rem">Ikuti langkah berikut untuk mulai menggunakan EventBot.</p></div>', unsafe_allow_html=True)
    cols = st.columns(len(STEPS))
    for col, step in zip(cols, STEPS):
        with col: st.markdown(f'<div class="step-item"><div class="step-num">{step["num"]}</div><div class="step-icon">{step["icon"]}</div><div class="step-label">{step["label"]}</div><div class="step-desc">{step["desc"]}</div></div>', unsafe_allow_html=True)

def render_faq():
    section_header("FAQ", "Pertanyaan Umum")
    for item in FAQ:
        with st.expander(item["q"]): st.markdown(f'<p style="font-size:.875rem;color:#b09cd4;line-height:1.6">{item["a"]}</p>', unsafe_allow_html=True)

def render_cta():
    st.markdown('<div class="cta-section"><p class="cta-title">Siap Mencoba EventBot?</p><p class="cta-sub">Mulai gunakan EventBot sekarang dan rasakan kemudahan mendaftar event favorit Anda.</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        if st.button("🚀 Mulai Sekarang", key="cta_btn", use_container_width=True):
            navigate_to("chatbot")

def render_footer():
    st.markdown('<div class="eb-footer"><p>© 2025 <strong>EventBot</strong> — Platform Manajemen Event &amp; Konferensi | Dibangun dengan ❤️ menggunakan FSM &amp; Kata Kunci</p><p style="margin-top:4px;font-size:.72rem">Sistem Chatbot FSM berbasis kata kunci untuk manajemen event dan konferensi</p></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ROUTING / ENTRY POINT
# ─────────────────────────────────────────────
inject_styles()

if "page" not in st.session_state:
    st.session_state.page = "home"
if "events" not in st.session_state:
    st.session_state.events = copy.deepcopy(DEFAULT_EVENTS)

render_sidebar()
render_topnav()

page = st.session_state.get("page", "home")

if page == "home":
    render_hero()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    with st.container(): render_features()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    with st.container(): render_events_grid(st.session_state.events)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    with st.container(): render_how_it_works()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    with st.container(): render_cta()
    render_footer()

elif page == "features":
    st.markdown("<br>", unsafe_allow_html=True)
    render_features()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    render_how_it_works()
    render_footer()

elif page == "events":
    st.markdown("<br>", unsafe_allow_html=True)
    render_events_grid(st.session_state.events)
    render_footer()

elif page == "chatbot":
    st.markdown("<br>", unsafe_allow_html=True)
    render_chatbot_page()
    render_footer()

elif page == "faq":
    st.markdown("<br>", unsafe_allow_html=True)
    render_faq()
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    render_cta()
    render_footer()

else:
    st.session_state.page = "home"
    st.rerun()