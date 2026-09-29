from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request
)

from app.schemas.webhook import PaymentWebhook
from app.core.security import verify_signature
from app.services.webhook_service import process_payment_event

router = APIRouter()

processed_events = set()


@router.post("/webhooks/payment")
async def payment_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):

    signature = request.headers.get(
        "X-Webhook-Signature"
    )

    if not signature:
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature"
        )

    payload = await request.body()

    if not verify_signature(payload, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    event = PaymentWebhook.model_validate_json(
        payload
    )

    if event.event_id in processed_events:
        return {
            "status": "already_processed"
        }

    processed_events.add(event.event_id)

    background_tasks.add_task(
        process_payment_event,
        event
    )

    return {
        "status": "received",
        "event_id": event.event_id
    }