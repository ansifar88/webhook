# Webhook Hub

A deliberately small FastAPI service for receiving payment webhooks safely enough to be useful from day one. It checks that a request was signed with a shared secret, ignores repeat deliveries while the app is running, and gets back to the sender quickly while the payment work happens in the background.

It is a compact starting point rather than a payment provider integration: there is no provider SDK or database to configure. Send it a correctly signed JSON payload and it will accept it.

## What happens to a webhook

1. `POST /webhooks/payment` receives the request.
2. The service reads `X-Webhook-Signature` and verifies it against the **exact raw request body** using HMAC-SHA256.
3. If the `event_id` has already been seen in this process, it responds with `already_processed`.
4. Otherwise it queues `process_payment_event` as a FastAPI background task and immediately acknowledges receipt.

For now, the background handler logs the payment ID, waits two seconds to mimic downstream work, then logs that it finished. That makes it a friendly place to add database updates, fulfilment, notifications, or a call to another service.

## Quick start

You will need Python 3.9 or newer.

```bash
git clone <your-repository-url>
cd webhook-hub

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
WEBHOOK_SECRET=my-super-secret-key
```

Then start the server:

```bash
uvicorn app.main:app --reload
```

The service will be available at `http://127.0.0.1:8000`. A quick browser or curl check is enough to confirm it is alive:

```bash
curl http://127.0.0.1:8000/
```

Expected response:

```json
{"message":"Webhook Hub is running"}
```

FastAPI also provides interactive API docs at `http://127.0.0.1:8000/docs`.

## Sending a payment event

The receiver expects JSON with these fields:

| Field | Type | Example |
| --- | --- | --- |
| `event_id` | string | `evt_001` |
| `event_type` | string | `payment.completed` |
| `payment_id` | string | `pay_123` |
| `amount` | integer | `4999` |
| `currency` | string | `INR` |

The sender must calculate an HMAC-SHA256 hex digest of the raw JSON body with `WEBHOOK_SECRET`, then send that digest in `X-Webhook-Signature`.

There is a ready-made helper for the included sample event:

```bash
python generate_signature.py
```

It prints a signature for this exact payload, using the sample secret `my-super-secret-key`:

```json
{"event_id":"evt_001","event_type":"payment.completed","payment_id":"pay_123","amount":4999,"currency":"INR"}
```

With that same secret in `.env`, paste the printed value into this request:

```bash
curl -X POST http://127.0.0.1:8000/webhooks/payment \
  -H 'Content-Type: application/json' \
  -H 'X-Webhook-Signature: <signature-from-generate_signature.py>' \
  --data-raw '{"event_id":"evt_001","event_type":"payment.completed","payment_id":"pay_123","amount":4999,"currency":"INR"}'
```

A first delivery returns:

```json
{"status":"received","event_id":"evt_001"}
```

Repeating the same event ID while the server is still running returns:

```json
{"status":"already_processed"}
```

## Responses you can rely on

| Situation | Response |
| --- | --- |
| Valid, new event | `200 OK` with `status: "received"` |
| Same `event_id` seen again in the current process | `200 OK` with `status: "already_processed"` |
| No signature header | `401 Unauthorized` |
| Signature does not match | `401 Unauthorized` |

## A couple of important realities

This project keeps processed event IDs in an in-memory Python set. Restarting the server clears it, and running more than one worker means each worker has its own list. That is perfect for a local demo, but production deduplication belongs in shared durable storage (usually a database table keyed by provider event ID).

Likewise, FastAPI background tasks run in the same application process. They keep the webhook endpoint responsive, but they are not a durable job queue: an app restart can interrupt work. For work that must survive retries and restarts, write the event to durable storage before acknowledging it and process it with a queue or worker.

Finally, the signature covers bytes, not a reformatted JSON object. Any difference in whitespace, character encoding, or field order changes the digest. Sign the exact body that is sent.

## Project layout

```text
app/
├── main.py                  # FastAPI application and health-style root route
├── routes/webhooks.py       # Payment webhook endpoint and duplicate check
├── core/security.py          # Environment loading and HMAC verification
├── schemas/webhook.py        # Expected payment event shape
└── services/webhook_service.py # Background payment-processing placeholder
generate_signature.py        # Signs the bundled sample payload
requirements.txt             # Pinned Python dependencies
```

## Next sensible steps

- Replace the in-memory duplicate set with a unique database record.
- Make processing idempotent and record failures for safe retries.
- Move important work to a durable queue/worker.
- Add provider-specific timestamp checks to reduce replay risk.
- Add tests for valid signatures, rejected signatures, malformed payloads, and duplicate delivery.

## Security note

Keep `WEBHOOK_SECRET` out of version control. The included `.gitignore` already excludes `.env`; use a long, randomly generated secret for anything beyond local development.
