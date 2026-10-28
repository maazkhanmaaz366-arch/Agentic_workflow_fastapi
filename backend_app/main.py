from fastapi import FastAPI 
from core.config import settings
from api.user.router import router as user_router
from api.product.router import router as product_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import os
from core.middleware import LoggingAndTimingMiddleware
from api.agent.router import router as agent_router
from api.user_agent.router import router as user_agent_router

app = FastAPI(
    title = settings.PROJECT_NAME,
    version= settings.VERSION
)
app.add_middleware(LoggingAndTimingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
os.makedirs("static", exist_ok=True)

app.mount("/static",StaticFiles(directory="static"),name="static")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials= True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

app.include_router(user_router)
app.include_router(product_router)
app.include_router(agent_router)
app.include_router(user_agent_router)


@app.get('/')
async def root():
    return {
        'message': 'Welcome to the user Management System',
        'version': settings.VERSION,
        'project': settings.PROJECT_NAME
    }

    
