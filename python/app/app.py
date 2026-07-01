import os
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

# Подключение к БД из переменных окружения
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "mydb")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

@app.route('/')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        data = request.json.get('data')
        cur.execute("INSERT INTO items (content) VALUES (%s)", (data,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "inserted"})
    else:
        cur.execute("SELECT id, content FROM items ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"id": r[0], "content": r[1]} for r in rows])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)