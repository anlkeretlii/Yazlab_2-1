import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import Database

def fix_database():
    db = Database()
    print(f"Working with database at: {db.db_path}")
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
         
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Current columns in articles table: {columns}")
         
            if 'original_filename' not in columns:
                print("Adding 'original_filename' column to articles table")
                cursor.execute("ALTER TABLE articles ADD COLUMN original_filename TEXT")
            
         
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Updated columns in articles table: {columns}")
            
            conn.commit()
            print("Database structure updated successfully!")
    
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_database()
    if success:
        print("Database migration completed successfully.")
    else:
        print("Database migration failed.")
