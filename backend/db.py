import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    # Conecta ao Postgres
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Usuários (SERIAL no lugar de AUTOINCREMENT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de Contas de Saldo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            account_name TEXT NOT NULL,
            current_balance NUMERIC NOT NULL DEFAULT 0,
            reserved_balance NUMERIC NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transações de Saldo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_transactions (
            id SERIAL PRIMARY KEY,
            account_id INTEGER NOT NULL REFERENCES balance_accounts(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            action_type TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            category TEXT,
            custom_category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de Cartões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            card_name TEXT NOT NULL,
            card_limit NUMERIC NOT NULL DEFAULT 0,
            used_limit NUMERIC NOT NULL DEFAULT 0,
            reserved_limit NUMERIC NOT NULL DEFAULT 0,
            due_day INTEGER NOT NULL,
            image_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transações de Cartão
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS card_transactions (
            id SERIAL PRIMARY KEY,
            card_id INTEGER NOT NULL REFERENCES credit_cards(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            action_type TEXT NOT NULL,
            amount NUMERIC NOT NULL,
            category TEXT,
            custom_category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# --- FUNÇÕES DE BUSCA (SELECT) ---
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_balance_account(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM balance_accounts WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
    account = cursor.fetchone()
    conn.close()
    return account

def get_user_cards(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM credit_cards WHERE user_id = %s ORDER BY id DESC", (user_id,))
    cards = cursor.fetchall()
    conn.close()
    return cards

def get_balance_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM balance_transactions WHERE user_id = %s ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_card_transactions(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT ct.*, cc.card_name
        FROM card_transactions ct
        INNER JOIN credit_cards cc ON cc.id = ct.card_id
        WHERE ct.user_id = %s
        ORDER BY ct.id DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_transactions_by_card(card_id, user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM card_transactions WHERE card_id = %s AND user_id = %s ORDER BY id DESC", (card_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- FUNÇÕES DE ATUALIZAÇÃO E EXCLUSÃO (UPDATE/DELETE) ---
def update_user_password(user_id, new_password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_password_hash, user_id))
    conn.commit()
    conn.close()

def update_user_image(user_id, filename):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_image = %s WHERE id = %s", (filename, user_id))
    conn.commit()
    conn.close()

def delete_card(card_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM card_transactions WHERE card_id = %s AND user_id = %s", (card_id, user_id))
    cursor.execute("DELETE FROM credit_cards WHERE id = %s AND user_id = %s", (card_id, user_id))
    conn.commit()
    conn.close()