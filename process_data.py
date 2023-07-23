import sqlite3
import os
from werkzeug.utils import secure_filename

def process_data(file_path):
    import sqlite3

    source_conn = sqlite3.connect(file_path)
    source_cursor = source_conn.cursor()

    destination_conn = sqlite3.connect('smc.db')
    destination_cursor = destination_conn.cursor()

    destination_cursor.execute('DELETE FROM stock')
    print("deleted all rows from stock table")

    source_cursor.execute('SELECT * FROM stock')
    rows = source_cursor.fetchall()
    destination_cursor.executemany('INSERT INTO stock VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', rows)  # Replace '...' with the appropriate number of '?' for your table columns
    print("inserted all rows from stock table")

    destination_conn.commit()

    source_conn.close()
    destination_conn.close()

    os.remove(file_path)
