"""Polling / wait-until utility for eventually-consistent APIs."""

import time
from typing import Callable, Optional, Any, TypeVar

T = TypeVar("T")


class PollingTimeoutError(Exception):
    """Raised when *wait_until* exhausts its timeout without the condition becoming true."""

    def __init__(self, timeout: float, last_value: Any = None, message: Optional[str] = None) -> None:
        self.timeout = timeout
        self.last_value = last_value
        if message:
            super().__init__(message)
        else:
            super().__init__(
                f"Condition not met within {timeout} seconds. "
                f"Last value: {last_value!r}"
            )


def wait_until(
    condition: Callable[[], T],
    *,
    timeout: float = 30.0,
    interval: float = 1.0,
    raises: bool = True,
    description: Optional[str] = None,
) -> Optional[T]:
    """Poll *condition* repeatedly until it returns a truthy value.

    Designed for eventually-consistent APIs where a resource may not be
    immediately available after creation.

    Args:
        condition: A zero-argument callable.  It is called every
            *interval* seconds.  The first truthy return value is
            returned from ``wait_until``.  Exceptions raised by
            *condition* are **not** caught — they propagate immediately.
        timeout: Maximum number of seconds to wait. Defaults to ``30``.
        interval: Seconds to sleep between attempts. Defaults to ``1``.
        raises: If ``True`` (default) raise :class:`PollingTimeoutError`
            when *timeout* elapses.  If ``False`` return ``None``
            instead.
        description: Optional human-readable label used in the timeout
            error message.

    Returns:
        The first truthy value returned by *condition*, or ``None`` if
        *raises* is ``False`` and the timeout elapses.

    Raises:
        PollingTimeoutError: If *raises* is ``True`` and the condition is
            not satisfied within *timeout* seconds.

    Example::

        from lashtest import APIClient
        from lashtest.utils.polling import wait_until

        client = APIClient('https://api.example.com')

        def job_is_done():
            with client.get('/jobs/42') as r:
                return r.json().get('status') == 'done'

        wait_until(job_is_done, timeout=60, interval=2)
    """
    deadline = time.monotonic() + timeout
    last_value: Any = None

    while True:
        last_value = condition()
        if last_value:
            return last_value

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        time.sleep(min(interval, remaining))

    if raises:
        parts = []
        if description:
            parts.append(description)
        parts.append(f"Condition not met within {timeout} seconds")
        raise PollingTimeoutError(timeout, last_value, " — ".join(parts) if description else None)

    return None
