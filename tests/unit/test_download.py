"""Tests for streaming file downloads (Request.stream() and download assertions).

A real local HTTP server is used so the actual streaming path of
``requests`` / ``httpx`` is exercised end to end.
"""

import asyncio
import hashlib
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest

from lashtest import APIClient
from lashtest.core import download
from lashtest.core.download import parse_content_disposition
from lashtest.core.exceptions import APIConnectionError
from lashtest.core.request import Request


PAYLOAD = os.urandom(300 * 1024 + 7)  # not a multiple of any chunk size
PAYLOAD_SHA256 = hashlib.sha256(PAYLOAD).hexdigest()
CSV = b"id,name\n1,ada\n2,linus\n"


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output quiet
        pass

    def _send(self, status, headers, body):
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/file.bin":
            self._send(200, {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(PAYLOAD)),
                "Content-Disposition": 'attachment; filename="file.bin"',
            }, PAYLOAD)
        elif path == "/chunked":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            for i in range(0, len(PAYLOAD), 50_000):
                part = PAYLOAD[i:i + 50_000]
                self.wfile.write(f"{len(part):x}\r\n".encode() + part + b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        elif path == "/export.csv":
            self._send(200, {
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Length": str(len(CSV)),
                "Content-Disposition": "attachment; filename=\"export.csv\"; "
                                       "filename*=UTF-8''r%C3%A9sum%C3%A9.csv",
            }, CSV)
        elif path == "/inline":
            self._send(200, {
                "Content-Type": "application/json",
                "Content-Length": "12",
                "Content-Disposition": "inline",
            }, b'{"ok": true}')
        elif path == "/truncated":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD[:1000])
            self.wfile.flush()
            self.close_connection = True
        elif path == "/flaky":
            self.server.flaky_hits += 1
            if self.server.flaky_hits == 1:
                self._send(503, {"Content-Length": "0"}, b"")
            else:
                self._send(200, {"Content-Length": str(len(CSV))}, CSV)
        else:
            self._send(404, {"Content-Length": "0"}, b"")


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # Tests that only read headers close the stream early on purpose;
        # the resulting connection resets are expected.
        pass


@pytest.fixture(scope="module")
def server_url():
    server = _Server(("127.0.0.1", 0), _Handler)
    server.flaky_hits = 0
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture
def client(server_url):
    c = APIClient(server_url)
    yield c
    c.close()


# ── Content-Disposition parsing ───────────────────────────────────────────────

class TestParseContentDisposition:

    def test_quoted_filename(self):
        assert parse_content_disposition('attachment; filename="a b.txt"') == ("attachment", "a b.txt")

    def test_unquoted_filename(self):
        assert parse_content_disposition("attachment; filename=report.pdf") == ("attachment", "report.pdf")

    def test_extended_filename_wins(self):
        value = "attachment; filename=\"fallback.txt\"; filename*=UTF-8''na%C3%AFve.txt"
        assert parse_content_disposition(value) == ("attachment", "naïve.txt")

    def test_no_filename(self):
        assert parse_content_disposition("inline") == ("inline", None)

    def test_type_is_case_insensitive(self):
        assert parse_content_disposition("ATTACHMENT; filename=x")[0] == "attachment"

    def test_escaped_quote(self):
        assert parse_content_disposition(r'attachment; filename="say \"hi\".txt"')[1] == 'say "hi".txt'


# ── Request.stream() ──────────────────────────────────────────────────────────

class TestRequestStream:

    def _request(self):
        client = MagicMock()
        client.timeout = 30
        return Request(client, "GET", "/x")

    def test_defaults_to_not_streaming(self):
        assert self._request().stream_response is False

    def test_stream_sets_flag_and_chunk_size(self):
        r = self._request().stream(chunk_size=1024)
        assert r.stream_response is True
        assert r.chunk_size == 1024

    def test_stream_returns_self(self):
        r = self._request()
        assert r.stream() is r

    @pytest.mark.parametrize("bad", [0, -1, 1.5, "10"])
    def test_rejects_invalid_chunk_size(self, bad):
        with pytest.raises(ValueError):
            self._request().stream(chunk_size=bad)


# ── end-to-end sync streaming ─────────────────────────────────────────────────

