"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import documents
from app.config import logger

# Logging is already configured in app.config
# Just get the logger for this module
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PDF2AlloyDB API",
    description="API for processing PDF documents from Google Drive and storing in AlloyDB",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "PDF2AlloyDB API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint with database connection test."""
    from app.db.connection import test_connection
    
    db_healthy = test_connection()
    status = "healthy" if db_healthy else "unhealthy"
    
    return {
        "status": status,
        "database": "connected" if db_healthy else "disconnected"
    }


@app.post("/admin/reconnect-db")
async def reconnect_database():
    """
    Manually reconnect to the database. Use this if database becomes unresponsive.
    This will close all existing connections and create new ones.
    """
    import time
    from app.db.connection import reconnect_db, test_connection, dispose_engine
    
    try:
        # First, try to dispose of any stuck connections
        logger.info("Attempting to dispose of existing connections...")
        dispose_engine(force=True)
        
        # Wait a moment for connections to close
        time.sleep(2)
        
        # Now try to reconnect
        reconnect_db(max_attempts=3, wait_between_attempts=3)
        
        # Test the connection
        is_healthy = test_connection()
        
        if is_healthy:
            return {
                "status": "success",
                "message": "Database reconnected successfully",
                "connection_healthy": True
            }
        else:
            return {
                "status": "warning",
                "message": "Database reconnected but connection test failed. The server may be down or unreachable.",
                "connection_healthy": False
            }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error reconnecting to database: {error_msg}")
        
        # Provide helpful error message
        if "timeout" in error_msg.lower():
            suggestion = "The database server may be down, unreachable, or overloaded. Check server status and network connectivity."
        elif "connection" in error_msg.lower():
            suggestion = "Unable to establish connection. Check if the database server is running and accessible."
        else:
            suggestion = "Check database server logs and ensure the connection string is correct."
        
        return {
            "status": "error",
            "message": f"Failed to reconnect: {error_msg}",
            "suggestion": suggestion,
            "connection_healthy": False
        }


if __name__ == "__main__":
    import uvicorn
    # Configure uvicorn to use the same logging configuration
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_config=None,  # Use Python's logging configuration instead of uvicorn's
        access_log=True   # Enable access logs
    )

