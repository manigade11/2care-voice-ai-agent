from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes.health_routes import router as health_router
from backend.routes.appointment_routes import router as appointment_router
from backend.routes.websocket_routes import router as websocket_router
from backend.api.deps import campaign_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    campaign_scheduler.start()
    yield
    campaign_scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(appointment_router, prefix="/api")
app.include_router(websocket_router, prefix="/api")