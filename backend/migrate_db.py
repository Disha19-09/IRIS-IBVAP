"""
Database Migration Script
Adds event_description column to alerts table
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "alerts.db")

def migrate():
    print("[INFO] Starting database migration...")
    
    if not os.path.exists(DB_PATH):
        print("[INFO] No existing database found. Will be created on first run.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if event_description column already exists
        cursor.execute("PRAGMA table_info(alerts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'event_description' in columns:
            print("[INFO] Database already up to date. event_description column exists.")
        else:
            print("[INFO] Adding event_description column to alerts table...")
            cursor.execute("ALTER TABLE alerts ADD COLUMN event_description TEXT")
            conn.commit()
            print("[SUCCESS] Database migration completed successfully!")
            
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
