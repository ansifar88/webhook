from fastapi import FastAPI
from app.routes.webhooks import router as webhook_router

app = FastAPI()

app.include_router(webhook_router)


@app.get("/")
async def root():
    return {
        "message": "Webhook Hub is running"
    }