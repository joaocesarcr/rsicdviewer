import sqlite3
from lorem import text

def create_and_populate_db():
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('captions.db')
    cursor = conn.cursor()

    # Create the images table with third_description
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        description TEXT,
        new_description TEXT,
        third_description TEXT
    )
    ''')

    # Insert 10 sample records all pointing to the same image
    records_inserted = 0
    for i in range(1, 11):  # 1 to 10
        # Generate unique Lorem Ipsum text for each record
        description = f"Original description #{i}: " + text()[:200]
        new_description = description
        third_description = description
        path = 'images/1.jpeg'  # Same path for all records

        try:
            cursor.execute('''
            INSERT INTO images (path, description, new_description, third_description)
            VALUES (?, ?, ?, ?)
            ''', (path, description, new_description, third_description))
            records_inserted += 1

        except sqlite3.IntegrityError as e:
            print(f"Error inserting record {i} with path '{path}': {e}")
            continue


    # Commit the changes
    conn.commit()
    print(f"\nTest database created and populated successfully!")
    print(f"Inserted {records_inserted} new records")
    
    # Show some sample data
    print("\nSample of inserted data:")
    cursor.execute('SELECT * FROM images LIMIT 3')
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"Path: {row[1]}")
        print(f"Description: {row[2][:50]}...")
        print(f"New Description: {row[3][:50]}...")
        print(f"Third Description: {row[4][:50]}...")
    
    # Show total count
    cursor.execute('SELECT COUNT(*) FROM images')
    total_records = cursor.fetchone()[0]
    print(f"\nTotal records in database: {total_records}")

    # Close the connection
    conn.close()

if __name__ == "__main__":
    create_and_populate_db()
