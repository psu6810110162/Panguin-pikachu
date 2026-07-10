import urllib.error
import urllib.request

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


def test_verify_rejects_a_relabeled_top_level_run_id():
    # run_id ระดับบนถูกรวมใน signature — สวมรอย payload ที่เซ็นถูกต้องเป็นคนละ run ไม่ได้
    payload = sign_run_record(_make_record("run-1"), SECRET, timestamp=1000.0, nonce="n1")
    relabeled = SignedPayload(
        run_id="run-EVIL",
        timestamp=payload.timestamp,
        nonce=payload.nonce,
        body=payload.body,
        signature=payload.signature,
    )
    with pytest.raises(VerificationError, match="signature"):
        verify_signed_payload(relabeled, SECRET, InMemoryNonceStore(), now=1000.0)


def test_verify_rejects_shifted_field_boundaries():
    # Canonical JSON envelope กัน delimiter confusion: ย้ายเนื้อหาข้ามขอบเขต field
    # (nonce กิน prefix ของ body) แล้ว signature เดิมต้องใช้ไม่ได้
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    shifted = SignedPayload(
        run_id=payload.run_id,
        timestamp=payload.timestamp,
        nonce=payload.nonce + payload.body[:1],
        body=payload.body[1:],
        signature=payload.signature,
    )
    with pytest.raises(VerificationError, match="signature"):
        verify_signed_payload(shifted, SECRET, InMemoryNonceStore(), now=1000.0)


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


def test_enqueue_is_a_no_op_for_a_run_still_pending_in_the_queue():
    # double-enqueue ก่อน flush แรกสำเร็จ ต้องไม่สร้าง entry ซ้ำ (คนละ nonce)
    transport = _FakeTransport(results=[True])
    client = _client(transport)
    record = _make_record("run-1")

    client.enqueue(record)
    client.enqueue(record)
    assert client.pending_run_ids() == ["run-1"]

    sent = client.flush()
    assert sent == ["run-1"]
    assert transport.calls == 1


def test_enqueue_is_still_deduped_while_a_run_is_retrying():
    transport = _FakeTransport(results=[False, True])
    client = _client(transport)
    record = _make_record("run-1")

    client.enqueue(record)
    client.flush()  # fail — ค้างอยู่ในคิวรอ retry
    client.enqueue(record)  # ต้องไม่เพิ่มซ้ำระหว่าง retry
    assert client.pending_run_ids() == ["run-1"]

    assert client.flush() == ["run-1"]


def test_a_dropped_run_can_be_enqueued_again():
    transport = _FakeTransport(results=[False, False, True])
    client = _client(transport, max_retries=1)
    record = _make_record("run-1")

    client.enqueue(record)
    client.flush()
    client.flush()  # เกิน max_retries — ถูก drop ออกจากคิวและ _pending_run_ids
    assert client.pending_run_ids() == []

    client.enqueue(record)  # drop แล้ว caller ลองใหม่ได้
    assert client.flush() == ["run-1"]


# ── HttpTransport ─────────────────────────────────────────


class _FakeHTTPResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="http://test",
        code=code,
        msg="",
        hdrs=None,
        fp=None,  # type: ignore[arg-type]
    )


def _send_with(monkeypatch: pytest.MonkeyPatch, outcome: object) -> bool:
    def fake_urlopen(request: object, timeout: float) -> _FakeHTTPResponse:
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, int)
        return _FakeHTTPResponse(status=outcome)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    payload = sign_run_record(_make_record(), SECRET, timestamp=1000.0, nonce="n1")
    return HttpTransport("http://test/api").send(payload)


def test_http_transport_returns_true_on_2xx(monkeypatch: pytest.MonkeyPatch):
    assert _send_with(monkeypatch, 200) is True


def test_http_transport_retries_on_4xx(monkeypatch: pytest.MonkeyPatch):
    # พฤติกรรม ณ D8: ทุก HTTP error ถูก retry — การ dequeue 4xx ถาวรมาทีหลังพร้อม
    # เหตุผลใน PR follow-ups (#31)
    assert _send_with(monkeypatch, _http_error(401)) is False


def test_http_transport_retries_on_5xx(monkeypatch: pytest.MonkeyPatch):
    assert _send_with(monkeypatch, _http_error(500)) is False


def test_http_transport_retries_on_network_error(monkeypatch: pytest.MonkeyPatch):
    assert _send_with(monkeypatch, urllib.error.URLError("connection refused")) is False