class TestStreamedDownload:

    def test_body_is_not_read_until_needed(self, client):
        with client.get("/file.bin").stream() as response:
            assert response.streamed is True
            assert response._spool is None
            assert response.body_size == len(PAYLOAD)
            assert response._spool is not None

    def test_full_chain(self, client, tmp_path):
        target = tmp_path / "nested" / "out.bin"
        with client.get("/file.bin").stream(chunk_size=4096) as response:
            response.assert_status(200) \
                    .assert_content_type("application/octet-stream") \
                    .assert_attachment(filename="file.bin") \
                    .assert_content_length() \
                    .assert_body_size(len(PAYLOAD)) \
                    .assert_body_size(min_bytes=1, max_bytes=len(PAYLOAD)) \
                    .assert_checksum("sha256", PAYLOAD_SHA256) \
                    .assert_checksum("MD5", hashlib.md5(PAYLOAD).hexdigest().upper()) \
                    .save_to(target)
        assert target.read_bytes() == PAYLOAD

    def test_chunked_transfer(self, client):
        with client.get("/chunked").stream() as response:
            response.assert_checksum("sha256", PAYLOAD_SHA256)
            assert response.body_size == len(PAYLOAD)

    def test_iter_bytes_respects_chunk_size(self, client):
        with client.get("/file.bin").stream() as response:
            chunks = list(response.iter_bytes(chunk_size=10_000))
        assert b"".join(chunks) == PAYLOAD
        assert max(len(c) for c in chunks) <= 10_000

    def test_iter_bytes_can_be_repeated(self, client):
        with client.get("/file.bin").stream() as response:
            assert b"".join(response.iter_bytes()) == b"".join(response.iter_bytes())

    def test_iter_bytes_rejects_bad_chunk_size(self, client):
        with client.get("/file.bin").stream() as response:
            with pytest.raises(ValueError):
                response.iter_bytes(0)

    def test_content_and_text_and_json_work_when_streamed(self, client):
        with client.get("/export.csv").stream() as response:
            assert response.content == CSV
            assert response.text == CSV.decode()
        with client.get("/inline").stream() as response:
            assert response.json() == {"ok": True}

    def test_save_to_directory_uses_attachment_filename(self, client, tmp_path):
        with client.get("/export.csv").stream() as response:
            response.save_to(tmp_path)
        assert (tmp_path / "résumé.csv").read_bytes() == CSV

    def test_save_to_directory_without_filename_fails(self, client, tmp_path):
        with client.get("/inline").stream() as response:
            with pytest.raises(ValueError, match="no Content-Disposition filename"):
                response.save_to(tmp_path)

    def test_assert_body_equals_file(self, client, tmp_path):
        same = tmp_path / "same.bin"
        same.write_bytes(PAYLOAD)
        different = tmp_path / "different.bin"
        different.write_bytes(PAYLOAD[:5000] + b"\x00" + PAYLOAD[5001:]
                              if PAYLOAD[5000] != 0 else PAYLOAD[:5000] + b"\x01" + PAYLOAD[5001:])
        shorter = tmp_path / "short.bin"
        shorter.write_bytes(PAYLOAD[:10])
        with client.get("/file.bin").stream() as response:
            response.assert_body_equals_file(same)
            with pytest.raises(AssertionError, match="first difference at byte 5000"):
                response.assert_body_equals_file(different)
            with pytest.raises(AssertionError, match="10 bytes"):
                response.assert_body_equals_file(shorter)

    def test_truncated_download_raises_connection_error(self, client):
        with client.get("/truncated").stream() as response:
            with pytest.raises(APIConnectionError, match="Download interrupted"):
                response.body_size

    def test_exit_releases_spool(self, client):
        with client.get("/file.bin").stream() as response:
            response.body_size
        assert response._spool is None

    def test_large_body_spools_to_disk(self, client, monkeypatch):
        monkeypatch.setattr(download, "SPOOL_MAX_MEMORY", 1024)
        with client.get("/file.bin").stream() as response:
            spool = response._body_spool()
            assert spool._rolled is True
            response.assert_checksum("sha256", PAYLOAD_SHA256)

    def test_retry_with_stream(self, client, server_url):
        with client.get("/flaky").stream().with_retry(max_attempts=2, backoff_factor=0) as response:
            response.assert_status(200).assert_body_size(len(CSV))


# ── assertion failures ────────────────────────────────────────────────────────

