"""
Migration runner using existing application infrastructure
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.config import get_db_session
from sqlalchemy import text


async def run_migration():
    """Run the migration to add missing columns"""
    
    migration_sql = """
    -- Add best_streak column
    ALTER TABLE user_analytics 
    ADD COLUMN IF NOT EXISTS best_streak INTEGER DEFAULT 0;

    -- Add total_interviews column  
    ALTER TABLE user_analytics
    ADD COLUMN IF NOT EXISTS total_interviews INTEGER DEFAULT 0;

    -- Update existing records to set default values
    UPDATE user_analytics 
    SET best_streak = COALESCE(streak, 0)
    WHERE best_streak IS NULL;

    UPDATE user_analytics
    SET total_interviews = 0
    WHERE total_interviews IS NULL;
    """
    
    try:
        # Use the existing database session
        async for db_session in get_db_session():
            print("Running migration to add UserAnalytics columns...")
            
            # Execute the migration
            await db_session.execute(text(migration_sql))
            await db_session.commit()
            
            print("✅ Migration completed successfully!")
            print("✅ Added best_streak column (INTEGER, DEFAULT 0)")
            print("✅ Added total_interviews column (INTEGER, DEFAULT 0)")
            print("✅ Updated existing records with default values")
            
            break  # Exit the async generator
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_migration())