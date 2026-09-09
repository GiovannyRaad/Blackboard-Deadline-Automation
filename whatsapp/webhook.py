from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

VERIFY_TOKEN = "mytesttoken123"  # pick anything you want

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

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
