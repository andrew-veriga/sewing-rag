"""Database connection management for AlloyDB."""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator, Optional
import time

from app.config import ALLOYDB_CONNECTION_STRING, logger
from app.models.database import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
engine: Optional[create_engine] = None
SessionLocal: Optional[sessionmaker] = None


def create_engine_with_pooling(connection_string: str):
    """
    Create SQLAlchemy engine with connection pooling and recovery settings.
    
    Args:
        connection_string: Database connection string
        
    Returns:
        SQLAlchemy engine
    """
    return create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=3,  # Reduced pool size to prevent connection exhaustion
        max_overflow=5,  # Reduced overflow to prevent too many connections
        pool_timeout=20,  # Timeout for getting connection from pool
        pool_recycle=1800,  # Recycle connections after 30 minutes (prevent stale connections)
        pool_pre_ping=True,  # Verify connections before using (auto-recovery)
        echo=False,  # Set to True for SQL query logging
        future=True,
        connect_args={
            "connect_timeout": 15,  # Increased connection timeout to 15 seconds
            "options": "-c statement_timeout=300000 -c idle_in_transaction_session_timeout=60000"  # 5 min statement timeout, 1 min idle transaction timeout
        }
    )


def initialize_db():
    """Initialize database engine and session factory."""
    global engine, SessionLocal
    
    if not ALLOYDB_CONNECTION_STRING:
        logger.warning("ALLOYDB_CONNECTION_STRING not set. Database operations will fail.")
        engine = None
        SessionLocal = None
        return
    
    try:
        engine = create_engine_with_pooling(ALLOYDB_CONNECTION_STRING)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database engine initialized with connection pooling")
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {str(e)}")
        engine = None
        SessionLocal = None
        raise


def dispose_engine(force: bool = False):
    """
    Dispose of the current engine and close all connections.
    
    Args:
        force: If True, force close even if there are errors
    """
    global engine, SessionLocal
    
    if engine:
        try:
            logger.info("Disposing database engine and closing all connections")
            # Invalidate all connections in the pool
            engine.pool.invalidate()
            # Dispose the engine
            engine.dispose(close=True)
        except Exception as e:
            logger.warning(f"Error disposing engine (this may be normal): {str(e)}")
            if force:
                # Force close by setting to None
                try:
                    engine.pool.dispose()
                except:
                    pass
        finally:
            engine = None
            SessionLocal = None
            # Give the system a moment to fully close connections
            time.sleep(0.5)


def reconnect_db(max_attempts: int = 3, wait_between_attempts: int = 3):
    """
    Reconnect to the database by disposing and recreating the engine.
    Tries multiple times with exponential backoff.
    
    Args:
        max_attempts: Maximum number of reconnection attempts
        wait_between_attempts: Initial wait time between attempts in seconds
    """
    logger.info("Reconnecting to database...")
    
    # First, dispose of all existing connections
    dispose_engine()
    
    # Wait a bit longer to ensure connections are fully closed
    time.sleep(2)
    
    # Try to reconnect with retries
    last_error = None
    for attempt in range(max_attempts):
        try:
            logger.info(f"Reconnection attempt {attempt + 1}/{max_attempts}")
            initialize_db()
            
            # Test the connection
            if test_connection():
                logger.info("Database reconnection successful")
                return
            else:
                logger.warning(f"Reconnection attempt {attempt + 1} succeeded but connection test failed")
                dispose_engine()
                
        except Exception as e:
            last_error = e
            logger.warning(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_attempts - 1:
                wait_time = wait_between_attempts * (2 ** attempt)  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before next attempt...")
                time.sleep(wait_time)
                dispose_engine()  # Ensure clean state
    
    # If all attempts failed, raise the last error
    if last_error:
        logger.error(f"Failed to reconnect after {max_attempts} attempts")
        raise last_error
    else:
        raise RuntimeError("Failed to reconnect: connection test failed after all attempts")


def test_connection(timeout: int = 5) -> bool:
    """
    Test database connection health with timeout.
    
    Args:
        timeout: Timeout in seconds for the test query
        
    Returns:
        True if connection is healthy, False otherwise
    """
    if not engine or not SessionLocal:
        return False
    
    try:
        # Use a simple query with timeout
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
            return True
    except Exception as e:
        error_str = str(e).lower()
        # Don't log timeout errors as errors, just return False
        if 'timeout' in error_str:
            logger.warning(f"Database connection test timed out after {timeout}s")
        else:
            logger.error(f"Database connection test failed: {str(e)}")
        return False


# Initialize on module import
initialize_db()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Database session
    """
    if not SessionLocal:
        raise RuntimeError("Database connection not configured. Set ALLOYDB_CONNECTION_STRING.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic recovery.
    
    Yields:
        Database session
    """
    if not SessionLocal:
        raise RuntimeError("Database connection not configured. Set ALLOYDB_CONNECTION_STRING.")
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            try:
                yield db
                db.commit()
                return
            except Exception as e:
                db.rollback()
                # Check if it's a connection error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['connection', 'closed', 'lost', 'timeout', 'broken']):
                    logger.warning(f"Database connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    db.close()
                    if attempt < max_retries - 1:
                        # Try to reconnect
                        reconnect_db()
                        continue
                raise
            finally:
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to get database connection after {max_retries} attempts: {str(e)}")
                raise
            time.sleep(0.5)  # Brief pause before retry


def init_db():
    """Initialize database tables (create if not exist)."""
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
    else:
        logger.warning("Cannot initialize database: engine not configured")

