"""Streaming download support shared by the sync and async responses.

The response body is consumed once, in chunks, into a
:class:`tempfile.SpooledTemporaryFile`. Small bodies stay in memory, large
ones roll over to disk, so a multi-gigabyte download never has to fit in
RAM. Every download assertion then re-reads that spool chunk by chunk, which
lets assertions be chained freely::

    with client.get('/export.csv').stream() as response:
        response.assert_status(200) \\
                .assert_content_type('text/csv') \\
                .assert_attachment(filename='export.csv') \\
                .assert_body_size(min_bytes=1) \\
                .assert_checksum('sha256', expected) \\
                .save_to('out/export.csv')
"""

import hashlib
import os
import re
import tempfile
from typing import IO, Any, Iterator, Optional, Union
from urllib.parse import unquote

DEFAULT_CHUNK_SIZE = 64 * 1024
#: Bodies up to this size are spooled in memory, larger ones go to a temp file.
SPOOL_MAX_MEMORY = 10 * 1024 * 1024

PathLike = Union[str, "os.PathLike[str]"]


def new_spool() -> IO[bytes]:
    return tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_MEMORY, mode="w+b")


def parse_content_disposition(value: str) -> tuple:
    """Return ``(disposition_type, filename)`` from a Content-Disposition header.

    ``filename*`` (RFC 6266 / RFC 5987, e.g. ``UTF-8''na%C3%AFve.txt``) takes
    precedence over plain ``filename``. ``filename`` is ``None`` when absent.
    """
    parts = [p.strip() for p in value.split(";")]
    disposition = parts[0].lower() if parts else ""
    plain: Optional[str] = None
    extended: Optional[str] = None
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, _, raw = part.partition("=")
        key = key.strip().lower()
        raw = raw.strip()
        if key == "filename*":
            match = re.match(r"^([\w!#$%&+^`{}~-]*)'[\w-]*'(.*)$", raw)
            if match:
                charset = match.group(1) or "utf-8"
                try:
                    extended = unquote(match.group(2), encoding=charset)
                except LookupError:
                    extended = unquote(match.group(2))
        elif key == "filename":
            if len(raw) >= 2 and raw[0] == raw[-1] == '"':
                raw = raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            plain = raw
    return disposition, extended if extended is not None else plain


