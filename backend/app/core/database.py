"""
Database configuration and session management
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create sync engine for initial setup - commented out for now
# sync_engine = create_engine(
#     settings.DATABASE_URL,
#     pool_size=settings.DATABASE_POOL_SIZE,
#     max_overflow=settings.DATABASE_MAX_OVERFLOW,
#     pool_pre_ping=True,
#     echo=settings.DEBUG,
# )

# Create async engine for application use
async_database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
async_engine = create_async_engine(
    async_database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Session makers - sync session commented out for now
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Declarative base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


# def get_db() -> Session:
#     """Dependency to get database session (sync)"""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


async def get_async_db() -> AsyncSession:
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session():
    """Context manager for database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models import user, scan, vulnerability, report, conversation
        
        async with async_engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {str(e)}")
        raise


async def drop_tables():
    """Drop all database tables (for testing)"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        logger.info("✅ Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"❌ Error dropping database tables: {str(e)}")
        raise


class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def health_check() -> bool:
        """Check database connectivity"""
        try:
            async with get_db_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    @staticmethod
    async def get_db_info():
        """Get database information"""
        try:
            async with get_db_session() as session:
                result = await session.execute("""
                    SELECT 
                        version() as version,
                        current_database() as database,
                        current_user as user,
                        inet_server_addr() as host,
                        inet_server_port() as port
                """)
                return dict(result.fetchone()._mapping)
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return None


# Export database manager instance
db_manager = DatabaseManager()