"""
Duckslator Database Connection Module

This module establishes and manages the connection to MongoDB using Motor,
an asynchronous Python driver for MongoDB. It provides database and collection
references for use throughout the application.

Features:
    - Asynchronous MongoDB connection using Motor
    - Automatic connection pooling and management
    - Environment-based configuration
    - Fallback database naming for development

Dependencies:
    - motor: Asynchronous MongoDB driver for Python
    - python-dotenv: For environment variable loading

Author: Your Name
Version: 1.0.0
"""

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# MongoDB connection URI from environment variables
# Format: mongodb://username:password@host:port/database
# Example: mongodb://localhost:27017/duckslator
MONGO_URI = os.getenv("MONGODB_URI")

# Validate that required environment variable is set
if not MONGO_URI:
    raise RuntimeError(
        "Missing MONGODB_URI in .env file. "
        "Please add your MongoDB connection string to continue. "
        "Example: mongodb://localhost:27017/duckslator"
    )

# =============================================================================
# DATABASE CLIENT INITIALIZATION
# =============================================================================

# Initialize asynchronous MongoDB client
# Motor provides async/await support for MongoDB operations
client = AsyncIOMotorClient(
    MONGO_URI,
    # Connection pool settings for optimal performance
    maxPoolSize=50,           # Maximum connections in pool
    minPoolSize=10,           # Minimum connections to maintain
    maxIdleTimeMS=30000,      # Close idle connections after 30 seconds
    serverSelectionTimeoutMS=5000,  # Timeout for server selection
    connectTimeoutMS=10000,   # Timeout for initial connection
    socketTimeoutMS=5000      # Timeout for socket operations
)

# =============================================================================
# DATABASE AND COLLECTION REFERENCES
# =============================================================================

# Get the default database from the connection URI
# If URI doesn't specify a database name, this will be None
default_db = client.get_default_database()

# Use default database if specified in URI, otherwise use "duckslator"
# This provides flexibility for different deployment environments
db = default_db if default_db is not None else client["duckslator"]

# Reference to the users collection
# This collection stores user accounts and authentication data
users_coll = db["users"]

# =============================================================================
# DATABASE HEALTH CHECK
# =============================================================================

async def check_database_connection():
    """
    Verify that the database connection is working.
    
    This function can be called during application startup to ensure
    the MongoDB connection is established and responsive.
    
    Returns:
        bool: True if connection is successful, False otherwise
        
    Usage:
        >>> await check_database_connection()
        True
    """
    try:
        # Ping the database to verify connectivity
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

async def get_database_info():
    """
    Get information about the connected database.
    
    Returns:
        dict: Database information including name, collections, and stats
        
    Usage:
        >>> info = await get_database_info()
        >>> print(f"Connected to: {info['name']}")
    """
    try:
        # Get database statistics
        stats = await db.command("dbStats")
        
        # Get list of collections
        collections = await db.list_collection_names()
        
        return {
            "name": db.name,
            "collections": collections,
            "stats": stats
        }
    except Exception as e:
        print(f"Failed to get database info: {e}")
        return {"error": str(e)}

# =============================================================================
# CONNECTION MANAGEMENT
# =============================================================================

async def close_database_connection():
    """
    Properly close the database connection.
    
    This function should be called during application shutdown
    to ensure clean connection termination and resource cleanup.
    
    Usage:
        >>> await close_database_connection()
        >>> print("Database connection closed")
    """
    try:
        # Close the client connection
        client.close()
        print("✅ Database connection closed successfully")
    except Exception as e:
        print(f"❌ Error closing database connection: {e}")

# =============================================================================
# COLLECTION UTILITIES
# =============================================================================

async def create_collection_indexes():
    """
    Create necessary database indexes for optimal performance.
    
    This function sets up indexes on commonly queried fields to improve
    query performance and enforce data constraints.
    
    Indexes Created:
        - users.email: Unique index for user authentication
        - users.google_id: Index for Google OAuth lookups
        - jobs.user_id: Index for user job queries
        - jobs.status: Index for job status filtering
        
    Usage:
        >>> await create_collection_indexes()
        >>> print("Database indexes created")
    """
    try:
        # Create unique index on user email
        await users_coll.create_index("email", unique=True)
        
        # Create index on Google ID for OAuth users
        await users_coll.create_index("google_id", sparse=True)
        
        # Create index on user ID for job queries
        await db.jobs.create_index("user_id")
        
        # Create index on job status for filtering
        await db.jobs.create_index("status")
        
        # Create index on creation date for sorting
        await db.jobs.create_index("created_at")
        
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create database indexes: {e}")

# =============================================================================
# DEVELOPMENT UTILITIES
# =============================================================================

async def reset_database():
    """
    Reset the database for development/testing purposes.
    
    WARNING: This function will delete all data in the database.
    Only use in development environments.
    
    Usage:
        >>> await reset_database()
        >>> print("Database reset complete")
    """
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ Cannot reset database in production environment")
        return False
    
    try:
        # Drop all collections
        await db.drop_collection("users")
        await db.drop_collection("jobs")
        
        # Recreate indexes
        await create_collection_indexes()
        
        print("✅ Database reset complete")
        return True
        
    except Exception as e:
        print(f"❌ Failed to reset database: {e}")
        return False