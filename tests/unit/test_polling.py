"""Unit tests for lashtest.utils.polling.wait_until."""

import time
import pytest
from unittest.mock import patch
from lashtest.utils.polling import wait_until, PollingTimeoutError


class TestWaitUntil:

    def test_returns_truthy_value_immediately(self):
        result = wait_until(lambda: 42, timeout=5, interval=0.1)
        assert result == 42

    def test_returns_true_on_first_call(self):
        result = wait_until(lambda: True, timeout=5)
        assert result is True

    def test_waits_until_condition_becomes_true(self):
        calls = [False, False, True]
        idx = iter(calls)
        result = wait_until(lambda: next(idx), timeout=5, interval=0.01)
        assert result is True

    def test_raises_polling_timeout_error_when_raises_is_true(self):
        with pytest.raises(PollingTimeoutError):
            wait_until(lambda: False, timeout=0.05, interval=0.01, raises=True)

    def test_returns_none_when_raises_is_false_and_timeout_elapses(self):
        result = wait_until(lambda: False, timeout=0.05, interval=0.01, raises=False)
        assert result is None

    def test_timeout_error_contains_timeout_value(self):
        with pytest.raises(PollingTimeoutError) as exc_info:
            wait_until(lambda: False, timeout=0.05, interval=0.01)
        assert exc_info.value.timeout == pytest.approx(0.05, abs=0.01)

    def test_timeout_error_contains_last_value(self):
        with pytest.raises(PollingTimeoutError) as exc_info:
            wait_until(lambda: 0, timeout=0.05, interval=0.01)
        assert exc_info.value.last_value == 0

    def test_description_included_in_timeout_error(self):
        with pytest.raises(PollingTimeoutError, match="job not done"):
            wait_until(lambda: False, timeout=0.05, interval=0.01, description="job not done")

    def test_condition_exceptions_propagate(self):
        def boom():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            wait_until(boom, timeout=5, interval=0.01)

    def test_truthy_string_is_accepted(self):
        result = wait_until(lambda: "ready", timeout=5)
        assert result == "ready"

    def test_truthy_dict_is_accepted(self):
        result = wait_until(lambda: {"status": "done"}, timeout=5)
        assert result == {"status": "done"}

    def test_falsy_values_keep_polling(self):
        counter = [0]
        def condition():
            counter[0] += 1
            if counter[0] >= 3:
                return "ok"
            return None  # falsy

        result = wait_until(condition, timeout=5, interval=0.01)
        assert result == "ok"
        assert counter[0] == 3

    @patch("time.sleep")
    def test_respects_interval(self, mock_sleep):
        calls = iter([False, True])
        wait_until(lambda: next(calls), timeout=5, interval=0.5)
        mock_sleep.assert_called_once_with(0.5)


class TestPollingTimeoutError:

    def test_is_exception(self):
        err = PollingTimeoutError(30, None)
        assert isinstance(err, Exception)

    def test_stores_timeout(self):
        err = PollingTimeoutError(15, "last")
        assert err.timeout == 15

    def test_stores_last_value(self):
        err = PollingTimeoutError(30, {"status": "pending"})
        assert err.last_value == {"status": "pending"}

    def test_message_contains_timeout(self):
        err = PollingTimeoutError(10, None)
        assert "10" in str(err)
