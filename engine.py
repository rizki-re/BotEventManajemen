"""
engine.py — NLP + FSM EventBot (upgraded)
"""
import re
import secrets
import string
from fsm import State, FSM, get_event_by_index, format_price, quota_pct, is_full

# ──────────────────────────────────────────────
#  NLP HELPERS (Dengan Kata Kunci Lebih Beragam)
# ──────────────────────────────────────────────
def _low(t: str) -> str: return t.lower().strip()

def _is_greeting(t): 
    return bool(re.search(r"\b(halo|hai|hi|hello|hey|mulai|start|apa kabar|p|tes|test|assalamualaikum|pagi|siang|sore|malam|yo|cuy)\b", t))

def _is_browse(t):   
    return bool(re.search(r"\b(lihat|event|daftar|semua|list|tampil|show|pilih|cari|jadwal|acara|ikutan|join|seminar|workshop)\b", t))

def _is_status(t):   
    return bool(re.search(r"\b(cek|status|check|periksa|kode|lacak|tiket|pantau)\b", t))

def _is_cancel(t):   
    return bool(re.search(r"\b(batal|cancel|hapus|batalkan|gajadi|nggak jadi|ga jadi|mundur|refund|urungkan)\b", t))

def _is_back(t):     
    return bool(re.search(r"\b(kembali|menu|back|keluar|main menu|awal|beranda|home|reset|ulang)\b", t))

def _is_yes(t):      
    return bool(re.search(r"\b(ya|yes|oke|ok|yap|iya|konfirmasi|yakin|setuju|lanjut|betul|bener|yoi|yup|gas|boleh)\b", t))

def _is_no(t):       
    return bool(re.search(r"\b(tidak|no|nope|ga|gak|jangan|batal|nggak|ndak|kagak|ngga)\b", t))

def _is_valid_email(t): 
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[a-z]{2,}$", t, re.I))

def _is_valid_phone(t): 
    return bool(re.match(r"^(\+62|62|0)\d{8,12}$", t.replace(" ", "").replace("-", "")))

def _is_reg_code(t):    
    return bool(re.match(r"^EVT-[A-Z0-9]{5}$", t.upper()))

def _gen_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "EVT-" + "".join(secrets.choice(alphabet) for _ in range(5))


