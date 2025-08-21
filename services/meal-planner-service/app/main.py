from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models import models
from app.controllers import meal_plan_controller
import logging
from sqlalchemy import text

# Set up logging
logger = logging.getLogger("meal_planner")
logger.setLevel(logging.DEBUG)

def run_migrations():
    """Run any necessary database migrations on startup."""
    try:
        db = SessionLocal()
        
        # Check if grocery_list columns exist, if not add them
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'meal_plans' AND column_name IN ('grocery_list', 'grocery_list_generated_at')
        """))
        existing_columns = [row[0] for row in result]
        
        if 'grocery_list' not in existing_columns:
            logger.info("Adding grocery_list column to meal_plans table")
            db.execute(text("ALTER TABLE meal_plans ADD COLUMN grocery_list TEXT"))
            db.commit()
            
        if 'grocery_list_generated_at' not in existing_columns:
            logger.info("Adding grocery_list_generated_at column to meal_plans table")
            db.execute(text("ALTER TABLE meal_plans ADD COLUMN grocery_list_generated_at TIMESTAMP"))
            db.commit()
            
        # Create index if it doesn't exist
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_plans_grocery_list_generated_at 
            ON meal_plans(grocery_list_generated_at)
        """))
        db.commit()
        
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        # Don't fail startup, just log the error
    finally:
        db.close()

# Run migrations first
run_migrations()

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

@app.get("/health")
def health_check():
    """Health check endpoint for the service."""
    return {"status": "healthy", "service": "meal-planner-service"}

# Include routers
# Use empty prefix since API gateway handles the /api/meal-plans prefix
app.include_router(meal_plan_controller.router, tags=["meal-plans"])