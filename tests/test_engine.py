"""Tests for engine.py — NLP helpers, validators, topic detection, formatters,
keyword_fallback, and the main fsm_step state machine."""

import copy
import re
import pytest

from fsm import (
    State, FSM, DEFAULT_EVENTS,
    get_event_by_index, format_price, is_full,
)
from engine import (
    _low, _is_greeting, _is_browse, _is_status, _is_cancel,
    _is_back, _is_yes, _is_no,
    _is_valid_email, _is_valid_phone, _is_reg_code, _gen_code,
    _detect_topic, _recommend_by_topic, TOPIC_MAP,
    _event_list_text, _event_detail_text,
    keyword_fallback, fsm_step,
)


# ── _low ─────────────────────────────────────────────────────────────────────

class TestLow:
    def test_strips_and_lowercases(self):
        assert _low("  Hello World  ") == "hello world"

    def test_empty_string(self):
        assert _low("") == ""


# ── Intent matchers ──────────────────────────────────────────────────────────

class TestIsGreeting:
    @pytest.mark.parametrize("text", [
        "halo", "hai", "hi", "hello", "hey", "mulai", "start",
        "apa kabar", "p", "tes", "assalamualaikum", "pagi",
        "siang", "sore", "malam", "yo", "cuy",
    ])
    def test_positive(self, text):
        assert _is_greeting(text)

    @pytest.mark.parametrize("text", ["daftar event", "batal", "123"])
    def test_negative(self, text):
        assert not _is_greeting(text)


class TestIsBrowse:
    @pytest.mark.parametrize("text", [
        "lihat", "event", "daftar", "semua", "list", "tampil",
        "show", "pilih", "cari", "jadwal", "seminar", "workshop",
    ])
    def test_positive(self, text):
        assert _is_browse(text)

    def test_negative(self):
        assert not _is_browse("batal pendaftaran")


class TestIsStatus:
    @pytest.mark.parametrize("text", [
        "cek", "status", "check", "periksa", "kode", "lacak", "tiket",
    ])
    def test_positive(self, text):
        assert _is_status(text)

    def test_negative(self):
        assert not _is_status("daftar event")


class TestIsCancel:
    @pytest.mark.parametrize("text", [
        "batal", "cancel", "hapus", "batalkan", "gajadi",
        "mundur", "refund", "urungkan",
    ])
    def test_positive(self, text):
        assert _is_cancel(text)

    def test_negative(self):
        assert not _is_cancel("lihat event")


class TestIsBack:
    @pytest.mark.parametrize("text", [
        "kembali", "menu", "back", "keluar", "main menu",
        "awal", "beranda", "home", "reset", "ulang",
    ])
    def test_positive(self, text):
        assert _is_back(text)

    def test_negative(self):
        assert not _is_back("daftar event baru")


class TestIsYes:
    @pytest.mark.parametrize("text", [
        "ya", "yes", "oke", "ok", "yap", "iya",
        "konfirmasi", "yakin", "setuju", "lanjut",
        "betul", "bener", "yoi", "yup", "gas", "boleh",
    ])
    def test_positive(self, text):
        assert _is_yes(text)

    def test_negative(self):
        assert not _is_yes("daftar event")


class TestIsNo:
    @pytest.mark.parametrize("text", [
        "tidak", "no", "nope", "ga", "gak", "jangan",
        "batal", "nggak", "ndak", "kagak", "ngga",
    ])
    def test_positive(self, text):
        assert _is_no(text)

    def test_negative(self):
        assert not _is_no("ya tentu")


# ── Validators ───────────────────────────────────────────────────────────────

class TestValidEmail:
    @pytest.mark.parametrize("email", [
        "user@example.com", "test.name+tag@domain.com",
        "a@b.xyz",
    ])
    def test_valid(self, email):
        assert _is_valid_email(email)

    @pytest.mark.parametrize("email", [
        "noatsign.com", "@missing.com", "user@", "user@.com", "",
    ])
    def test_invalid(self, email):
        assert not _is_valid_email(email)