# ──────────────────────────────────────────────
#  TOPIC MAP — Peta Intent Pengguna ke Tag Kategori
#  Setiap topik berisi: (kata kunci trigger, tag pencarian di event)
# ──────────────────────────────────────────────
TOPIC_MAP = [
    # ── Desain & UI/UX ──────────────────────────────────────────────
    {
        "label": "Desain & UI/UX",
        "emoji": "🎨",
        "triggers": [
            "ui", "ux", "ui/ux", "user interface", "user experience",
            "desain", "design", "figma", "prototype", "wireframe", "mockup",
            "belajar desain", "mau desain", "tertarik desain", "ingin desain",
            "visual", "kreatif", "grafis", "graphic", "adobe", "canva",
            "interface", "interaksi", "hci", "human computer", "product design",
            "design thinking", "ux research", "usability", "accessibility",
        ],
        "tags": ["desain", "ui", "ux", "design", "visual", "grafis", "kreatif"],
    },
    # ── Programming & Coding ─────────────────────────────────────────
    {
        "label": "Programming & Coding",
        "emoji": "💻",
        "triggers": [
            "coding", "code", "ngoding", "koding", "programmer", "programming",
            "developer", "dev", "belajar coding", "mau coding", "ingin coding",
            "python", "javascript", "java", "php", "golang", "flutter", "kotlin",
            "android", "ios", "mobile", "web", "backend", "frontend", "fullstack",
            "pemrograman", "aplikasi", "app", "software", "buat aplikasi",
            "belajar python", "belajar javascript", "belajar web", "html", "css",
            "react", "vue", "nodejs", "laravel", "django", "spring", "rust", "c++",
        ],
        "tags": ["programming", "coding", "developer", "software", "web", "mobile", "python", "javascript"],
    },
    # ── Data & AI/ML ─────────────────────────────────────────────────
    {
        "label": "Data Science & AI",
        "emoji": "📊",
        "triggers": [
            "data", "data science", "machine learning", "ml", "ai", "artificial intelligence",
            "deep learning", "neural", "analisis data", "analitik", "analytics",
            "belajar data", "mau data", "ingin data", "dataset",
            "sql", "database", "big data", "hadoop", "spark", "tableau",
            "statistik", "statistika", "model prediksi", "nlp", "computer vision",
            "chatgpt", "llm", "generative ai", "tensorflow", "pytorch", "scikit",
            "r programming", "data engineer", "data analyst","belajar", "business intelligence",
        ],
        "tags": ["data", "machine learning", "ai", "analitik", "sql", "statistik"],
    },
    # ── Bisnis & Kewirausahaan ───────────────────────────────────────
    {
        "label": "Bisnis & Kewirausahaan",
        "emoji": "💼",
        "triggers": [
            "bisnis", "business", "wirausaha", "entrepreneur", "startup",
            "jualan", "jual", "berdagang", "dagang", "usaha", "umkm",
            "mau bisnis", "ingin bisnis", "buka usaha", "buka toko",
            "pitch", "investor", "funding", "modal", "revenue", "profit",
            "manajemen", "management", "leadership", "pemimpin",
            "strategi bisnis", "business model", "lean", "scrum", "agile",
            "networking", "kolaborasi", "partner", "kerjasama",
        ],
        "tags": ["bisnis", "startup", "entrepreneur", "wirausaha", "manajemen"],
    },
    # ── Marketing & Digital Marketing ────────────────────────────────
    {
        "label": "Marketing & Digital",
        "emoji": "📣",
        "triggers": [
            "marketing", "pemasaran", "digital marketing", "promosi",
            "sosmed", "social media", "instagram", "tiktok", "youtube",
            "content creator", "konten", "copywriting", "copy",
            "seo", "sem", "google ads", "facebook ads", "iklan",
            "branding", "brand", "influencer", "kol", "email marketing",
            "growth hacking", "growth", "funnel", "conversion",
            "mau marketing", "belajar marketing", "ingin marketing",
        ],
        "tags": ["marketing", "digital", "sosmed", "branding", "konten", "seo"],
    },
    # ── Keuangan & Investasi ─────────────────────────────────────────
    {
        "label": "Keuangan & Investasi",
        "emoji": "💰",
        "triggers": [
            "keuangan", "finance", "investasi", "invest", "saham", "stock",
            "crypto", "bitcoin", "aset", "portofolio", "reksa dana",
            "tabungan", "menabung", "finansial", "literasi keuangan",
            "trading", "forex", "obligasi", "deposito", "asuransi",
            "mau invest", "belajar investasi", "ingin investasi", "belajar saham",
        ],
        "tags": ["keuangan", "finance", "investasi", "saham", "trading"],
    },
    # ── Fotografi & Videografi ───────────────────────────────────────
    {
        "label": "Fotografi & Videografi",
        "emoji": "📸",
        "triggers": [
            "foto", "fotografi", "photography", "kamera", "camera",
            "video", "videografi", "videography", "sinematografi",
            "editing foto", "edit foto", "lightroom", "photoshop",
            "premiere", "after effects", "editing video", "edit video",
            "vlog", "youtuber", "konten video", "short film",
            "belajar foto", "mau foto", "ingin foto",
        ],
        "tags": ["fotografi", "videografi", "foto", "video", "editing"],
    },
    # ── Public Speaking & Soft Skills ────────────────────────────────
    {
        "label": "Public Speaking & Soft Skills",
        "emoji": "🎤",
        "triggers": [
            "public speaking", "berbicara", "presentasi", "presentation",
            "komunikasi", "communication", "percaya diri", "self confidence",
            "leadership", "kepemimpinan", "teamwork", "kerja tim",
            "soft skill", "personal development", "pengembangan diri",
            "mau presentasi", "belajar berbicara", "ingin komunikasi",
            "negosiasi", "negotiation", "persuasi", "storytelling",
        ],
        "tags": ["public speaking", "komunikasi", "presentasi", "soft skill", "leadership"],
    },
    # ── Cybersecurity ────────────────────────────────────────────────
    {
        "label": "Cybersecurity",
        "emoji": "🔐",
        "triggers": [
            "keamanan", "security", "cybersecurity", "hacking", "ethical hacking",
            "penetration testing", "pentest", "ctf", "bug bounty",
            "network security", "firewall", "enkripsi", "encryption",
            "belajar hacking", "mau cyber", "ingin security",
        ],
        "tags": ["keamanan", "cyber", "security", "hacking", "pentest"],
    },
    # ── Cloud & DevOps ───────────────────────────────────────────────
    {
        "label": "Cloud & DevOps",
        "emoji": "☁️",
        "triggers": [
            "cloud", "aws", "gcp", "azure", "google cloud", "devops",
            "docker", "kubernetes", "k8s", "container", "microservice",
            "ci/cd", "pipeline", "deployment", "server", "linux",
            "infrastructure", "iaas", "saas", "paas",
            "belajar cloud", "mau devops", "ingin cloud",
        ],
        "tags": ["cloud", "devops", "aws", "docker", "server", "linux"],
    },
    # ── Kesehatan & Wellness ─────────────────────────────────────────
    {
        "label": "Kesehatan & Wellness",
        "emoji": "🏃",
        "triggers": [
            "kesehatan", "health", "wellness", "sehat", "olahraga",
            "yoga", "meditasi", "meditation", "mindfulness", "mental health",
            "kesehatan mental", "stress", "produktivitas", "produktif",
            "tidur", "sleep", "nutrisi", "gizi", "diet",
            "mau sehat", "ingin sehat", "belajar kesehatan",
        ],
        "tags": ["kesehatan", "wellness", "olahraga", "mental health", "sehat"],
    },
]


