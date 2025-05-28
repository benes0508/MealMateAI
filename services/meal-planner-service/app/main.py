from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import models
from app.controllers import meal_plan_controller
import logging

# Set up logging
logger = logging.getLogger("meal_planner")
logger.setLevel(logging.DEBUG)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meal Planner Service",
    description="LLM-powered meal planning service for MealMateAI",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Use empty prefix since API gateway handles the /api/meal-plans prefix
app.include_router(meal_plan_controller.router, tags=["meal-plans"])

@app.get("/health")
def health_check():
    """Health check endpoint for the service."""
    return {"status": "healthy", "service": "meal-planner-service"}