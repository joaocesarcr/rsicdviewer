import sqlite3

def update_database_schema():
    try:
        # Connect to the database
        conn = sqlite3.connect('captions.db')  # Replace with your database name
        cursor = conn.cursor()

        # Check if 'third_description' column exists; if not, add it
        cursor.execute("""
            PRAGMA table_info(images);
        """)
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'third_description' not in columns:
            cursor.execute("""
                ALTER TABLE images ADD COLUMN third_description TEXT;
            """)
            print("Added 'third_description' column.")
        else:
            print("'third_description' column already exists.")

        # Commit the changes
        conn.commit()
        print("Database schema updated successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database_schema()

