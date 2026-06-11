"""
engine.py — NLP + FSM EventBot (upgraded)
"""
import random
import re
import string
from fsm import State, FSM, get_event_by_index, format_price, quota_pct, is_full

# ──────────────────────────────────────────────
#  NLP HELPERS (Dengan Kata Kunci Lebih Beragam)
# ──────────────────────────────────────────────
def _low(t: str) -> str: return t.lower().strip()

def _is_greeting(t): 
    # Tambahan: sapaan muslim, waktu, slang (p, tes, yo)
    return bool(re.search(r"\b(halo|hai|hi|hello|hey|mulai|start|apa kabar|p|tes|test|assalamualaikum|pagi|siang|sore|malam|yo|cuy)\b", t))

def _is_browse(t):   
    # Tambahan: join, cari, jadwal, acara, ikutan, dll
    return bool(re.search(r"\b(lihat|event|daftar|semua|list|tampil|show|pilih|cari|jadwal|acara|ikutan|join|seminar|workshop)\b", t))

def _is_status(t):   
    # Tambahan: lacak, tiket saya, pantau
    return bool(re.search(r"\b(cek|status|check|periksa|kode|lacak|tiket|pantau)\b", t))

def _is_cancel(t):   
    # Tambahan: gajadi, mundur, refund, urung
    return bool(re.search(r"\b(batal|cancel|hapus|batalkan|gajadi|nggak jadi|ga jadi|mundur|refund|urungkan)\b", t))

def _is_back(t):     
    # Tambahan: home, awal, beranda, reset
    return bool(re.search(r"\b(kembali|menu|back|keluar|main menu|awal|beranda|home|reset|ulang)\b", t))

def _is_yes(t):      
    # Tambahan: gas, yoi, betul, bener, boleh
    return bool(re.search(r"\b(ya|yes|oke|ok|yap|iya|konfirmasi|yakin|setuju|lanjut|betul|bener|yoi|yup|gas|boleh)\b", t))

def _is_no(t):       
    # Tambahan: nggak, ndak, kagak, ngga
    return bool(re.search(r"\b(tidak|no|nope|ga|gak|jangan|batal|nggak|ndak|kagak|ngga)\b", t))

def _is_valid_email(t): 
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[a-z]{2,}$", t, re.I))

def _is_valid_phone(t): 
    return bool(re.match(r"^(\+62|62|0)\d{8,12}$", t.replace(" ", "").replace("-", "")))

def _is_reg_code(t):    
    return bool(re.match(r"^EVT-[A-Z0-9]{5}$", t.upper()))

