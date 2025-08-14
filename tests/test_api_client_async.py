import asyncio
import types
import pytest
from calabrio_py.api import AsyncApiClient


class DummyAiohttpResponse:
    def __init__(self, status=200, payload=None):
        self.status = status
        self._payload = payload or {"Result": []}  # Errorsキー無しでも動作すること

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")

    async def json(self):
        return self._payload


class DummyAiohttpSession:
    def __init__(self, headers=None):
        self.headers = headers or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, **kwargs):
        return DummyAiohttpResponse(200, {"ok": True})


@pytest.mark.asyncio
async def test_async_make_request_handles_missing_errors(monkeypatch):
    monkeypatch.setattr("aiohttp.ClientSession", lambda headers=None: DummyAiohttpSession(headers))
    client = AsyncApiClient("https://example.com/api", "TEST_TOKEN")
    res = await client.get_all_business_units()
    assert isinstance(res, dict)
    assert res.get("ok") is True


