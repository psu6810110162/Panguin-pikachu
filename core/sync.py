"""Secure sync client — ส่ง RunRecord ไปเซิร์ฟเวอร์ ตาม docs/adr/004-https-hmac-no-aes.md

HTTPS จัดการ encrypt-in-transit อยู่แล้ว ที่นี่ทำแค่ HMAC-SHA256 sign บน
timestamp + nonce + payload (กัน tamper + replay attack) และคิว offline
พร้อม retry/backoff เผื่อเน็ตหลุดกลางคัน (สถานการณ์จริงของห้องเรียน)
"""

import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from typing import Protocol

from core.schema import RunRecord

# ปฏิเสธ payload ที่ timestamp ห่างจากเวลาปัจจุบันเกินนี้ แม้ signature/nonce จะถูกต้องก็ตาม
MAX_CLOCK_SKEW_S = 300.0
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_BASE_S = 1.0


# ── Signing ───────────────────────────────────────────────


@dataclass
class SignedPayload:
    run_id: str
    timestamp: float
    nonce: str
    body: str  # RunRecord.to_dict() เข้ารหัสเป็น JSON แล้ว (sort_keys=True เพื่อผลลัพธ์คงที่)
    signature: str  # HMAC-SHA256 hex digest


def _compute_signature(secret: bytes, timestamp: float, nonce: str, body: str) -> str:
    message = f"{timestamp}:{nonce}:{body}".encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def sign_run_record(
    record: RunRecord,
    secret: bytes,
    *,
    timestamp: float | None = None,
    nonce: str | None = None,
) -> SignedPayload:
    """Serialize + sign RunRecord หนึ่งอัน — timestamp/nonce รับค่าจากภายนอกได้ (สำหรับ test)
    ถ้าไม่ระบุจะสุ่ม/ใช้เวลาจริง
    """
    ts = timestamp if timestamp is not None else time.time()
    n = nonce if nonce is not None else secrets.token_hex(16)
    body = json.dumps(record.to_dict(), sort_keys=True)
    signature = _compute_signature(secret, ts, n, body)
    return SignedPayload(
        run_id=record.run_id, timestamp=ts, nonce=n, body=body, signature=signature
    )


# ── Verification (ฝั่ง server จะใช้) ──────────────────────


class VerificationError(Exception):
    """เกิดขึ้นเมื่อ SignedPayload ไม่ผ่าน signature, freshness หรือ replay check"""


class NonceStore(Protocol):
    def seen(self, nonce: str) -> bool: ...
    def remember(self, nonce: str) -> None: ...


