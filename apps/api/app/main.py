from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import calculations, norms, diagnosis, billing

app = FastAPI(title="EngBrain API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(calculations.router)
app.include_router(norms.router)
app.include_router(diagnosis.router)
app.include_router(billing.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
