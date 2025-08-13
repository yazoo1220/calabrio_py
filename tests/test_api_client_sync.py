import types
import json
from calabrio_py.api import ApiClient


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"Result": [], "Errors": []}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_authorization_header_and_url_join(monkeypatch):
    calls = {}

    def fake_request(method, url, **kwargs):
        calls["method"] = method
        calls["url"] = url
        calls["headers"] = kwargs.get("headers", {})
        calls["json"] = kwargs.get("json")
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr("requests.request", fake_request)

    client = ApiClient("https://example.com/api", "TEST_TOKEN")
    res = client.get_all_business_units()

    assert isinstance(res, dict)
    assert res.get("ok") is True
    assert calls["method"] == "POST"
    assert calls["url"] == "https://example.com/api/query/BusinessUnit/AllBusinessUnits"
    assert calls["headers"].get("Authorization") == "Bearer TEST_TOKEN"


def test_no_double_base_url_when_absolute_passed(monkeypatch):
    calls = {}

    def fake_request(method, url, **kwargs):
        calls["url"] = url
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr("requests.request", fake_request)

    client = ApiClient("https://example.com/api", "TEST_TOKEN")
    # 明示的に絶対URLを渡しても二重結合されないこと
    res = client.post("https://example.com/api/command/AddTeam", data={})
    assert res.get("ok") is True
    assert calls["url"] == "https://example.com/api/command/AddTeam"


def test_get_schedules_by_change_date_returns_dict(monkeypatch):
    def fake_request(method, url, **kwargs):
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr("requests.request", fake_request)

    client = ApiClient("https://example.com/api", "TEST_TOKEN")
    res = client.get_schedules_by_change_date(
        changes_from="2025-01-01T00:00:00Z",
        changes_to="2025-01-02T00:00:00Z",
        page=1,
        page_size=10,
    )
    assert isinstance(res, dict)
    assert res.get("ok") is True


def test_add_person_accepts_dict(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["json"] = kwargs.get("json")
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr("requests.request", fake_request)
    client = ApiClient("https://example.com/api", "TEST_TOKEN")
    payload = {"TimeZoneId": "UTC", "BusinessUnitId": "BU1", "FirstName": "A", "LastName": "B"}
    res = client.add_person(payload)
    assert res.get("ok") is True
    assert captured["json"] == payload


