from fastapi import FastAPI

app = FastAPI(title="Analytics Service")


@app.get("/health")
async def health():
    return {"status": "ok"}