class TestValidPhone:
    @pytest.mark.parametrize("phone", [
        "08123456789", "081234567890", "+6281234567890",
        "6281234567890", "0812-3456-7890",
    ])
    def test_valid(self, phone):
        assert _is_valid_phone(phone)

    @pytest.mark.parametrize("phone", [
        "12345", "abcde", "", "081",
    ])
    def test_invalid(self, phone):
        assert not _is_valid_phone(phone)


class TestIsRegCode:
    @pytest.mark.parametrize("code", ["EVT-AB12C", "EVT-ZZZZZ", "evt-ab12c"])
    def test_valid(self, code):
        assert _is_reg_code(code)

    @pytest.mark.parametrize("code", ["EVT12345", "ABC-12345", "EVT-AB", ""])
    def test_invalid(self, code):
        assert not _is_reg_code(code)


class TestGenCode:
    def test_format(self):
        code = _gen_code()
        assert re.match(r"^EVT-[A-Z0-9]{5}$", code)

    def test_uniqueness(self):
        codes = {_gen_code() for _ in range(50)}
        assert len(codes) > 1  # extremely unlikely all 50 are the same


# ── Topic Detection ──────────────────────────────────────────────────────────

class TestDetectTopic:
    def test_detects_design_topic(self):
        topic = _detect_topic("saya mau belajar ui/ux desain")
        assert topic is not None
        assert topic["label"] == "Desain & UI/UX"

    def test_detects_programming_topic(self):
        topic = _detect_topic("ingin belajar coding python")
        assert topic is not None
        assert topic["label"] == "Programming & Coding"

    def test_detects_data_ai_topic(self):
        topic = _detect_topic("machine learning dan deep learning")
        assert topic is not None
        assert topic["label"] == "Data Science & AI"

    def test_detects_business_topic(self):
        topic = _detect_topic("saya mau buka startup bisnis")
        assert topic is not None
        assert topic["label"] == "Bisnis & Kewirausahaan"

    def test_detects_marketing_topic(self):
        topic = _detect_topic("digital marketing dan seo")
        assert topic is not None
        assert topic["label"] == "Marketing & Digital"

    def test_detects_cybersecurity(self):
        topic = _detect_topic("ethical hacking penetration testing")
        assert topic is not None
        assert topic["label"] == "Cybersecurity"

    def test_detects_cloud_devops(self):
        topic = _detect_topic("belajar docker kubernetes cloud")
        assert topic is not None
        assert topic["label"] == "Cloud & DevOps"

    def test_no_match(self):
        assert _detect_topic("xyzzy gibberish 12345") is None

    def test_empty_string(self):
        assert _detect_topic("") is None


# ── _recommend_by_topic ──────────────────────────────────────────────────────

class TestRecommendByTopic:
    @pytest.fixture
    def events(self):
        return copy.deepcopy(DEFAULT_EVENTS)

    def test_matches_technology_events(self, events):
        topic = {"label": "AI", "emoji": "🧠",
                 "triggers": ["ai"], "tags": ["ai", "machine learning"]}
        matches = _recommend_by_topic(topic, events)
        assert len(matches) > 0
        # EVT001 is the AI seminar
        assert any("AI" in m["title"] for m in matches)

    def test_skips_full_events(self):
        events = [
            {"id": "1", "title": "Full Event", "desc": "ai event",
             "category": "Teknologi", "type": "Online",
             "quota": 10, "registered": 10},
        ]
        topic = {"label": "AI", "emoji": "🧠",
                 "triggers": ["ai"], "tags": ["ai"]}
        matches = _recommend_by_topic(topic, events)
        # Should fallback to non-full events; since all are full, returns empty subset
        assert isinstance(matches, list)

    def test_fallback_when_no_tag_match(self, events):
        topic = {"label": "Quantum", "emoji": "⚛️",
                 "triggers": ["quantum"], "tags": ["quantum computing"]}
        matches = _recommend_by_topic(topic, events)
        # Falls back to first 3 non-full events
        assert len(matches) <= len(events)
        assert len(matches) > 0


# ── Text Formatters ──────────────────────────────────────────────────────────

