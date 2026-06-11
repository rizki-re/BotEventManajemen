"""
fsm.py — Data event, konstanta, struktur FSM, dan Metadata State
"""
from dataclasses import dataclass, field
from enum import Enum

# ──────────────────────────────────────────────
#  KONSTANTA APLIKASI & DATA (Dari data.py)
# ──────────────────────────────────────────────
APP_NAME = "EventBot"
APP_TAGLINE = "Platform Manajemen Event & Konferensi"
APP_VERSION = "1.0.0"

STATS = [
    {"num": "12+",  "label": "Event Tersedia"},
    {"num": "3.2K+","label": "Pendaftar"},
    {"num": "6",    "label": "Kategori"},
    {"num": "24/7", "label": "Tersedia"},
]

FEATURES = [
    {
        "icon": "📋", "color": "purple",
        "title": "Jelajahi Event",
        "desc": "Temukan seminar, workshop, dan konferensi berdasarkan kategori, tanggal, "
                "atau kata kunci. Informasi lengkap tersedia langsung di chat.",
    },
    {
        "icon": "✍️", "color": "pink",
        "title": "Pendaftaran Mudah",
        "desc": "Isi formulir pendaftaran melalui percakapan natural. Tidak perlu navigasi "
                "halaman yang rumit — cukup jawab pertanyaan bot.",
    },
    {
        "icon": "🎫", "color": "cyan",
        "title": "Kode Registrasi Unik",
        "desc": "Dapatkan kode pendaftaran unik setelah konfirmasi. Gunakan kode ini untuk "
                "check-in di hari pelaksanaan event.",
    },
    {
        "icon": "🔍", "color": "green",
        "title": "Cek Status Kapan Saja",
        "desc": "Masukkan kode registrasi untuk melihat status pendaftaran dan detail event "
                "secara real-time.",
    },
    {
        "icon": "❌", "color": "amber",
        "title": "Pembatalan & Reschedule",
        "desc": "Batalkan pendaftaran atau ajukan reschedule ke event lain dengan alur "
                "percakapan yang jelas dan terkonfirmasi.",
    },
    {
        "icon": "🤖", "color": "red",
        "title": "Mesin FSA Terstruktur",
        "desc": "Chatbot ditenagai Finite State Automata sehingga setiap percakapan "
                "mengikuti alur logika yang terstruktur dan tidak ambigu.",
    },
]

STEPS = [
    {"num": "01", "icon": "🌐", "label": "Buka Website",       "desc": "Akses EventBot melalui browser kapan saja dan di mana saja."},
    {"num": "02", "icon": "💬", "label": "Pilih Menu Chatbot", "desc": "Ketik atau klik pilihan menu yang tersedia di chatbot."},
    {"num": "03", "icon": "📋", "label": "Daftar Event",       "desc": "Pilih event dan isi data pendaftaran melalui percakapan."},
    {"num": "04", "icon": "🎫", "label": "Dapatkan Kode",      "desc": "Terima kode registrasi unik sebagai bukti pendaftaran resmi."},
    {"num": "05", "icon": "🔍", "label": "Cek Status",         "desc": "Periksa status kapan saja menggunakan kode registrasi Anda."},
]

FAQ = [
    {
        "q": "Bagaimana cara mendaftar ke sebuah event?",
        "a": "Ketik 'daftar' atau 'lihat event' di chatbot, pilih event yang diminati, "
             "lalu ikuti panduan pengisian data. Anda akan mendapatkan kode registrasi unik di akhir proses.",
    },
    {
        "q": "Bisakah saya membatalkan pendaftaran?",
        "a": "Ya, ketik 'batal' atau 'batalkan pendaftaran' di chatbot, masukkan kode registrasi "
             "Anda, dan konfirmasi pembatalan. Pembatalan gratis hingga H-3 sebelum pelaksanaan event.",
    },
    {
        "q": "Bagaimana cara cek status pendaftaran?",
        "a": "Ketik 'cek status' di chatbot, kemudian masukkan kode registrasi yang Anda terima "
             "saat mendaftar. Sistem akan menampilkan status terkini pendaftaran Anda.",
    },
    {
        "q": "Apakah ada biaya pendaftaran?",
        "a": "Tergantung event. Beberapa event bersifat gratis (FREE), sedangkan event berbayar "
             "akan menampilkan harga tiket. Lihat badge di kartu event untuk informasi biaya.",
    },
]

