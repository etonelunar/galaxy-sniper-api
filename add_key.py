import sqlite3
import secrets

def generate_key():
    return secrets.token_urlsafe(16)  # генерирует строку типа "aB3dEfGhIjKlMnOp"

conn = sqlite3.connect('licenses.db')
c = conn.cursor()

# Создадим таблицу, если её нет (на случай, если мы ещё не создавали БД)
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

# Генерируем ключ
key = generate_key()
license_type = 'premium'  # или 'basic'

c.execute("INSERT INTO licenses (license_key, license_type) VALUES (?, ?)", (key, license_type))
conn.commit()
conn.close()

print(f"Сгенерирован ключ: {key}")
print(f"Тип: {license_type}")