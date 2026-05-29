from fastapi import FastAPI
from app.api.v1.endpoints import knowledge

app = FastAPI(
    title="Knowledge Service",
    description="Enterprise Knowledge Service for AI Agents",
    version="0.1.0"
)

app.include_router(knowledge.router, prefix="/api/v1", tags=["Knowledge"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
