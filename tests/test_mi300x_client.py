import httpx
import pytest

import recap.inference.mi300x_client as client


class _FakeResp:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            req = httpx.Request("POST", "http://x")
            raise httpx.HTTPStatusError("err", request=req, response=httpx.Response(self.status_code))

    def json(self):
        return self._json


def test_raises_when_url_unset(monkeypatch):
    monkeypatch.delenv("RECAP_MI300X_URL", raising=False)
    with pytest.raises(RuntimeError, match="RECAP_MI300X_URL"):
        client._post("medgemma", "sys", "user")


def test_posts_to_correct_url(monkeypatch):
    monkeypatch.setenv("RECAP_MI300X_URL", "https://example.test")
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"] = url
        seen["json"] = json
        return _FakeResp(200, {"text": "hello"})

    monkeypatch.setattr(client.httpx, "post", fake_post)
    out = client._post("qwen", "sys-prompt", "user-prompt")
    assert out == "hello"
    assert seen["url"] == "https://example.test/qwen"
    assert seen["json"] == {"system": "sys-prompt", "user": "user-prompt"}


def test_retries_on_transport_errors(monkeypatch):
    monkeypatch.setenv("RECAP_MI300X_URL", "https://example.test")
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)
    calls = {"n": 0}

    def flaky_post(url, json, timeout):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("boom")
        return _FakeResp(200, {"text": "ok"})

    monkeypatch.setattr(client.httpx, "post", flaky_post)
    out = client._post("medgemma", "s", "u")
    assert out == "ok"
    assert calls["n"] == 3


def test_gives_up_after_three_attempts(monkeypatch):
    monkeypatch.setenv("RECAP_MI300X_URL", "https://example.test")
    monkeypatch.setattr(client.time, "sleep", lambda *_: None)
    calls = {"n": 0}

    def always_fail(url, json, timeout):
        calls["n"] += 1
        raise httpx.ConnectError("down")

    monkeypatch.setattr(client.httpx, "post", always_fail)
    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        client._post("medgemma", "s", "u")
    assert calls["n"] == 3


def test_strips_trailing_slash_from_url(monkeypatch):
    monkeypatch.setenv("RECAP_MI300X_URL", "https://example.test/")
    seen = {}

    def fake_post(url, json, timeout):
        seen["url"] = url
        return _FakeResp(200, {"text": ""})

    monkeypatch.setattr(client.httpx, "post", fake_post)
    client._post("qwen", "s", "u")
    assert seen["url"] == "https://example.test/qwen"
