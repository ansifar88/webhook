import asyncio


async def process_payment_event(event):

    print(
        f"Processing payment: {event.payment_id}"
    )

    await asyncio.sleep(2)

    print(
        f"Payment processed: {event.payment_id}"
    )