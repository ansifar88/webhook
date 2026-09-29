import hashlib
import hmac

secret = "my-super-secret-key"

payload = (
    '{"event_id":"evt_001",'
    '"event_type":"payment.completed",'
    '"payment_id":"pay_123",'
    '"amount":4999,'
    '"currency":"INR"}'
)

signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

print(signature)