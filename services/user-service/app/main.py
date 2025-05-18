from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import models
from app.controllers import user_controller

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", 
              description="User management microservice for MealMateAI",
              version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "user-service"}

# Include routers
app.include_router(user_controller.router, prefix="/api/users", tags=["users"])

# Add this section to run the app directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")