class DownloadMixin:
    """Download helpers and assertions.

    Subclasses provide ``headers`` and implement :meth:`_body_spool`, which
    must return a seekable binary file holding the complete body.
    """

    headers: Any

    # ── to implement ──────────────────────────────────────────────────────────

    def _body_spool(self) -> IO[bytes]:  # pragma: no cover - abstract
        raise NotImplementedError

    # ── helpers ───────────────────────────────────────────────────────────────

    def _header(self, name: str) -> Optional[str]:
        value = self.headers.get(name)
        if value is not None:
            return value
        lowered = name.lower()
        for key, val in self.headers.items():
            if key.lower() == lowered:
                return val
        return None

    def _iter_spool(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        spool = self._body_spool()
        spool.seek(0)
        while True:
            chunk = spool.read(chunk_size)
            if not chunk:
                break
            yield chunk

    @property
    def content(self) -> bytes:
        """The full response body as bytes.

        Loads the whole body into memory. For large downloads prefer
        :meth:`iter_bytes`, :meth:`save_to` or the download assertions.
        """
        spool = self._body_spool()
        spool.seek(0)
        return spool.read()

    @property
    def body_size(self) -> int:
        """Size of the (decoded) response body in bytes."""
        spool = self._body_spool()
        spool.seek(0, os.SEEK_END)
        return spool.tell()

    def iter_bytes(self, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[bytes]:
        """Iterate over the response body in chunks of at most *chunk_size* bytes."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        return self._iter_spool(chunk_size)

    def checksum(self, algorithm: str = "sha256") -> str:
        """Return the hex digest of the body using a :mod:`hashlib` *algorithm*."""
        try:
            digest = hashlib.new(algorithm.lower())
        except ValueError:
            raise ValueError(f"Unsupported hash algorithm: '{algorithm}'")
        for chunk in self._iter_spool():
            digest.update(chunk)
        return digest.hexdigest()

    @property
    def filename(self) -> Optional[str]:
        """Filename advertised by the Content-Disposition header, if any."""
        header = self._header("Content-Disposition")
        if not header:
            return None
        return parse_content_disposition(header)[1]

    def save_to(self, path: PathLike, *, make_dirs: bool = True) -> Any:
        """Write the body to *path*, chunk by chunk.

        Args:
            path: Destination file path. If it is an existing directory, the
                file is saved inside it under the Content-Disposition filename.
            make_dirs: Create missing parent directories. Defaults to ``True``.

        Returns:
            The current response for chaining.
        """
        target = os.fspath(path)
        if os.path.isdir(target):
            name = self.filename
            if not name:
                raise ValueError(
                    f"'{target}' is a directory and the response has no "
                    "Content-Disposition filename to save under"
                )
            target = os.path.join(target, os.path.basename(name))
        parent = os.path.dirname(target)
        if make_dirs and parent:
            os.makedirs(parent, exist_ok=True)
        with open(target, "wb") as fh:
            for chunk in self._iter_spool():
                fh.write(chunk)
        return self

    # ── assertions ────────────────────────────────────────────────────────────

    def assert_content_type(self, expected: str) -> Any:
        """Assert the media type of the Content-Type header, ignoring parameters.

        ``assert_content_type('text/csv')`` passes for ``text/csv; charset=utf-8``.
        Pass parameters explicitly to compare the full header value.
        """
        __tracebackhide__ = True
        actual = self._header("Content-Type")
        assert actual is not None, "Expected header 'Content-Type' to be present but it was not found"
        if ";" in expected:
            norm = lambda v: ";".join(p.strip().lower() for p in v.split(";"))
            assert norm(actual) == norm(expected), \
                f"Expected Content-Type '{expected}', got '{actual}'"
        else:
            media_type = actual.split(";", 1)[0].strip().lower()
            assert media_type == expected.strip().lower(), \
                f"Expected Content-Type '{expected}', got '{actual}'"
        return self

    def assert_attachment(self, filename: Optional[str] = None) -> Any:
        """Assert the response is served as a download (``Content-Disposition: attachment``).

        Args:
            filename: If given, the advertised filename must match exactly.
                ``filename*`` (RFC 5987 encoded) is decoded before comparing.
        """
        __tracebackhide__ = True
        header = self._header("Content-Disposition")
        assert header is not None, \
            "Expected header 'Content-Disposition' to be present but it was not found"
        disposition, actual_name = parse_content_disposition(header)
        assert disposition == "attachment", \
            f"Expected Content-Disposition 'attachment', got '{disposition}'"
        if filename is not None:
            assert actual_name == filename, \
                f"Expected attachment filename '{filename}', got '{actual_name}'"
        return self

    def assert_body_size(
        self,
        equals: Optional[int] = None,
        *,
        min_bytes: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ) -> Any:
        """Assert the size of the body in bytes.

        Args:
            equals: Exact expected size.
            min_bytes: Inclusive lower bound.
            max_bytes: Inclusive upper bound.
        """
        __tracebackhide__ = True
        if equals is None and min_bytes is None and max_bytes is None:
            raise ValueError("Provide at least one of equals, min_bytes or max_bytes")
        size = self.body_size
        if equals is not None:
            assert size == equals, f"Expected body size {equals} bytes, got {size} bytes"
        if min_bytes is not None:
            assert size >= min_bytes, f"Expected body size >= {min_bytes} bytes, got {size} bytes"
        if max_bytes is not None:
            assert size <= max_bytes, f"Expected body size <= {max_bytes} bytes, got {size} bytes"
        return self

    def assert_content_length(self) -> Any:
        """Assert the received body matches the Content-Length header.

        Catches truncated or padded downloads. Skipped comparisons are not
        silent: if the body was content-encoded (gzip, br, ...) the header
        describes the compressed size, so this raises an AssertionError
        explaining why it cannot be checked.
        """
        __tracebackhide__ = True
        header = self._header("Content-Length")
        assert header is not None, "Expected header 'Content-Length' to be present but it was not found"
        encoding = (self._header("Content-Encoding") or "identity").strip().lower()
        assert encoding == "identity", (
            f"Cannot compare Content-Length with the body: it is '{encoding}'-encoded "
            "and Content-Length counts the encoded bytes"
        )
        expected = int(header)
        size = self.body_size
        assert size == expected, \
            f"Content-Length says {expected} bytes but {size} bytes were received"
        return self

    def assert_checksum(self, algorithm: str, expected: str) -> Any:
        """Assert the hex digest of the body, e.g. ``assert_checksum('sha256', '9f86...')``.

        The comparison is case-insensitive. Any :mod:`hashlib` algorithm works.
        """
        __tracebackhide__ = True
        actual = self.checksum(algorithm)
        assert actual == expected.strip().lower(), \
            f"Expected {algorithm} checksum '{expected}', got '{actual}'"
        return self

    def assert_body_equals_file(self, path: PathLike) -> Any:
        """Assert the body is byte-for-byte identical to the file at *path*.

        Compared chunk by chunk, so neither side is loaded fully into memory.
        """
        __tracebackhide__ = True
        expected_size = os.path.getsize(path)
        size = self.body_size
        assert size == expected_size, \
            f"Expected body to match '{path}' ({expected_size} bytes), got {size} bytes"
        offset = 0
        with open(path, "rb") as fh:
            for chunk in self._iter_spool():
                expected_chunk = fh.read(len(chunk))
                if chunk != expected_chunk:
                    for i, (a, b) in enumerate(zip(chunk, expected_chunk)):
                        if a != b:
                            offset += i
                            break
                    raise AssertionError(
                        f"Expected body to match '{path}', first difference at byte {offset}"
                    )
                offset += len(chunk)
        return self
