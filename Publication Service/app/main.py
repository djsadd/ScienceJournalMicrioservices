from fastapi import FastAPI

app = FastAPI(title="Publication Service")


@app.get("/health")
async def health():
    return {"status": "ok"}