DEFAULT_EVENTS: list[dict] = [
    {
        "id": "EVT001", "emoji": "🧠",
        "title": "Seminar Nasional AI & Machine Learning 2025",
        "category": "Teknologi", "date": "15 Juli 2025", "time": "09.00–17.00 WIB",
        "location": "Jakarta Convention Center", "type": "Offline",
        "price": 150_000, "quota": 200, "registered": 178, "free": False,
        "desc": "Eksplorasi tren terbaru AI dan ML dari para ahli terkemuka.",
        "color": "linear-gradient(135deg,#1a0533,#2d1b5e)",
    },
    {
        "id": "EVT002", "emoji": "💼",
        "title": "Workshop Digital Marketing untuk UMKM",
        "category": "Bisnis", "date": "22 Juli 2025", "time": "08.00–16.00 WIB",
        "location": "Zoom Online", "type": "Online",
        "price": 0, "quota": 100, "registered": 87, "free": True,
        "desc": "Strategi pemasaran digital praktis untuk pelaku usaha mikro.",
        "color": "linear-gradient(135deg,#0c1a4d,#1a3a6b)",
    },
    {
        "id": "EVT003", "emoji": "🎨",
        "title": "Konferensi UX/UI Design Indonesia",
        "category": "Desain", "date": "1 Agustus 2025", "time": "09.00–18.00 WIB",
        "location": "Bandung Tech Hub", "type": "Offline",
        "price": 250_000, "quota": 150, "registered": 150, "free": False,
        "desc": "Tren desain terkini dan studi kasus dari praktisi top Indonesia.",
        "color": "linear-gradient(135deg,#2d0a3a,#5c1a6b)",
    },
    {
        "id": "EVT004", "emoji": "🌐",
        "title": "Forum Wirausaha Muda 2025",
        "category": "Kewirausahaan", "date": "10 Agustus 2025", "time": "08.30–15.30 WIB",
        "location": "Surabaya Expo Center", "type": "Hybrid",
        "price": 75_000, "quota": 300, "registered": 213, "free": False,
        "desc": "Networking dan inspirasi untuk entrepreneur muda Indonesia.",
        "color": "linear-gradient(135deg,#0a2d1a,#1a5c3a)",
    },
    {
        "id": "EVT005", "emoji": "🔬",
        "title": "Webinar Riset & Publikasi Ilmiah",
        "category": "Akademik", "date": "18 Agustus 2025", "time": "13.00–16.00 WIB",
        "location": "Zoom Online", "type": "Online",
        "price": 0, "quota": 500, "registered": 342, "free": True,
        "desc": "Panduan lengkap publikasi di jurnal internasional bereputasi.",
        "color": "linear-gradient(135deg,#0a2040,#0a3060)",
    },
    {
        "id": "EVT006", "emoji": "🏥",
        "title": "Konferensi Kesehatan Digital 2025",
        "category": "Kesehatan", "date": "25 Agustus 2025", "time": "09.00–17.00 WIB",
        "location": "RSCM Jakarta", "type": "Offline",
        "price": 200_000, "quota": 120, "registered": 95, "free": False,
        "desc": "Inovasi teknologi dalam pelayanan kesehatan modern Indonesia.",
        "color": "linear-gradient(135deg,#1a0a0a,#4d1a1a)",
    },
]

def get_event_by_id(events: list[dict], event_id: str) -> dict | None:
    return next((e for e in events if e["id"] == event_id), None)

def get_event_by_index(events: list[dict], idx: int) -> dict | None:
    try: return events[idx - 1]
    except IndexError: return None

def format_price(price: int) -> str:
    return "GRATIS" if price == 0 else f"Rp {price:,.0f}".replace(",", ".")

def quota_pct(event: dict) -> int:
    return round((event["registered"] / event["quota"]) * 100) if event["quota"] else 0

def is_full(event: dict) -> bool:
    return event["registered"] >= event["quota"]

# ──────────────────────────────────────────────
#  FSM STATES & DATA CLASS (Dari engine.py)
# ──────────────────────────────────────────────
class State(str, Enum):
    IDLE           = "IDLE"
    BROWSING       = "BROWSING"
    REGISTERING    = "REGISTERING"
    COLLECT_NAME   = "COLLECT_NAME"
    COLLECT_EMAIL  = "COLLECT_EMAIL"
    COLLECT_PHONE  = "COLLECT_PHONE"
    CONFIRMING     = "CONFIRMING"
    DONE           = "DONE"
    CHECK_STATUS   = "CHECK_STATUS"
    CANCELLING     = "CANCELLING"
    CANCEL_CONFIRM = "CANCEL_CONFIRM"

@dataclass
class FSM:
    state: State = State.IDLE
    selected_event: dict | None = None
    user_info: dict = field(default_factory=dict)
    registrations: dict = field(default_factory=dict)
    cancel_code: str = ""

STATE_META: dict[State, tuple[str, str]] = {
    State.IDLE:           ("⚪", "#888888"),
    State.BROWSING:       ("🔵", "#22d3ee"),
    State.REGISTERING:    ("🟣", "#a78bfa"),
    State.COLLECT_NAME:   ("🟣", "#a78bfa"),
    State.COLLECT_EMAIL:  ("🟣", "#a78bfa"),
    State.COLLECT_PHONE:  ("🟣", "#a78bfa"),
    State.CONFIRMING:     ("🟡", "#fbbf24"),
    State.DONE:           ("🟢", "#34d399"),
    State.CHECK_STATUS:   ("🔵", "#22d3ee"),
    State.CANCELLING:     ("🔴", "#f87171"),
    State.CANCEL_CONFIRM: ("🔴", "#f87171"),
}