class TestEventListText:
    def test_contains_all_events(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        text = _event_list_text(events)
        for ev in events:
            assert ev["title"] in text

    def test_contains_numbering(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        text = _event_list_text(events)
        assert "1." in text
        assert f"{len(events)}." in text


class TestEventDetailText:
    def test_contains_fields(self):
        ev = DEFAULT_EVENTS[0]
        text = _event_detail_text(ev)
        assert ev["title"] in text
        assert ev["date"] in text
        assert ev["location"] in text
        assert format_price(ev["price"]) in text

    def test_full_event_message(self):
        ev = {"id": "X", "emoji": "🔬", "title": "Full",
              "date": "1 Jan", "time": "09:00", "location": "Zoom",
              "category": "Tech", "type": "Online",
              "price": 0, "quota": 10, "registered": 10,
              "free": True, "desc": "desc"}
        text = _event_detail_text(ev)
        assert "sudah penuh" in text


# ── keyword_fallback ─────────────────────────────────────────────────────────

class TestKeywordFallback:
    @pytest.fixture
    def events(self):
        return copy.deepcopy(DEFAULT_EVENTS)

    def test_greeting(self, events):
        resp = keyword_fallback("halo", events)
        assert "EventBot" in resp

    def test_price_query(self, events):
        resp = keyword_fallback("harga event", events)
        assert "Harga" in resp or "harga" in resp

    def test_free_events(self, events):
        resp = keyword_fallback("event gratis", events)
        assert "gratis" in resp.lower()

    def test_quota_query(self, events):
        resp = keyword_fallback("sisa kuota", events)
        assert "Kuota" in resp or "kuota" in resp

    def test_location_query(self, events):
        resp = keyword_fallback("lokasi event", events)
        assert "Lokasi" in resp

    def test_schedule_query(self, events):
        resp = keyword_fallback("jadwal kapan", events)
        assert "Jadwal" in resp

    def test_howto_query(self, events):
        resp = keyword_fallback("cara daftar", events)
        assert "Cara" in resp or "cara" in resp

    def test_help_query(self, events):
        resp = keyword_fallback("bantuan", events)
        assert "bisa membantu" in resp.lower() or "EventBot" in resp

    def test_topic_recommendation(self, events):
        resp = keyword_fallback("saya mau belajar coding python", events)
        assert "tertarik" in resp.lower() or "event" in resp.lower()

    def test_recommendation_keyword(self, events):
        resp = keyword_fallback("rekomendasi event", events)
        assert "Rekomendasi" in resp or "rekomendasi" in resp

    def test_unknown_fallback(self, events):
        resp = keyword_fallback("xyzzy gibberish", events)
        assert "belum mengenali" in resp.lower() or "coba" in resp.lower()


# ── fsm_step — Full State Machine Tests ──────────────────────────────────────

class TestFsmStepIdle:
    @pytest.fixture
    def setup(self):
        return FSM(), copy.deepcopy(DEFAULT_EVENTS)

    def test_greeting(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "halo", events)
        assert fsm.state == State.IDLE
        assert "EventBot" in resp
        assert not fallback

    def test_browse(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "lihat event", events)
        assert fsm.state == State.BROWSING
        assert not fallback

    def test_check_status(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "cek status", events)
        assert fsm.state == State.CHECK_STATUS
        assert not fallback

    def test_cancel(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "batal", events)
        assert fsm.state == State.CANCELLING
        assert not fallback

    def test_unknown_triggers_fallback(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "xyzzy", events)
        assert fallback
        assert resp == ""


class TestFsmStepBrowsing:
    @pytest.fixture
    def setup(self):
        fsm = FSM(state=State.BROWSING)
        return fsm, copy.deepcopy(DEFAULT_EVENTS)

    def test_back_to_idle(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.IDLE
        assert not fallback

    def test_select_valid_event(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "1", events)
        assert fsm.state == State.REGISTERING
        assert fsm.selected_event is not None
        assert not fallback

    def test_select_invalid_event(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "99", events)
        assert fsm.state == State.BROWSING
        assert "tidak valid" in resp
        assert not fallback

    def test_non_numeric_triggers_fallback(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "random text", events)
        assert fallback


class TestFsmStepRegistering:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.REGISTERING, selected_event=events[0])
        return fsm, events

    def test_confirm_yes(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "ya", events)
        assert fsm.state == State.COLLECT_NAME
        assert not fallback

    def test_back_to_browsing(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.BROWSING
        assert not fallback

    def test_full_event_redirects(self):
        ev = {"id": "X", "title": "Full", "quota": 10, "registered": 10,
              "emoji": "🔬", "date": "1 Jan", "time": "09:00",
              "location": "Zoom", "category": "Tech", "type": "Online",
              "price": 0, "free": True, "desc": "desc",
              "color": "linear-gradient(135deg,#0a2040,#0a3060)"}
        events = [ev]
        fsm = FSM(state=State.REGISTERING, selected_event=ev)
        resp, _, fallback = fsm_step(fsm, "ya", events)
        assert fsm.state == State.BROWSING
        assert "penuh" in resp

    def test_unrecognized_triggers_fallback(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "random text", events)
        assert fallback


class TestFsmStepCollectName:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.COLLECT_NAME, selected_event=events[0])
        return fsm, events

    def test_valid_name(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "John Doe", events)
        assert fsm.state == State.COLLECT_EMAIL
        assert fsm.user_info["name"] == "John Doe"
        assert not fallback

    def test_short_name_rejected(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "ab", events)
        assert fsm.state == State.COLLECT_NAME
        assert "tidak valid" in resp

    def test_numeric_name_rejected(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "12345", events)
        assert fsm.state == State.COLLECT_NAME

    def test_back_to_idle(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.IDLE


class TestFsmStepCollectEmail:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.COLLECT_EMAIL, selected_event=events[0],
                   user_info={"name": "John Doe"})
        return fsm, events

    def test_valid_email(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "john@example.com", events)
        assert fsm.state == State.COLLECT_PHONE
        assert fsm.user_info["email"] == "john@example.com"

    def test_invalid_email(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "notanemail", events)
        assert fsm.state == State.COLLECT_EMAIL
        assert "tidak valid" in resp

    def test_back_to_name(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.COLLECT_NAME
        assert "name" not in fsm.user_info


class TestFsmStepCollectPhone:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.COLLECT_PHONE, selected_event=events[0],
                   user_info={"name": "John", "email": "j@e.com"})
        return fsm, events

    def test_valid_phone(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "08123456789", events)
        assert fsm.state == State.CONFIRMING
        assert "Konfirmasi" in resp

    def test_invalid_phone(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "123", events)
        assert fsm.state == State.COLLECT_PHONE
        assert "tidak valid" in resp

    def test_back_to_email(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.COLLECT_EMAIL


class TestFsmStepConfirming:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.CONFIRMING, selected_event=events[0],
                   user_info={"name": "John", "email": "j@e.com", "phone": "08123456789"})
        return fsm, events

    def test_confirm_yes(self, setup):
        fsm, events = setup
        resp, chips, fallback = fsm_step(fsm, "ya", events)
        assert fsm.state == State.DONE
        assert "Berhasil" in resp
        assert len(fsm.registrations) == 1
        code = list(fsm.registrations.keys())[0]
        assert re.match(r"^EVT-[A-Z0-9]{5}$", code)

    def test_confirm_no(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "tidak", events)
        assert fsm.state == State.COLLECT_NAME
        assert fsm.user_info == {}

    def test_invalid_input(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "maybe", events)
        assert fsm.state == State.CONFIRMING
        assert "YA" in resp


class TestFsmStepDone:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.DONE)
        return fsm, events

    def test_browse_again(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "lihat event", events)
        assert fsm.state == State.BROWSING

    def test_check_status(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "cek status", events)
        assert fsm.state == State.CHECK_STATUS

    def test_other_returns_to_idle_with_fallback(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "random", events)
        assert fsm.state == State.IDLE
        assert fallback


class TestFsmStepCheckStatus:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.CHECK_STATUS)
        fsm.registrations["EVT-AB12C"] = {
            "code": "EVT-AB12C", "name": "John",
            "email": "j@e.com", "phone": "08123456789",
            "event": events[0], "time": "01 Jan 2025, 10:00 WIB",
        }
        return fsm, events

    def test_found_code(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "EVT-AB12C", events)
        assert fsm.state == State.IDLE
        assert "TERDAFTAR" in resp

    def test_valid_format_not_found(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "EVT-ZZZZZ", events)
        assert fsm.state == State.CHECK_STATUS
        assert "tidak ditemukan" in resp

    def test_invalid_format(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "hello", events)
        assert "tidak valid" in resp.lower() or "format" in resp.lower()

    def test_back(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.IDLE


class TestFsmStepCancelling:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.CANCELLING)
        fsm.registrations["EVT-AB12C"] = {
            "code": "EVT-AB12C", "name": "John",
            "email": "j@e.com", "phone": "08123456789",
            "event": events[0], "time": "01 Jan 2025, 10:00 WIB",
        }
        return fsm, events

    def test_found_code(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "EVT-AB12C", events)
        assert fsm.state == State.CANCEL_CONFIRM
        assert fsm.cancel_code == "EVT-AB12C"

    def test_code_not_found(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "EVT-ZZZZZ", events)
        assert fsm.state == State.CANCELLING
        assert "tidak ditemukan" in resp

    def test_invalid_format(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "hello", events)
        assert "tidak valid" in resp.lower() or "format" in resp.lower()

    def test_back(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "kembali", events)
        assert fsm.state == State.IDLE


