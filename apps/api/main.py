from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from contextlib import asynccontextmanager
import secrets

from .config import APIConfig
from .routers import public, admin, monitoring
from .deps.dependencies import db_pool, redis_pool
from .auth.jwt_auth import create_access_token, pwd_context
from .models import TokenResponse

config = APIConfig()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_pool.init(config.database_url.get_secret_value())
    # Initialize Redis is handled in dependencies
    yield
    # Shutdown
    await db_pool.close()
    if redis_pool:
        await redis_pool.close()

app = FastAPI(
    title=config.api_title,
    version=config.api_version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(monitoring.router)

# Basic auth for getting JWT token
security = HTTPBasic()

@app.post("/api/auth/token", response_model=TokenResponse)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate and get JWT token"""
    # Verify credentials (in production, check against database)
    correct_username = secrets.compare_digest(
        credentials.username, config.admin_username
    )
    correct_password = pwd_context.verify(
        credentials.password, 
        config.admin_password.get_secret_value()
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Create token
    access_token = create_access_token(data={"sub": credentials.username})
    return TokenResponse(access_token=access_token)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Alpaca Trading API",
        "version": config.api_version,
        "docs": "/docs"
    }