def _detect_topic(text: str) -> dict | None:
    """
    Mendeteksi topik/intent dari teks pengguna.
    Mengembalikan dict topik pertama yang cocok, atau None.
    """
    low = text.lower()
    # Hapus kata-kata umum yang tidak relevan
    noise = r"\b(saya|aku|mau|ingin|minta|tolong|pengen|pengin|kepingin|tertarik|belajar|cari|coba|ikut|ikutan|ada|event|acara|seminar|workshop|dong|deh|yuk|nih|loh|kak|mas|mbak|bang)\b"
    clean = re.sub(noise, " ", low).strip()

    best_topic = None
    best_score = 0

    for topic in TOPIC_MAP:
        score = 0
        for trigger in topic["triggers"]:
            if trigger in clean or trigger in low:
                # Bonus skor jika trigger lebih panjang (lebih spesifik)
                score += 1 + len(trigger.split()) * 0.5
        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic if best_score > 0 else None


def _recommend_by_topic(topic: dict, events: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Mencari event yang cocok dengan topik.
    Mengembalikan (matched_events, unmatched_fallback_events).
    """
    matches = []
    for e in events:
        if is_full(e):
            continue
        haystack = " ".join([
            e.get("title", ""), e.get("desc", ""),
            e.get("category", ""), e.get("type", "")
        ]).lower()
        if any(tag in haystack for tag in topic["tags"]):
            matches.append(e)

    # Jika tidak ada yang cocok persis, ambil event yang tidak penuh
    if not matches:
        matches = [e for e in events if not is_full(e)][:3]

    return matches


# ──────────────────────────────────────────────
#  TEXT FORMATTERS
# ──────────────────────────────────────────────
def _event_list_text(events: list[dict]) -> str:
    lines = ["📋 **Daftar Event yang Tersedia:**\n"]
    for i, e in enumerate(events, 1):
        status = "🔴 PENUH" if is_full(e) else f"🟢 {e['quota'] - e['registered']} kursi tersisa"
        lines.append(
            f"**{i}. {e['emoji']} {e['title']}**\n"
            f"   📅 {e['date']} | 🕐 {e['time']}\n"
            f"   📍 {e['location']} | 💰 {format_price(e['price'])}\n"
            f"   {status}\n"
        )
    lines.append("\nKetik **nomor event** (1–{}) untuk melihat detail, atau tanyakan apa saja!".format(len(events)))
    return "\n".join(lines)

def _event_detail_text(e: dict) -> str:
    pct    = quota_pct(e)
    status = "🔴 PENUH" if is_full(e) else f"🟢 {e['quota'] - e['registered']} kursi tersisa ({pct}% terisi)"
    return (
        f"### {e['emoji']} {e['title']}\n\n"
        f"📅 **Tanggal:** {e['date']}\n"
        f"🕐 **Waktu:** {e['time']}\n"
        f"📍 **Lokasi:** {e['location']}\n"
        f"🏷️ **Kategori:** {e['category']} — {e['type']}\n"
        f"💰 **Harga:** {format_price(e['price'])}\n"
        f"👥 **Kuota:** {status}\n\n"
        f"📝 {e['desc']}\n\n"
        f"{'❌ Event ini sudah penuh.' if is_full(e) else 'Ketik **YA** untuk mendaftar atau **kembali** untuk event lain.'}"
    )


# ──────────────────────────────────────────────
#  KEYWORD FALLBACK 
# ──────────────────────────────────────────────
def keyword_fallback(text: str, events: list[dict]) -> str:
    """Jawaban berbasis kata kunci dan topic detection saat FSM tidak mengenali input."""
    low = text.lower().strip()

    # ── Sapaan ──────────────────────────────────────────────────────
    if _is_greeting(low):
        return (
            "👋 Halo! Saya **EventBot**, siap membantu Anda! 😊\n\n"
            "Saya bisa membantu:\n"
            "- 📋 **Lihat Event** — ketik `lihat event`\n"
            "- 🔍 **Cek Status** — ketik `cek status`\n"
            "- ❌ **Batal Pendaftaran** — ketik `batal`\n"
            "- 💬 Tanya tentang **harga**, **jadwal**, **lokasi**, atau **rekomendasi**!\n\n"
            "Mau mulai dari mana?"
        )

    # ── Harga / gratis ──────────────────────────────────────────────
    if any(w in low for w in ["gratis", "free", "harga", "bayar", "biaya", "tiket", "murah"]):
        gratis = [e for e in events if e["price"] == 0]
        if gratis and any(w in low for w in ["gratis", "free", "murah"]):
            names = ", ".join(f"**{e['title']}**" for e in gratis)
            return f"🎉 Event **gratis** yang tersedia: {names}\n\nKetik **lihat event** untuk detail lengkap!"
        lines = "\n".join(f"- {e['emoji']} {e['title']}: **{format_price(e['price'])}**" for e in events)
        return f"💰 **Daftar Harga Event:**\n\n{lines}\n\nKetik **lihat event** atau nomor event untuk detail."

    # ── Kuota / slot ────────────────────────────────────────────────
    if any(w in low for w in ["sisa", "kuota", "slot", "penuh", "kosong", "tempat"]):
        lines = []
        for e in events:
            sisa = e["quota"] - e["registered"]
            status = "🔴 PENUH" if sisa <= 0 else f"🟢 {sisa} kursi tersisa"
            lines.append(f"- {e['emoji']} {e['title']}: {status}")
        return "📊 **Status Kuota Event:**\n\n" + "\n".join(lines) + "\n\nKetik **lihat event** untuk daftar lengkap."

    # ── Lokasi / tempat ─────────────────────────────────────────────
    if any(w in low for w in ["lokasi", "tempat", "dimana", "di mana", "venue", "kota"]):
        lines = "\n".join(f"- {e['emoji']} {e['title']}: 📍 {e['location']}" for e in events)
        return f"📍 **Lokasi Event:**\n\n{lines}\n\nKetik **lihat event** untuk detail lengkap."

    # ── Jadwal / tanggal ────────────────────────────────────────────
    if any(w in low for w in ["tanggal", "kapan", "jadwal", "bulan", "hari", "waktu", "jam"]):
        lines = "\n".join(f"- {e['emoji']} {e['title']}: 📅 {e['date']}, 🕐 {e['time']}" for e in events)
        return f"📅 **Jadwal Event:**\n\n{lines}\n\nKetik **lihat event** untuk detail lebih lanjut."

    # ── Cara daftar / panduan ───────────────────────────────────────
    if any(w in low for w in ["cara", "bagaimana", "gimana", "proses", "langkah", "panduan"]):
        return (
            "📝 **Cara Mendaftar Event:**\n\n"
            "1. Ketik **lihat event** untuk melihat daftar\n"
            "2. Ketik **nomor event** yang ingin didaftarkan\n"
            "3. Ketik **YA** untuk konfirmasi\n"
            "4. Isi **nama**, **email**, dan **nomor HP**\n"
            "5. Konfirmasi dan dapatkan **kode registrasi EVT-XXXXX**!\n\n"
            "Mau mulai? Ketik **lihat event** sekarang! 😊"
        )

    # ── Bantuan / help ──────────────────────────────────────────────
    if any(w in low for w in ["help", "bantuan", "tolong", "bisa apa", "fitur", "menu"]):
        return (
            "🤖 **EventBot bisa membantu Anda dengan:**\n\n"
            "- **`lihat event`** — tampilkan semua event tersedia\n"
            "- **`cek status`** — cek status pendaftaran dengan kode EVT-XXXXX\n"
            "- **`batal`** — batalkan pendaftaran\n"
            "- **`harga`** — lihat daftar harga event\n"
            "- **`jadwal`** — lihat jadwal semua event\n"
            "- **`lokasi`** — lihat lokasi semua event\n"
            "- **`rekomendasi`** — dapatkan saran event untuk Anda\n"
            "- **`cara daftar`** — panduan pendaftaran step-by-step\n\n"
            "Atau ceritakan minat Anda, misalnya:\n"
            "_\"saya mau belajar UI/UX\"_ atau _\"tertarik coding Python\"_!"
        )

    # ── TOPIC DETECTION — Inti rekomendasi berbasis intent ──────────
    # Ini menangkap pola seperti:
    # "saya mau belajar UI/UX", "tertarik data science", "ingin coding",
    # "pengen ikut workshop desain", "ada event tentang marketing?", dll.
    topic = _detect_topic(low)
    if topic:
        matched = _recommend_by_topic(topic, events)

        if not matched:
            return (
                f"{topic['emoji']} Wah, minat Anda di bidang **{topic['label']}** sangat bagus! "
                f"Sayangnya belum ada event yang tersedia untuk topik ini saat ini.\n\n"
                f"Ketik **lihat event** untuk melihat semua event yang tersedia. "
                f"Kami akan terus menambahkan event baru! 😊"
            )

        # Format rekomendasi dengan info lengkap
        rec_lines = []
        for i, e in enumerate(matched[:3], 1):
            sisa = e["quota"] - e["registered"]
            status = f"🟢 {sisa} kursi tersisa"
            rec_lines.append(
                f"**{i}. {e['emoji']} {e['title']}**\n"
                f"   📅 {e['date']} | 💰 {format_price(e['price'])}\n"
                f"   📍 {e['location']} | {status}"
            )

        return (
            f"{topic['emoji']} Karena Anda tertarik dengan **{topic['label']}**, "
            f"berikut event yang relevan:\n\n"
            + "\n\n".join(rec_lines)
            + "\n\nKetik **lihat event** untuk semua event atau **nomor event** untuk detail & daftar!"
        )

    # ── Fallback eksplisit kata "rekomendasi" ───────────────────────
    if any(w in low for w in ["rekomendasi", "rekomen", "cocok", "saran", "suggest"]):
        available = [e for e in events if not is_full(e)][:3]
        if not available:
            available = events[:3]
        recs = "\n".join(
            f"- {e['emoji']} **{e['title']}** — {e['category']}, {format_price(e['price'])}"
            for e in available
        )
        return (
            f"🎯 **Rekomendasi Event Populer:**\n\n{recs}\n\n"
            f"💡 _Tip: Ceritakan minat Anda untuk rekomendasi lebih tepat!_\n"
            f"Contoh: _\"saya mau belajar desain\"_ atau _\"tertarik bisnis startup\"_"
        )

    # ── Default ─────────────────────────────────────────────────────
    return (
        "😊 Maaf, saya belum mengenali perintah tersebut.\n\n"
        "Coba salah satu kata kunci berikut:\n"
        "- **`lihat event`** — lihat semua event\n"
        "- **`cek status`** — cek pendaftaran\n"
        "- **`batal`** — batalkan pendaftaran\n"
        "- **`harga`** / **`jadwal`** / **`lokasi`** / **`rekomendasi`**\n\n"
        "Atau ceritakan minat Anda! Contoh:\n"
        "_\"saya mau belajar UI/UX\"_, _\"tertarik coding\"_, _\"ingin belajar bisnis\"_ 💡"
    )


# ──────────────────────────────────────────────
#  MAIN FSM STEP
# ──────────────────────────────────────────────
def fsm_step(fsm: FSM, text: str, events: list[dict]) -> tuple[str, list[str], bool]:
    t   = text.strip()
    low = _low(t)

    # ── IDLE ─
    if fsm.state == State.IDLE:
        if _is_browse(low):
            fsm.state = State.BROWSING
            return _event_list_text(events), [str(i) for i in range(1, len(events)+1)] + ["Kembali"], False
        if _is_status(low):
            fsm.state = State.CHECK_STATUS
            return "🔍 **Cek Status Pendaftaran**\n\nMasukkan **kode registrasi** Anda (format: `EVT-XXXXX`):", ["Kembali"], False
        if _is_cancel(low) and not _is_yes(low):
            fsm.state = State.CANCELLING
            return "❌ **Batalkan Pendaftaran**\n\nMasukkan **kode registrasi** yang ingin dibatalkan:", ["Kembali"], False
        if _is_greeting(low):
            return (
                "👋 Halo! Saya **EventBot**, siap membantu Anda! 😊\n\n"
                "Saya bisa membantu:\n"
                "- 📋 **Lihat Event** — cari event yang cocok untuk Anda\n"
                "- 🔍 **Cek Status** — cek pendaftaran dengan kode registrasi\n"
                "- ❌ **Batal Pendaftaran** — batalkan pendaftaran yang ada\n\n"
                "Mau mulai dari mana?",
                ["Lihat Event", "Cek Status", "Batal Pendaftaran"],
                False,
            )
        
        return "", ["Lihat Event", "Cek Status", "Batal Pendaftaran"], True

    # ── BROWSING 
    elif fsm.state == State.BROWSING:
        if _is_back(low):
            fsm.state = State.IDLE
            return "Kembali ke menu utama. Ada yang bisa saya bantu? 😊", ["Lihat Event", "Cek Status", "Batal Pendaftaran"], False
        if t.isdigit():
            idx = int(t)
            ev  = get_event_by_index(events, idx)
            if ev:
                fsm.selected_event = ev
                fsm.state = State.REGISTERING
                return _event_detail_text(ev), (["Kembali"] if is_full(ev) else ["Ya, Daftar!", "Kembali"]), False
            return f"❌ Nomor **{idx}** tidak valid. Pilih antara 1–{len(events)}.", [str(i) for i in range(1, len(events)+1)] + ["Kembali"], False
        return "", [str(i) for i in range(1, len(events)+1)] + ["Kembali"], True

    # ── REGISTERING ───────────────────────────
    elif fsm.state == State.REGISTERING:
        if _is_back(low):
            fsm.state = State.BROWSING
            return _event_list_text(events), [str(i) for i in range(1, len(events)+1)] + ["Kembali"], False
        ev = fsm.selected_event
        if ev and is_full(ev):
            fsm.state = State.BROWSING
            return "❌ Event ini sudah penuh. Silakan pilih event lain.", [str(i) for i in range(1, len(events)+1)] + ["Kembali"], False
        if _is_yes(low):
            fsm.state = State.COLLECT_NAME
            return "Baik! Mari mulai pendaftaran 😊\n\n✏️ Masukkan **nama lengkap** Anda:", ["Kembali"], False
        return "", ["Ya, Daftar!", "Kembali"], True

    # ── COLLECT_NAME ──────────────────────────
    elif fsm.state == State.COLLECT_NAME:
        if _is_back(low):
            fsm.state = State.IDLE
            return "Pendaftaran dibatalkan. Kembali ke menu utama.", ["Lihat Event", "Cek Status"], False
        if len(t) < 3 or t.isdigit():
            return "⚠️ Nama tidak valid. Masukkan **nama lengkap** Anda (min. 3 huruf):", ["Kembali"], False
        if len(t) > 100:
            return "⚠️ Nama terlalu panjang (maks. 100 karakter). Coba lagi:", ["Kembali"], False
        fsm.user_info["name"] = t.title()
        fsm.state = State.COLLECT_EMAIL
        return f"✅ Nama: **{t.title()}**\n\n📧 Masukkan **alamat email** aktif Anda:", ["Kembali"], False

    # ── COLLECT_EMAIL ─────────────────────────
    elif fsm.state == State.COLLECT_EMAIL:
        if _is_back(low):
            fsm.state = State.COLLECT_NAME
            fsm.user_info.pop("name", None)
            return "✏️ Masukkan ulang **nama lengkap** Anda:", ["Kembali"], False
        if len(t) > 254:
            return "⚠️ Email terlalu panjang (maks. 254 karakter). Coba lagi:", ["Kembali"], False
        if not _is_valid_email(t):
            return "⚠️ Format email tidak valid.\nContoh yang benar: `nama@email.com`\n\nCoba lagi:", ["Kembali"], False
        fsm.user_info["email"] = t.lower()
        fsm.state = State.COLLECT_PHONE
        return f"✅ Email: **{t.lower()}**\n\n📱 Masukkan **nomor HP** Anda (contoh: `08123456789`):", ["Kembali"], False

    # ── COLLECT_PHONE ─────────────────────────
    elif fsm.state == State.COLLECT_PHONE:
        if _is_back(low):
            fsm.state = State.COLLECT_EMAIL
            fsm.user_info.pop("email", None)
            return "📧 Masukkan ulang **email** Anda:", ["Kembali"], False
        if len(t) > 20:
            return "⚠️ Nomor HP terlalu panjang (maks. 20 karakter). Coba lagi:", ["Kembali"], False
        if not _is_valid_phone(t):
            return "⚠️ Format nomor HP tidak valid.\nGunakan format: `08123456789` atau `+628123456789`\n\nCoba lagi:", ["Kembali"], False
        fsm.user_info["phone"] = t
        fsm.state = State.CONFIRMING
        ev = fsm.selected_event
        return (
            f"📋 **Konfirmasi Data Pendaftaran**\n\n"
            f"👤 Nama   : **{fsm.user_info['name']}**\n"
            f"📧 Email  : {fsm.user_info['email']}\n"
            f"📱 HP     : {fsm.user_info['phone']}\n\n"
            f"🎪 **{ev['emoji']} {ev['title']}**\n"
            f"📅 {ev['date']} | 🕐 {ev['time']}\n"
            f"📍 {ev['location']}\n"
            f"💰 {format_price(ev['price'])}\n\n"
            f"Apakah data sudah benar? Ketik **YA** untuk lanjut.",
            ["Ya, Konfirmasi!", "Tidak, Ulangi"],
            False,
        )

    # ── CONFIRMING ────────────────────────────
    elif fsm.state == State.CONFIRMING:
        if _is_yes(low):
            from datetime import datetime
            ev   = fsm.selected_event
            code = _gen_code()
            ev["registered"] = min(ev["registered"] + 1, ev["quota"])
            fsm.registrations[code] = {
                "code": code, "name": fsm.user_info["name"],
                "email": fsm.user_info["email"], "phone": fsm.user_info["phone"],
                "event": ev, "time": datetime.now().strftime("%d %b %Y, %H:%M WIB"),
            }
            fsm.user_info = {}
            fsm.state = State.DONE
            return (
                f"🎉 **Pendaftaran Berhasil!**\n\n"
                f"🎫 **Kode Registrasi Anda:**\n"
                f"## `{code}`\n\n"
                f"✅ Simpan kode ini untuk check-in!\n"
                f"📅 {ev['date']} | 📍 {ev['location']}",
                ["Lihat Event Lain", "Cek Status", "Selesai"],
                False,
            )
        if _is_no(low):
            fsm.state = State.COLLECT_NAME
            fsm.user_info = {}
            return "Oke, mari ulangi dari awal.\n\n✏️ **Nama lengkap** Anda:", ["Kembali"], False
        return "Ketik **YA** untuk konfirmasi atau **TIDAK** untuk mengulang.", ["Ya, Konfirmasi!", "Tidak, Ulangi"], False

    # ── DONE ──────────────────────────────────
    elif fsm.state == State.DONE:
        if _is_browse(low) or "event lain" in low:
            fsm.state = State.BROWSING
            return _event_list_text(events), [str(i) for i in range(1, len(events)+1)] + ["Kembali"], False
        if _is_status(low):
            fsm.state = State.CHECK_STATUS
            return "Masukkan **kode registrasi** Anda:", ["Kembali"], False
        fsm.state = State.IDLE
        return "", ["Lihat Event Lain", "Cek Status", "Selesai"], True

    # ── CHECK_STATUS ──────────────────────────
    elif fsm.state == State.CHECK_STATUS:
        if _is_back(low):
            fsm.state = State.IDLE
            return "Kembali ke menu utama.", ["Lihat Event", "Cek Status", "Batal Pendaftaran"], False
        code = t.upper()
        reg  = fsm.registrations.get(code)
        if reg:
            ev = reg["event"]
            fsm.state = State.IDLE
            return (
                f"✅ **Status Ditemukan!**\n\n"
                f"📌 Kode   : **{reg['code']}**\n"
                f"👤 Nama   : {reg['name']}\n"
                f"📧 Email  : {reg['email']}\n"
                f"📱 HP     : {reg['phone']}\n\n"
                f"🎪 **{ev['emoji']} {ev['title']}**\n"
                f"📅 {ev['date']} | 📍 {ev['location']}\n\n"
                f"🟢 Status : **TERDAFTAR** ✓\n"
                f"🕒 Waktu  : {reg['time']}",
                ["Batalkan Pendaftaran", "Lihat Event Lain", "Selesai"],
                False,
            )
        if _is_reg_code(t):
            return f"❌ Kode **`{code}`** tidak ditemukan dalam sesi ini.\n\nPastikan kode benar atau coba kode lain:", ["Kembali"], False
        return "Format kode tidak valid. Masukkan kode dengan format **`EVT-XXXXX`**\n\nContoh: `EVT-AB12C`", ["Kembali"], False

    # ── CANCELLING ────────────────────────────
    elif fsm.state == State.CANCELLING:
        if _is_back(low):
            fsm.state = State.IDLE
            return "Kembali ke menu utama.", ["Lihat Event", "Cek Status"], False
        code = t.upper()
        reg  = fsm.registrations.get(code)
        if reg:
            fsm.cancel_code = code
            fsm.state = State.CANCEL_CONFIRM
            ev = reg["event"]
            return (
                f"⚠️ **Konfirmasi Pembatalan**\n\n"
                f"📌 Kode  : **{reg['code']}**\n"
                f"👤 Nama  : {reg['name']}\n"
                f"🎪 {ev['emoji']} {ev['title']}\n"
                f"📅 {ev['date']}\n\n"
                f"Apakah Anda **yakin** ingin membatalkan?",
                ["Ya, Batalkan", "Tidak, Kembali"],
                False,
            )
        if _is_reg_code(t):
            return f"❌ Kode **`{code}`** tidak ditemukan. Coba kode lain:", ["Kembali"], False
        return "Format kode tidak valid. Masukkan **`EVT-XXXXX`**:", ["Kembali"], False

    # ── CANCEL_CONFIRM ────────────────────────
    elif fsm.state == State.CANCEL_CONFIRM:
        if _is_yes(low):
            code = fsm.cancel_code
            reg  = fsm.registrations.pop(code, None)
            fsm.state = State.IDLE
            fsm.cancel_code = ""
            if reg:
                reg["event"]["registered"] = max(0, reg["event"]["registered"] - 1)
                return (
                    f"✅ **Pendaftaran Berhasil Dibatalkan**\n\n"
                    f"📌 `{code}` — {reg['name']}\n"
                    f"🎪 {reg['event']['title']}\n\n"
                    f"Kuota telah dikembalikan. Anda bisa daftar event lain kapan saja 😊",
                    ["Lihat Event", "Selesai"],
                    False,
                )
        fsm.state = State.IDLE
        fsm.cancel_code = ""
        return "Pembatalan dibatalkan 😊 Pendaftaran Anda masih **aktif**.", ["Lihat Event", "Cek Status"], False

    fsm.state = State.IDLE
    return "", ["Halo", "Lihat Event", "Cek Status"], True