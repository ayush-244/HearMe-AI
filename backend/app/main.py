import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .api.document_routes import router as document_router
from .api.search_routes import router as search_router
from .api.knowledge_routes import router as knowledge_router
from .api.memory_routes import router as memory_router
from .api.conversation_routes import router as conversation_router
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
app.include_router(search_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(conversation_router, prefix="/api/v1")
