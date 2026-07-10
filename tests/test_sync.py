import io
import urllib.error
from unittest.mock import patch

import pytest

from core.schema import RunRecord
from core.sync import (
    DEFAULT_BACKOFF_BASE_S,
    DEFAULT_MAX_RETRIES,
    HttpTransport,
    InMemoryNonceStore,
    SignedPayload,
    SyncClient,
    Transport,
    VerificationError,
    sign_run_record,
    verify_signed_payload,
)

SECRET = b"test-secret"


def _make_record(run_id: str = "run-1") -> RunRecord:
    return RunRecord(run_id=run_id, player_id="player-1")


# ── Signing / verification ───────────────────────────────


def test_sign_and_verify_round_trip_succeeds():
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    verify_signed_payload(payload, SECRET, InMemoryNonceStore(), now=1000.0)


def test_verify_rejects_a_tampered_body():
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    tampered = SignedPayload(
        run_id=payload.run_id,
        timestamp=payload.timestamp,
        nonce=payload.nonce,
        body=payload.body.replace("run-1", "run-EVIL"),
        signature=payload.signature,
    )
    with pytest.raises(VerificationError, match="signature"):
        verify_signed_payload(tampered, SECRET, InMemoryNonceStore(), now=1000.0)


def test_verify_rejects_the_wrong_secret():
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    with pytest.raises(VerificationError, match="signature"):
        verify_signed_payload(payload, b"wrong-secret", InMemoryNonceStore(), now=1000.0)


def test_verify_rejects_a_stale_timestamp():
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    with pytest.raises(VerificationError, match="clock skew"):
        verify_signed_payload(payload, SECRET, InMemoryNonceStore(), now=1000.0 + 301.0)


def test_verify_rejects_a_replayed_nonce():
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    store = InMemoryNonceStore()
    verify_signed_payload(payload, SECRET, store, now=1000.0)

    with pytest.raises(VerificationError, match="replay"):
        verify_signed_payload(payload, SECRET, store, now=1000.0)


# ── SyncClient: queue, retry/backoff, idempotency ────────


class _FakeTransport:
    """ส่งได้/ไม่ได้ตาม script ที่กำหนดไว้ล่วงหน้า — เพื่อจำลองเน็ตหลุด/กลับมา"""

    def __init__(self, results: list[bool]) -> None:
        self._results = list(results)
        self.calls = 0

    def send(self, payload: SignedPayload) -> bool:
        self.calls += 1
        if not self._results:
            return True
        return self._results.pop(0)


def _client(
    transport: Transport,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_base_s: float = DEFAULT_BACKOFF_BASE_S,
) -> SyncClient:
    return SyncClient(SECRET, transport, max_retries=max_retries, backoff_base_s=backoff_base_s)


def test_flush_sends_a_queued_record_successfully():
    transport = _FakeTransport(results=[True])
    client = _client(transport)
    client.enqueue(_make_record("run-1"))

    sent = client.flush()

    assert sent == ["run-1"]
    assert client.pending_run_ids() == []


def test_failed_send_stays_queued_and_retries_on_next_flush():
    transport = _FakeTransport(results=[False, True])
    client = _client(transport)
    client.enqueue(_make_record("run-1"))

    first = client.flush()
    assert first == []
    assert client.pending_run_ids() == ["run-1"]

    second = client.flush()
    assert second == ["run-1"]
    assert client.pending_run_ids() == []


def test_item_is_dropped_after_exceeding_max_retries():
    transport = _FakeTransport(results=[False, False])
    client = _client(transport, max_retries=1)
    client.enqueue(_make_record("run-1"))

    client.flush()  # attempt 1 fails, requeued (attempts=1 <= max_retries=1)
    client.flush()  # attempt 2 fails, attempts=2 > max_retries=1, dropped

    assert client.pending_run_ids() == []
    assert transport.calls == 2


def test_enqueue_is_a_no_op_for_a_run_already_synced():
    transport = _FakeTransport(results=[True])
    client = _client(transport)
    record = _make_record("run-1")

    client.enqueue(record)
    client.flush()
    assert client.pending_run_ids() == []

    client.enqueue(record)  # idempotent: already in _sent_run_ids
    assert client.pending_run_ids() == []


def test_backoff_delay_grows_exponentially():
    client = _client(_FakeTransport(results=[]), backoff_base_s=2.0)
    assert client.backoff_delay(0) == 2.0
    assert client.backoff_delay(1) == 4.0
    assert client.backoff_delay(2) == 8.0


# ── HttpTransport ─────────────────────────────────────────


def _make_payload() -> SignedPayload:
    return sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")


def test_http_transport_returns_true_on_2xx():
    transport = HttpTransport("https://example.test/runs")
    fake_response = io.BytesIO(b"{}")
    fake_response.status = 200
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        assert transport.send(_make_payload()) is True


def test_http_transport_gives_up_without_retry_on_4xx():
    """400/401 = server จะไม่มีวันรับ payload นี้ ไม่ว่า retry กี่ครั้ง — dequeue ทันที (True)"""
    transport = HttpTransport("https://example.test/runs")
    error = urllib.error.HTTPError(
        url="https://example.test/runs", code=401, msg="unauthorized", hdrs=None, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=error):
        assert transport.send(_make_payload()) is True


def test_http_transport_retries_on_5xx():
    """500 = ปัญหาชั่วคราวฝั่ง server — ยังคุ้มที่จะ retry (False = ยังอยู่ในคิว)"""
    transport = HttpTransport("https://example.test/runs")
    error = urllib.error.HTTPError(
        url="https://example.test/runs", code=500, msg="server error", hdrs=None, fp=None
    )
    with patch("urllib.request.urlopen", side_effect=error):
        assert transport.send(_make_payload()) is False


def test_http_transport_retries_on_network_error():
    transport = HttpTransport("https://example.test/runs")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network down")):
        assert transport.send(_make_payload()) is False
