from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.database import engine
from app.models import models
from app.controllers import user_controller

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("user-service")

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", 
              description="User management microservice for MealMateAI",
              version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "service": "user-service"}

# Include user controller router
app.include_router(user_controller.router, tags=["users"])

# Add this section to run the app directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")