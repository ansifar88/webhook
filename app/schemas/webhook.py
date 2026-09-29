from pydantic import BaseModel


class PaymentWebhook(BaseModel):
    event_id: str
    event_type: str
    payment_id: str
    amount: int
    currency: str