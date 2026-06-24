"""Tests for fsm.py — data helpers, State enum, FSM dataclass, and metadata."""

import pytest
from fsm import (
    APP_NAME, APP_TAGLINE, APP_VERSION,
    STATS, FEATURES, STEPS, FAQ, DEFAULT_EVENTS,
    get_event_by_id, get_event_by_index,
    format_price, quota_pct, is_full,
    State, FSM, STATE_META,
)


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_app_metadata(self):
        assert APP_NAME == "EventBot"
        assert APP_TAGLINE == "Platform Manajemen Event & Konferensi"
        assert APP_VERSION == "1.0.0"

    def test_stats_structure(self):
        assert len(STATS) == 4
        for s in STATS:
            assert "num" in s and "label" in s

    def test_features_structure(self):
        assert len(FEATURES) == 6
        for f in FEATURES:
            assert {"icon", "color", "title", "desc"} <= set(f)

    def test_steps_structure(self):
        assert len(STEPS) == 5
        for s in STEPS:
            assert {"num", "icon", "label", "desc"} <= set(s)

    def test_faq_structure(self):
        assert len(FAQ) == 4
        for item in FAQ:
            assert "q" in item and "a" in item

    def test_default_events_count(self):
        assert len(DEFAULT_EVENTS) == 6

    def test_default_events_fields(self):
        required = {"id", "emoji", "title", "category", "date", "time",
                     "location", "type", "price", "quota", "registered",
                     "free", "desc", "color"}
        for ev in DEFAULT_EVENTS:
            assert required <= set(ev), f"Event {ev.get('id')} missing fields"

    def test_default_events_unique_ids(self):
        ids = [e["id"] for e in DEFAULT_EVENTS]
        assert len(ids) == len(set(ids))


# ── get_event_by_id ──────────────────────────────────────────────────────────

class TestGetEventById:
    @pytest.fixture
    def events(self):
        return [
            {"id": "EVT001", "title": "Event A"},
            {"id": "EVT002", "title": "Event B"},
            {"id": "EVT003", "title": "Event C"},
        ]

    def test_found(self, events):
        assert get_event_by_id(events, "EVT002")["title"] == "Event B"

    def test_not_found(self, events):
        assert get_event_by_id(events, "EVT999") is None

    def test_empty_list(self):
        assert get_event_by_id([], "EVT001") is None

    def test_case_sensitive(self, events):
        assert get_event_by_id(events, "evt001") is None


# ── get_event_by_index ───────────────────────────────────────────────────────

class TestGetEventByIndex:
    @pytest.fixture
    def events(self):
        return [
            {"id": "EVT001", "title": "First"},
            {"id": "EVT002", "title": "Second"},
        ]

    def test_first_element(self, events):
        assert get_event_by_index(events, 1)["title"] == "First"

    def test_last_element(self, events):
        assert get_event_by_index(events, 2)["title"] == "Second"

    def test_out_of_range(self, events):
        assert get_event_by_index(events, 10) is None

    def test_zero_index(self, events):
        # idx=0 → events[-1] which is valid Python, but semantically idx 0 is invalid.
        # The function doesn't guard against this, so it returns last element.
        result = get_event_by_index(events, 0)
        assert result is not None  # documents current behavior

    def test_negative_index(self, events):
        # Negative indices wrap in Python; documenting current behavior.
        result = get_event_by_index(events, -1)
        assert result is not None

    def test_empty_list(self):
        assert get_event_by_index([], 1) is None


# ── format_price ─────────────────────────────────────────────────────────────

class TestFormatPrice:
    def test_free(self):
        assert format_price(0) == "GRATIS"

    def test_small_price(self):
        assert format_price(500) == "Rp 500"

    def test_thousands(self):
        assert format_price(75_000) == "Rp 75.000"

    def test_hundreds_of_thousands(self):
        assert format_price(150_000) == "Rp 150.000"

    def test_millions(self):
        assert format_price(1_500_000) == "Rp 1.500.000"


# ── quota_pct ────────────────────────────────────────────────────────────────

class TestQuotaPct:
    def test_half_full(self):
        assert quota_pct({"registered": 50, "quota": 100}) == 50

    def test_completely_full(self):
        assert quota_pct({"registered": 100, "quota": 100}) == 100

    def test_empty(self):
        assert quota_pct({"registered": 0, "quota": 100}) == 0

    def test_zero_quota(self):
        assert quota_pct({"registered": 0, "quota": 0}) == 0

    def test_rounding(self):
        assert quota_pct({"registered": 1, "quota": 3}) == 33

    def test_over_capacity(self):
        # Edge case: registered > quota
        assert quota_pct({"registered": 120, "quota": 100}) == 120


# ── is_full ──────────────────────────────────────────────────────────────────

class TestIsFull:
    def test_not_full(self):
        assert is_full({"registered": 50, "quota": 100}) is False

    def test_exactly_full(self):
        assert is_full({"registered": 100, "quota": 100}) is True

    def test_over_capacity(self):
        assert is_full({"registered": 101, "quota": 100}) is True

    def test_empty_event(self):
        assert is_full({"registered": 0, "quota": 100}) is False


# ── State Enum ───────────────────────────────────────────────────────────────

class TestStateEnum:
    def test_all_states_exist(self):
        expected = {
            "IDLE", "BROWSING", "REGISTERING", "COLLECT_NAME",
            "COLLECT_EMAIL", "COLLECT_PHONE", "CONFIRMING", "DONE",
            "CHECK_STATUS", "CANCELLING", "CANCEL_CONFIRM",
        }
        actual = {s.value for s in State}
        assert actual == expected

    def test_state_is_string(self):
        assert isinstance(State.IDLE, str)
        assert State.IDLE == "IDLE"

    def test_state_count(self):
        assert len(State) == 11


# ── FSM Dataclass ────────────────────────────────────────────────────────────

class TestFSMDataclass:
    def test_default_state(self):
        fsm = FSM()
        assert fsm.state == State.IDLE

    def test_default_selected_event(self):
        fsm = FSM()
        assert fsm.selected_event is None

    def test_default_user_info(self):
        fsm = FSM()
        assert fsm.user_info == {}

    def test_default_registrations(self):
        fsm = FSM()
        assert fsm.registrations == {}

    def test_default_cancel_code(self):
        fsm = FSM()
        assert fsm.cancel_code == ""

    def test_mutable_defaults_independent(self):
        fsm1 = FSM()
        fsm2 = FSM()
        fsm1.user_info["name"] = "Alice"
        assert fsm2.user_info == {}

    def test_set_state(self):
        fsm = FSM()
        fsm.state = State.BROWSING
        assert fsm.state == State.BROWSING


# ── STATE_META ───────────────────────────────────────────────────────────────

class TestStateMeta:
    def test_all_states_have_meta(self):
        for state in State:
            assert state in STATE_META, f"{state} missing from STATE_META"

    def test_meta_structure(self):
        for state, (emoji, color) in STATE_META.items():
            assert isinstance(emoji, str) and len(emoji) > 0
            assert isinstance(color, str) and color.startswith("#")
