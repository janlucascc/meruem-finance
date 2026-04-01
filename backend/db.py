import os
import sqlite3

# Configuração de Caminhos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE_PATH = os.path.join(INSTANCE_DIR, "meruem.db")

# Garante que a pasta instance existe para o SQLite
os.makedirs(INSTANCE_DIR, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Usuários (com coluna de imagem)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            profile_image TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de Contas de Saldo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_name TEXT NOT NULL,
            current_balance REAL NOT NULL DEFAULT 0,
            reserved_balance REAL NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Transações de Saldo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            custom_category TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES balance_accounts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Tabela de Cartões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            card_name TEXT NOT NULL,
            card_limit REAL NOT NULL DEFAULT 0,
            used_limit REAL NOT NULL DEFAULT 0,
            reserved_limit REAL NOT NULL DEFAULT 0,
            due_day INTEGER NOT NULL,
            image_filename TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Transações de Cartão
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS card_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            custom_category TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES credit_cards (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

# --- FUNÇÕES DE BUSCA (SELECT) ---

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_balance_account(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM balance_accounts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    account = cursor.fetchone()
    conn.close()
    return account

def get_user_cards(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM credit_cards WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    )
    cards = cursor.fetchall()
    conn.close()
    return cards

def get_balance_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM balance_transactions WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_card_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ct.*, cc.card_name
        FROM card_transactions ct
        INNER JOIN credit_cards cc ON cc.id = ct.card_id
        WHERE ct.user_id = ?
        ORDER BY ct.id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_transactions_by_card(card_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM card_transactions 
        WHERE card_id = ? AND user_id = ? 
        ORDER BY id DESC
    """, (card_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- FUNÇÕES DE ATUALIZAÇÃO E EXCLUSÃO (UPDATE/DELETE) ---

def update_user_password(user_id, new_password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    conn.close()

def update_user_image(user_id, filename):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_image = ? WHERE id = ?", (filename, user_id))
    conn.commit()
    conn.close()

def delete_card(card_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM card_transactions WHERE card_id = ? AND user_id = ?", (card_id, user_id))
    cursor.execute("DELETE FROM credit_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
    conn.commit()
    conn.close()