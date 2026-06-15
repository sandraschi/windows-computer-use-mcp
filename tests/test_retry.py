"""Tests for retry helper."""

import pytest

from windows_computer_use_mcp.retry import with_retry


def test_with_retry_succeeds_second_attempt():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("nope")
        return "ok"

    assert with_retry(flaky, attempts=3, delay=0.01, label="test") == "ok"
    assert calls["n"] == 2


def test_with_retry_raises_after_exhausted():
    def always_fail():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        with_retry(always_fail, attempts=2, delay=0.01, label="test")
