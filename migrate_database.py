#!/usr/bin/env python3
"""
Database migration script to add missing subscription columns to the users table.
"""

import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database file path
DB_FILE = 'mindmap.db'

print("Loaded Stripe key:", os.getenv("STRIPE_SECRET_KEY"))

def migrate_database():
    """Add missing subscription columns to the users table"""
    
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found!")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("Current columns in users table:", columns)
        
        # Columns to add
        columns_to_add = [
            ('is_subscribed', 'BOOLEAN DEFAULT 0'),
            ('stripe_customer_id', 'VARCHAR(100)'),
            ('trial_start_date', 'DATETIME'),
            ('trial_end_date', 'DATETIME'),
            ('subscription_end_date', 'DATETIME')
        ]
        
        # Add missing columns
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print("Updated columns in users table:", new_columns)
        
        conn.close()
        print("Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("Starting database migration...")
    success = migrate_database()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!") 