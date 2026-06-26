import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .api.document_routes import router as document_router
from .services import init_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing services...")
    init_services()
    logger.info("Services initialized. Backend ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Multilingual Sentiment Chatbot API",
    description="AI-powered multilingual chatbot with sentiment detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
