from fastapi import FastAPI

app = FastAPI(title="File Processing Service")


@app.get("/health")
async def health():
    return {"status": "ok"}