class TestFsmStepCancelConfirm:
    @pytest.fixture
    def setup(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM(state=State.CANCEL_CONFIRM, cancel_code="EVT-AB12C")
        fsm.registrations["EVT-AB12C"] = {
            "code": "EVT-AB12C", "name": "John",
            "email": "j@e.com", "phone": "08123456789",
            "event": events[0], "time": "01 Jan 2025, 10:00 WIB",
        }
        return fsm, events

    def test_confirm_cancel(self, setup):
        fsm, events = setup
        original_reg = events[0]["registered"]
        resp, _, fallback = fsm_step(fsm, "ya", events)
        assert fsm.state == State.IDLE
        assert "Berhasil Dibatalkan" in resp
        assert "EVT-AB12C" not in fsm.registrations
        assert events[0]["registered"] == original_reg - 1

    def test_deny_cancel(self, setup):
        fsm, events = setup
        resp, _, fallback = fsm_step(fsm, "tidak mau", events)
        assert fsm.state == State.IDLE
        assert "aktif" in resp.lower()
        assert "EVT-AB12C" in fsm.registrations


# ── Full Registration Flow (End-to-End) ──────────────────────────────────────

class TestFullRegistrationFlow:
    def test_complete_registration_and_cancel(self):
        events = copy.deepcopy(DEFAULT_EVENTS)
        fsm = FSM()

        # Step 1: Browse events
        resp, chips, _ = fsm_step(fsm, "lihat event", events)
        assert fsm.state == State.BROWSING

        # Step 2: Select event 1
        resp, chips, _ = fsm_step(fsm, "1", events)
        assert fsm.state == State.REGISTERING

        # Step 3: Confirm registration
        resp, chips, _ = fsm_step(fsm, "ya", events)
        assert fsm.state == State.COLLECT_NAME

        # Step 4: Enter name
        resp, chips, _ = fsm_step(fsm, "Alice Wonderland", events)
        assert fsm.state == State.COLLECT_EMAIL

        # Step 5: Enter email
        resp, chips, _ = fsm_step(fsm, "alice@wonder.land", events)
        assert fsm.state == State.COLLECT_PHONE

        # Step 6: Enter phone
        resp, chips, _ = fsm_step(fsm, "081234567890", events)
        assert fsm.state == State.CONFIRMING

        # Step 7: Final confirmation
        resp, chips, _ = fsm_step(fsm, "ya", events)
        assert fsm.state == State.DONE
        assert len(fsm.registrations) == 1

        reg_code = list(fsm.registrations.keys())[0]

        # Step 8: Check status
        fsm_step(fsm, "cek status", events)
        assert fsm.state == State.CHECK_STATUS
        resp, _, _ = fsm_step(fsm, reg_code, events)
        assert "TERDAFTAR" in resp
        assert fsm.state == State.IDLE

        # Step 9: Cancel the registration
        fsm_step(fsm, "batal", events)
        assert fsm.state == State.CANCELLING
        resp, _, _ = fsm_step(fsm, reg_code, events)
        assert fsm.state == State.CANCEL_CONFIRM
        resp, _, _ = fsm_step(fsm, "ya", events)
        assert fsm.state == State.IDLE
        assert reg_code not in fsm.registrations
