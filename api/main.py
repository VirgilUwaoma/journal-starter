from fastapi import FastAPI
from dotenv import load_dotenv
from routers.journal_router import router as journal_router
import logging
from contextlib import asynccontextmanager
load_dotenv()

# TODO: Setup basic console logging
# Hint: Use logging.basicConfig() with level=logging.INFO
# Steps:
# 1. Configure logging with basicConfig()
# 2. Set level to logging.INFO
# 3. Add console handler
# 4. Test by adding a log message when the app starts

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
