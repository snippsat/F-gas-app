import sqlite3
import os
from datetime import datetime

def backup_database():
    """Create a backup of the existing database if it exists"""
    if os.path.exists('fgas.db'):
        print("Creating backup of existing database...")
        import shutil
        backup_name = f"fgas_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2('fgas.db', backup_name)
        print(f"Backup created as {backup_name}")
        return True
    return False

def migrate_data():
    """Migrate data from old schema to new schema"""
    if not os.path.exists('fgas.db'):
        print("No existing database found.")
        return False
    
    # First, check if the old table structure exists
    conn = sqlite3.connect('fgas.db')
    cursor = conn.cursor()
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fgas_records'")
    if not cursor.fetchone():
        print("No fgas_records table found. No migration needed.")
        conn.close()
        return False
    
    # Create a temporary table with the new schema
    print("Creating temporary table with new schema...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fgas_records_new (
        id TEXT,
        date TEXT,
        comments TEXT,
        filled_kg REAL,
        created_at TEXT,
        PRIMARY KEY (id, date)
    )
    ''')
    
    # Get data from old table
    try:
        print("Fetching existing records...")
        cursor.execute('SELECT id, date, comments, filled_kg, created_at FROM fgas_records')
        records = cursor.fetchall()
        print(f"Found {len(records)} records to migrate.")
        
        # Insert data into new table
        for record in records:
            try:
                cursor.execute('''
                INSERT INTO fgas_records_new (id, date, comments, filled_kg, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''', record)
                print(f"Migrated record: {record[0]} - {record[1]}")
            except sqlite3.IntegrityError:
                print(f"Skipping duplicate record: {record[0]} - {record[1]}")
        
        # Rename tables
        print("Finalizing migration...")
        cursor.execute('DROP TABLE fgas_records')
        cursor.execute('ALTER TABLE fgas_records_new RENAME TO fgas_records')
        
        conn.commit()
        print("Migration completed successfully!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    backed_up = backup_database()
    if backed_up:
        migrate_data()
        print("You can now start your application with the migrated data.")
    else:
        print("No existing database to migrate.") 