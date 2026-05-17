
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Dany@789",
    database="smartdesk"
)

cursor = conn.cursor(buffered=True)
print("Database Connected Successfully")