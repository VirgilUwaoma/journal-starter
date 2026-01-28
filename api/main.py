from fastapi import FastAPI
from dotenv import load_dotenv
from api.routers.journal_router import router as journal_router
import logging
from contextlib import asynccontextmanager
load_dotenv()


logging.basicConfig(level="INFO")
LOGGER = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOGGER.info("Journal API Started Succesfully🚀")
    yield


app = FastAPI(title="Journal API",
              description="A simple journal API for tracking daily work, struggles, and intentions",
              lifespan=lifespan)
app.include_router(journal_router)