def _gen_code() -> str:
    return "EVT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

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
#  KEYWORD FALLBACK (Tanpa AI)
# ──────────────────────────────────────────────
def keyword_fallback(text: str, events: list[dict]) -> str:
    """Jawaban berbasis kata kunci saat FSM tidak mengenali input."""
    low = text.lower().strip()

    # Sapaan
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

    # Harga / gratis
    if any(w in low for w in ["gratis", "free", "harga", "bayar", "biaya", "tiket", "murah"]):
        gratis = [e for e in events if e["price"] == 0]
        if gratis and any(w in low for w in ["gratis", "free", "murah"]):
            names = ", ".join(f"**{e['title']}**" for e in gratis)
            return f"🎉 Event **gratis** yang tersedia: {names}\n\nKetik **lihat event** untuk detail lengkap!"
        lines = "\n".join(f"- {e['emoji']} {e['title']}: **{format_price(e['price'])}**" for e in events)
        return f"💰 **Daftar Harga Event:**\n\n{lines}\n\nKetik **lihat event** atau nomor event untuk detail."

    # Kuota / slot
    if any(w in low for w in ["sisa", "kuota", "slot", "penuh", "kosong", "tempat"]):
        lines = []
        for e in events:
            sisa = e["quota"] - e["registered"]
            status = "🔴 PENUH" if sisa <= 0 else f"🟢 {sisa} kursi tersisa"
            lines.append(f"- {e['emoji']} {e['title']}: {status}")
        return "📊 **Status Kuota Event:**\n\n" + "\n".join(lines) + "\n\nKetik **lihat event** untuk daftar lengkap."

    # Lokasi / tempat
    if any(w in low for w in ["lokasi", "tempat", "dimana", "di mana", "venue", "kota"]):
        lines = "\n".join(f"- {e['emoji']} {e['title']}: 📍 {e['location']}" for e in events)
        return f"📍 **Lokasi Event:**\n\n{lines}\n\nKetik **lihat event** untuk detail lengkap."

    # Jadwal / tanggal
    if any(w in low for w in ["tanggal", "kapan", "jadwal", "bulan", "hari", "waktu", "jam"]):
        lines = "\n".join(f"- {e['emoji']} {e['title']}: 📅 {e['date']}, 🕐 {e['time']}" for e in events)
        return f"📅 **Jadwal Event:**\n\n{lines}\n\nKetik **lihat event** untuk detail lebih lanjut."

    # Rekomendasi berdasarkan kategori
    if any(w in low for w in ["rekomendasi", "rekomen", "cocok", "saran", "suggest",
                               "programmer", "developer", "coding", "teknologi", "tech",
                               "data", "desain", "bisnis", "marketing", "seminar", "workshop"]):
        matches = []
        for e in events:
            haystack = (e.get("category","") + e.get("type","") + e.get("title","") + e.get("desc","")).lower()
            topic_keys = ["programmer","developer","coding","teknologi","tech","data","desain","bisnis","marketing","seminar","workshop"]
            if any(k in haystack for k in topic_keys if k in low):
                matches.append(e)
        if not matches:
            matches = [e for e in events if not is_full(e)][:3]
        if not matches:
            matches = events[:3]
        recs = "\n".join(f"- {e['emoji']} **{e['title']}** — {e['category']}, {format_price(e['price'])}" for e in matches)
        return f"🎯 **Rekomendasi Event untuk Anda:**\n\n{recs}\n\nKetik **lihat event** untuk semua event atau nomor untuk detail!"

    # Cara daftar / panduan
    if any(w in low for w in ["cara", "bagaimana", "gimana", "proses", "langkah", "panduan", "daftar"]):
        return (
            "📝 **Cara Mendaftar Event:**\n\n"
            "1. Ketik **lihat event** untuk melihat daftar\n"
            "2. Ketik **nomor event** yang ingin didaftarkan\n"
            "3. Ketik **YA** untuk konfirmasi\n"
            "4. Isi **nama**, **email**, dan **nomor HP**\n"
            "5. Konfirmasi dan dapatkan **kode registrasi EVT-XXXXX**!\n\n"
            "Mau mulai? Ketik **lihat event** sekarang! 😊"
        )

    # Bantuan / help
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
            "- **`cara daftar`** — panduan pendaftaran step-by-step"
        )

    # Default
    return (
        "😊 Maaf, saya belum mengenali perintah tersebut.\n\n"
        "Coba salah satu kata kunci berikut:\n"
        "- **`lihat event`** — lihat semua event\n"
        "- **`cek status`** — cek pendaftaran\n"
        "- **`batal`** — batalkan pendaftaran\n"
        "- **`harga`** / **`jadwal`** / **`lokasi`** / **`rekomendasi`**\n\n"
        "Atau ketik **`bantuan`** untuk panduan lengkap! 😊"
    )


# ──────────────────────────────────────────────
#  MAIN FSM STEP
# ──────────────────────────────────────────────
def fsm_step(fsm: FSM, text: str, events: list[dict]) -> tuple[str, list[str], bool]:
    t   = text.strip()
    low = _low(t)

    # ── IDLE ──────────────────────────────────
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
        # Coba jawab dengan AI; jika tidak ada API key, gunakan fallback
        return "", ["Lihat Event", "Cek Status", "Batal Pendaftaran"], True

    # ── BROWSING ──────────────────────────────
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
        fsm.user_info["name"] = t.title()
        fsm.state = State.COLLECT_EMAIL
        return f"✅ Nama: **{t.title()}**\n\n📧 Masukkan **alamat email** aktif Anda:", ["Kembali"], False

    # ── COLLECT_EMAIL ─────────────────────────
    elif fsm.state == State.COLLECT_EMAIL:
        if _is_back(low):
            fsm.state = State.COLLECT_NAME
            fsm.user_info.pop("name", None)
            return "✏️ Masukkan ulang **nama lengkap** Anda:", ["Kembali"], False
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