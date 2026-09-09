from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

app = FastAPI()

# Set WEBHOOK_VERIFY_TOKEN in whatsapp/.env; it must match what you enter in the
# Meta dashboard. Keeping it out of the source avoids committing a shared secret.
VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN")

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if not VERIFY_TOKEN:
        return {"error": "WEBHOOK_VERIFY_TOKEN is not set in whatsapp/.env"}

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "verification failed"}

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("🔥 WEBHOOK EVENT RECEIVED:")
    print(data)
    return {"status": "received"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
