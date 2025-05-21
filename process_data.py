import sqlite3
import os
from werkzeug.utils import secure_filename
import requests
from datetime import datetime, timedelta

SERVER_URL = ""


def process_data(file_path):
    if "stock" in file_path:
        import sqlite3

        source_conn = sqlite3.connect(file_path)
        source_cursor = source_conn.cursor()

        destination_conn = sqlite3.connect("smc.db")
        destination_cursor = destination_conn.cursor()

        destination_cursor.execute("DELETE FROM stock")
        print("deleted all rows from stock table")

        source_cursor.execute("SELECT * FROM stock")
        rows = source_cursor.fetchall()
        destination_cursor.executemany(
            "INSERT INTO stock VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        print("inserted all rows from stock table")
        headers = {"content-type": "text/plain"}
        requests.post(
            SERVER_URL, data=str(f"DB Updated. {len(rows)} Rows Total"), headers=headers
        )

        destination_conn.commit()

        source_conn.close()
        destination_conn.close()

        os.remove(file_path)
    if "sales" in file_path:
        import sqlite3

        source_conn = sqlite3.connect(file_path)
        source_cursor = source_conn.cursor()

        destination_conn = sqlite3.connect("smc.db")
        destination_cursor = destination_conn.cursor()
        if "daily" in file_path:
            date = datetime.strftime(datetime.now() - timedelta(1), "%Y-%m-%d")
            destination_cursor.execute(
                f"""DELETE FROM sales WHERE EntryDate>= '{date}'"""
            )
            source_cursor.execute("SELECT * FROM sales")
            rows = source_cursor.fetchall()
            destination_cursor.executemany(
                """
            INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
                rows,
            )
            print("inserted all rows from stock table")
        headers = {"content-type": "text/plain"}
        requests.post(
            "SERVER_URL",
            data=str(f"SALES Database Updated. {len(rows)} Rows (15 mins)"),
            headers=headers,
        )

        destination_conn.commit()
        source_conn.close()
        destination_conn.close()
        os.remove(file_path)
    else:
        date = datetime.strftime(datetime.now() - timedelta(20), "%Y-%m-%d")
        destination_cursor.execute(f"""DELETE FROM sales WHERE EntryDate>= '{date}'""")
        source_cursor.execute("SELECT * FROM sales")
        rows = source_cursor.fetchall()
        destination_cursor.executemany(
            """
        INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            rows,
        )
        print("inserted all rows from stock table")
        headers = {"content-type": "text/plain"}
        requests.post(
            SERVER_URL,
            data=str(f"SALES Database Updated. {len(rows)} Rows (4 hrs)"),
            headers=headers,
        )

        destination_conn.commit()
        source_conn.close()
        destination_conn.close()
        os.remove(file_path)
