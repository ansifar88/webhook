import hashlib
import hmac
import os

from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


def verify_signature(
    payload: bytes,
    signature: str
) -> bool:

    if not WEBHOOK_SECRET:
        return False

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature
    )