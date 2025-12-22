from fastapi import FastAPI
from app.api import membership
from app.models.member import Base
from app.db.database import DATABASE_URL, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Topptur og Frikjøring API",
    description="API for managing members and synchronizing member data",
    version="1.0.0"
)

# Include routers
app.include_router(membership.router)


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to Topptur og Frikjøring API",
        "version": "1.0.0",
        "endpoints": {
            "members": "/api/members",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("DATABASE_URL =", DATABASE_URL)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
