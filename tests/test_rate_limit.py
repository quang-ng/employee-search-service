import asyncio

import pytest
from fastapi import HTTPException

from app.middleware import rate_limit


class DummyRequest:
    def __init__(self, host):
        self.client = type('client', (), {'host': host})


class DummyUser:
    def __init__(self, user_id):
        self.id = user_id


def test_get_rate_limit_key_with_user():
    request = DummyRequest('127.0.0.1')
    user = DummyUser(42)
    key = rate_limit.get_rate_limit_key(request, user)
    assert key == 'user:42'


def test_get_rate_limit_key_without_user():
    request = DummyRequest('192.168.1.1')
    key = rate_limit.get_rate_limit_key(request, None)
    assert key == 'ip:192.168.1.1'


def test_is_allowed_under_limit():
    key = 'test_key_under_limit'
    limiter = rate_limit.InProcessRateLimiter()
    for _ in range(rate_limit.RATE_LIMIT):
        assert limiter.is_allowed(key)
    # Next request should be blocked
    assert not limiter.is_allowed(key)


def test_is_allowed_after_period(monkeypatch):
    key = 'test_key_period'
    limiter = rate_limit.InProcessRateLimiter()
    times = [100.0 + i for i in range(rate_limit.RATE_LIMIT)]
    monkeypatch.setattr(rate_limit.time, 'monotonic', lambda: times.pop(0) if times else 200.0)
    for _ in range(rate_limit.RATE_LIMIT):
        assert limiter.is_allowed(key)
    # Simulate time passing beyond RATE_PERIOD
    assert limiter.is_allowed(key)


def test_rate_limiter_allows(monkeypatch):
    request = DummyRequest('10.0.0.1')
    user = DummyUser(1)
    # Patch is_allowed to always return True
    monkeypatch.setattr(rate_limit.rate_limiter_instance, 'is_allowed', lambda key: True)
    # Should not raise
    asyncio.run(rate_limit.rate_limiter(request, user))


def test_rate_limiter_blocks(monkeypatch):
    request = DummyRequest('10.0.0.2')
    user = DummyUser(2)
    # Patch is_allowed to always return False
    monkeypatch.setattr(rate_limit.rate_limiter_instance, 'is_allowed', lambda key: False)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(rate_limit.rate_limiter(request, user))
    assert exc.value.status_code == 429
    assert "Rate limit exceeded" in exc.value.detail
