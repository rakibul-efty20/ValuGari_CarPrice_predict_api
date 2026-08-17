import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.model import ModelLoadError, get_model
from app.routers import predict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at process startup so the first request isn't slow,
    # and so a broken/missing pkl fails loudly at boot instead of mid-request.
    try:
        get_model()
    except ModelLoadError:
        logger.exception("Model failed to load at startup")
        raise
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix=f"/api/{settings.api_version}")

# Registered after the API router, so /api/v1/* and /docs still resolve
# there first — this only catches whatever those routes don't claim.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