class TestDownloadAssertionFailures:

    def test_content_type_mismatch(self, client):
        with client.get("/export.csv").stream() as response:
            response.assert_content_type("TEXT/CSV")
            response.assert_content_type("text/csv; charset=UTF-8")
            with pytest.raises(AssertionError, match="Expected Content-Type 'text/plain'"):
                response.assert_content_type("text/plain")
            with pytest.raises(AssertionError):
                response.assert_content_type("text/csv; charset=latin-1")

    def test_attachment_wrong_disposition(self, client):
        with client.get("/inline").stream() as response:
            with pytest.raises(AssertionError, match="got 'inline'"):
                response.assert_attachment()

    def test_attachment_wrong_filename(self, client):
        with client.get("/file.bin").stream() as response:
            with pytest.raises(AssertionError, match="got 'file.bin'"):
                response.assert_attachment(filename="other.bin")

    def test_attachment_missing_header(self, client):
        with client.get("/chunked").stream() as response:
            with pytest.raises(AssertionError, match="Content-Disposition"):
                response.assert_attachment()

    def test_body_size_failures(self, client):
        with client.get("/export.csv").stream() as response:
            with pytest.raises(AssertionError, match="Expected body size 1 bytes"):
                response.assert_body_size(1)
            with pytest.raises(AssertionError, match=">="):
                response.assert_body_size(min_bytes=10_000)
            with pytest.raises(AssertionError, match="<="):
                response.assert_body_size(max_bytes=1)
            with pytest.raises(ValueError):
                response.assert_body_size()

    def test_checksum_failures(self, client):
        with client.get("/export.csv").stream() as response:
            with pytest.raises(AssertionError, match="sha256 checksum"):
                response.assert_checksum("sha256", "0" * 64)
            with pytest.raises(ValueError, match="Unsupported hash algorithm"):
                response.assert_checksum("not-a-hash", "x")

    def test_content_length_missing(self, client):
        with client.get("/chunked").stream() as response:
            with pytest.raises(AssertionError, match="Content-Length"):
                response.assert_content_length()

    def test_content_length_with_encoding_is_explicit(self):
        from lashtest.core.response import Response
        from datetime import timedelta
        raw = MagicMock()
        raw.status_code = 200
        raw.elapsed = timedelta(seconds=0.1)
        raw.headers = {"Content-Length": "5", "Content-Encoding": "gzip"}
        raw.content = b"hello world"
        with pytest.raises(AssertionError, match="'gzip'-encoded"):
            Response(raw).assert_content_length()


# ── non-streamed responses get the same helpers ───────────────────────────────

class TestNonStreamedResponse:

    def test_download_assertions_work_without_stream(self, client):
        with client.get("/file.bin") as response:
            assert response.streamed is False
            response.assert_attachment(filename="file.bin") \
                    .assert_checksum("sha256", PAYLOAD_SHA256) \
                    .assert_content_length()
            assert response.content == PAYLOAD


# ── async ─────────────────────────────────────────────────────────────────────

class TestAsyncStreamedDownload:

    @pytest.fixture(autouse=True)
    def _need_httpx(self):
        pytest.importorskip("httpx")

    def test_async_stream_chain(self, server_url, tmp_path):
        from lashtest.core.async_client import AsyncAPIClient

        async def run():
            async with AsyncAPIClient(server_url) as client:
                async with client.get("/file.bin").stream(chunk_size=8192) as response:
                    assert response.streamed is True
                    response.assert_status(200) \
                            .assert_attachment(filename="file.bin") \
                            .assert_content_length() \
                            .assert_checksum("sha256", PAYLOAD_SHA256) \
                            .save_to(tmp_path / "async.bin")
                    chunks = [c async for c in response.aiter_bytes(10_000)]
                    assert b"".join(chunks) == PAYLOAD
                assert response._spool is None

        asyncio.run(run())
        assert (tmp_path / "async.bin").read_bytes() == PAYLOAD

    def test_async_stream_json(self, server_url):
        from lashtest.core.async_client import AsyncAPIClient

        async def run():
            async with AsyncAPIClient(server_url) as client:
                async with client.get("/inline").stream() as response:
                    assert response.json() == {"ok": True}

        asyncio.run(run())

    def test_async_truncated_download(self, server_url):
        from lashtest.core.async_client import AsyncAPIClient

        async def run():
            async with AsyncAPIClient(server_url) as client:
                await client.get("/truncated").stream().send()

        with pytest.raises(APIConnectionError, match="Download interrupted"):
            asyncio.run(run())

    def test_async_stream_rejects_bad_chunk_size(self, server_url):
        from lashtest.core.async_client import AsyncAPIClient
        with pytest.raises(ValueError):
            AsyncAPIClient(server_url).get("/x").stream(chunk_size=0)
