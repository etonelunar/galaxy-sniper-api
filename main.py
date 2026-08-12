from flask import Flask, request, jsonify
import sqlite3
import datetime
import os

app = Flask(__name__)

# --- Имя файла базы данных ---
DB_NAME = "licenses.db"

# --- Инициализация базы данных при первом запуске ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Таблица с лицензиями
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            license_type TEXT NOT NULL,
            hwid TEXT,
            status TEXT DEFAULT 'active',
            activated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Таблица настроек (для минимальной версии)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    # Устанавливаем начальную минимальную версию, если её нет
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('min_version', '1.0.0')")
    conn.commit()
    conn.close()

init_db()

# --- Вспомогательные функции ---
def get_license(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM licenses WHERE license_key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row

def update_license(key, hwid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE licenses SET hwid = ?, status = 'used', activated_at = ? WHERE license_key = ?",
              (hwid, datetime.datetime.now(), key))
    conn.commit()
    conn.close()

def get_min_version():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'min_version'")
    row = c.fetchone()
    conn.close()
    return row[0] if row else "1.0.0"

# --- Эндпоинт для активации ---
@app.route('/activate', methods=['POST'])
def activate():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    version = data.get('version')
    
    if not key or not hwid:
        return jsonify({'status': 'error', 'detail': 'Не указаны key или hwid'}), 400
    
    row = get_license(key)
    if not row:
        return jsonify({'status': 'error', 'detail': 'Неверный ключ'}), 400
    
    # row: (id, license_key, license_type, hwid, status, activated_at, created_at)
    license_type, db_hwid, status = row[2], row[3], row[4]
    
    if status == 'blocked':
        return jsonify({'status': 'error', 'detail': 'Ключ заблокирован'}), 403
    if status == 'used':
        if db_hwid == hwid:
            min_ver = get_min_version()
            return jsonify({'status': 'success', 'type': license_type, 'hwid': hwid, 'min_version': min_ver})
        else:
            return jsonify({'status': 'error', 'detail': 'Ключ уже активирован на другом устройстве'}), 400
    if status == 'active':
        update_license(key, hwid)
        min_ver = get_min_version()
        return jsonify({'status': 'success', 'type': license_type, 'hwid': hwid, 'min_version': min_ver})
    
    return jsonify({'status': 'error', 'detail': 'Неизвестная ошибка'}), 400

# --- Эндпоинт для проверки уже активированного ключа ---
@app.route('/check', methods=['POST'])
def check():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')
    version = data.get('version')
    
    if not key or not hwid:
        return jsonify({'status': 'error', 'detail': 'Не указаны key или hwid'}), 400
    
    row = get_license(key)
    if not row:
        return jsonify({'status': 'error', 'detail': 'Неверный ключ'}), 400
    
    license_type, db_hwid, status = row[2], row[3], row[4]
    
    if status == 'blocked':
        return jsonify({'status': 'error', 'detail': 'Ключ заблокирован'}), 403
    if status != 'used':
        return jsonify({'status': 'error', 'detail': 'Ключ не активирован'}), 400
    if db_hwid != hwid:
        return jsonify({'status': 'error', 'detail': 'HWID не совпадает с привязанным'}), 400
    
    min_ver = get_min_version()
    return jsonify({'status': 'success', 'type': license_type, 'hwid': hwid, 'min_version': min_ver})

# --- Просто для проверки, что сервер работает ---
@app.route('/')
def root():
    return {"message": "Galaxy Sniper API работает"}

# --- Запуск сервера ---
if __name__ == '__main__':
    # Для Render порт будет передан через переменную окружения, но мы пропишем 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)