class InMemoryNonceStore:
    """NonceStore ง่าย ๆ ใช้ใน test และ dev server (D9) — ถ้า deploy จริงแล้ว server
    restart บ่อยควรเปลี่ยนเป็น store ที่ persist ได้ (DB/Redis) แทน
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def seen(self, nonce: str) -> bool:
        return nonce in self._seen

    def remember(self, nonce: str) -> None:
        self._seen.add(nonce)


def verify_signed_payload(
    payload: SignedPayload,
    secret: bytes,
    nonce_store: NonceStore,
    *,
    now: float | None = None,
    max_clock_skew_s: float = MAX_CLOCK_SKEW_S,
) -> None:
    """ตรวจ signature, ความสด (freshness), และ replay — raise VerificationError ถ้าไม่ผ่าน
    ข้อใดข้อหนึ่ง ถ้าผ่านทั้งหมดจะ remember nonce ไว้ทันที (ป้องกัน payload เดิมถูกส่งซ้ำ)
    """
    current = now if now is not None else time.time()

    expected = _compute_signature(secret, payload.timestamp, payload.nonce, payload.body)
    if not hmac.compare_digest(expected, payload.signature):
        raise VerificationError("signature mismatch")

    if abs(current - payload.timestamp) > max_clock_skew_s:
        raise VerificationError("timestamp outside allowed clock skew")

    if nonce_store.seen(payload.nonce):
        raise VerificationError("nonce already used (replay)")

    nonce_store.remember(payload.nonce)


# ── Offline queue + retry/backoff + idempotency ──────────


class Transport(Protocol):
    def send(self, payload: SignedPayload) -> bool:
        """True = ส่งสำเร็จ (2xx), False = ล้มเหลว (เน็ตหลุด, server ตอบ error ฯลฯ)"""
        ...


@dataclass
class _QueuedRun:
    payload: SignedPayload
    attempts: int = 0


class SyncClient:
    """คิว RunRecord ที่ยังไม่ได้ sync, sign แล้วส่งผ่าน transport พร้อม retry/backoff

    รอบที่ส่งไม่สำเร็จจะยังอยู่ในคิว (ไม่หาย) จนกว่าจะเกิน max_retries — เหมาะกับสถานการณ์
    ห้องเรียนที่เน็ตไม่นิ่ง เรียก flush() ซ้ำได้เรื่อย ๆ เมื่อเน็ตกลับมา (caller เป็นคนกำหนด
    จังหวะเรียก เช่นผ่าน Kivy Clock — core/ ไม่ sleep/schedule เอง)
    """

    def __init__(
        self,
        secret: bytes,
        transport: Transport,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_s: float = DEFAULT_BACKOFF_BASE_S,
    ) -> None:
        self._secret = secret
        self._transport = transport
        self._max_retries = max_retries
        self._backoff_base_s = backoff_base_s
        self._queue: deque[_QueuedRun] = deque()
        self._sent_run_ids: set[str] = set()  # idempotency: กัน enqueue ซ้ำของ run ที่ sync แล้ว

    def enqueue(self, record: RunRecord) -> None:
        if record.run_id in self._sent_run_ids:
            return
        self._queue.append(_QueuedRun(payload=sign_run_record(record, self._secret)))

    def flush(self) -> list[str]:
        """พยายามส่งทุกอย่างในคิวหนึ่งรอบ คืน run_id ที่ส่งสำเร็จ

        รายการที่ยังไม่เกิน max_retries จะถูกใส่กลับเข้าคิว รายการที่เกินแล้วจะถูกทิ้ง
        (เรียก pending_run_ids() เพื่อตรวจว่ามีอะไรค้าง/หลุดคิวไปบ้าง)
        """
        sent: list[str] = []
        remaining: deque[_QueuedRun] = deque()

        while self._queue:
            item = self._queue.popleft()
            if self._transport.send(item.payload):
                self._sent_run_ids.add(item.payload.run_id)
                sent.append(item.payload.run_id)
                continue

            item.attempts += 1
            if item.attempts <= self._max_retries:
                remaining.append(item)

        self._queue = remaining
        return sent

    def pending_run_ids(self) -> list[str]:
        return [item.payload.run_id for item in self._queue]

    def backoff_delay(self, attempt: int) -> float:
        """Exponential backoff: backoff_base_s * 2**attempt — เป็นแค่การคำนวณ ไม่ sleep เอง
        caller (เช่น Kivy Clock.schedule_once) เป็นคนใช้ค่านี้กำหนดจังหวะ retry
        """
        return self._backoff_base_s * (2**attempt)


# ── Default transport (สำหรับใช้งานจริง) ─────────────────


class HttpTransport:
    """ส่ง SignedPayload เป็น JSON ผ่าน HTTPS POST — ใช้ stdlib urllib ล้วน ไม่เพิ่ม
    dependency ใหม่ (เช่น requests) เว้นแต่ในอนาคตความต้องการซับซ้อนขึ้นจริง ๆ
    """

    def __init__(self, url: str, timeout_s: float = 5.0) -> None:
        self._url = url
        self._timeout_s = timeout_s

    def send(self, payload: SignedPayload) -> bool:
        body = json.dumps(
            {
                "run_id": payload.run_id,
                "timestamp": payload.timestamp,
                "nonce": payload.nonce,
                "body": payload.body,
                "signature": payload.signature,
            }
        ).encode()
        request = urllib.request.Request(
            self._url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:  # noqa: S310
                return 200 <= response.status < 300
        except urllib.error.HTTPError as error:
            # 4xx (signature/validation ผิด) จะไม่มีวันสำเร็จถึงจะ retry กี่ครั้งก็ตาม —
            # ถือว่า "จัดการแล้ว" (True) เพื่อให้ SyncClient.flush() เอาออกจากคิว ไม่ใช่
            # เก็บไว้ retry จนครบ max_retries โดยเปล่าประโยชน์ ส่วน 5xx เป็นปัญหาฝั่ง server
            # ชั่วคราว ยังคุ้มที่จะ retry (False)
            return 400 <= error.code < 500
        except (urllib.error.URLError, TimeoutError):
            return False
