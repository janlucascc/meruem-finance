import os
import uuid
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, 
    url_for, session, flash, jsonify, send_from_directory
)

# Leitura do arquivo .env (Chave do BD)
load_dotenv()

# Importando o blueprint de autenticação
from routes.auth import auth_bp

# Importando as funções do banco de dados
from db import (
    init_db, get_connection, get_user_by_email, get_user_by_id,
    get_user_balance_account, get_user_cards, get_balance_transactions, 
    get_card_transactions, delete_card, get_transactions_by_card, update_user_image
)

# ==========================================
# CONFIGURAÇÃO DE PASTAS (O PADRÃO SÊNIOR)
# ==========================================
# 1. Descobre o caminho exato da pasta onde o app.py está rodando (pasta backend)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Volta um nível (raiz do projeto) e aponta para a pasta frontend
FRONTEND_DIR = os.path.join(os.path.dirname(BACKEND_DIR), 'frontend')

# 3. Inicializa o Flask ensinando exatamente onde estão os arquivos visuais
app = Flask(__name__, 
            template_folder=os.path.join(FRONTEND_DIR, 'templates'), 
            static_folder=os.path.join(FRONTEND_DIR, 'static'))

app.secret_key = "meruem_secret_key_123"

# 4. Configuração de Uploads (Salva imagens dentro do frontend/static/uploads)
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
DEFAULT_CATEGORIES = ["Moradia", "Alimentação", "Transporte", "Lazer", "Emergência"]

app.register_blueprint(auth_bp)

# ==========================================
# INICIALIZAÇÃO PARA O RENDER (GUNICORN)
# ==========================================
init_db()

# ==========================================
# FILTROS JINJA2 E CONTEXTO GLOBAL
# ==========================================
@app.template_filter('brl')
def brl_format(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter('format_datetime')
def format_datetime(value):
    if not value: return ""
    # O Postgres já retorna um objeto datetime nativo
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y às %H:%M')
    try:
        dt = datetime.strptime(str(value)[:19], '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d/%m/%Y às %H:%M')
    except:
        return value

@app.template_filter('action_name')
def action_name(value):
    actions = {
        'use': 'Gasto adicionado', 'pay': 'Fatura paga',
        'reserve': 'Reservado', 'unreserve': 'Reserva liberada',
        'commit': 'Comprometido', 'add': 'Saldo adicionado',
        'remove': 'Saldo removido'
    }
    return actions.get(value, value)

@app.context_processor
def inject_user_data():
    if "user_id" in session:
        try:
            user = get_user_by_id(session["user_id"])
            if user:
                account = get_user_balance_account(user["id"])
                current_balance = account["current_balance"] if account else 0
                
                try:
                    profile_img = user["profile_image"]
                except (IndexError, KeyError):
                    profile_img = None
                
                return {
                    "user_name": user["full_name"],
                    "user_profile_image": profile_img,
                    "sidebar_balance": current_balance
                }
        except Exception as e:
            print(f"Erro ao carregar dados do usuário: {e}")
            
    return {"user_name": "Usuário", "user_profile_image": None, "sidebar_balance": 0}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("home"))
        return view_func(*args, **kwargs)
    return wrapped

# ==========================================
# ROTAS DE PÁGINAS
# ==========================================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    account = get_user_balance_account(user_id)
    cards = get_user_cards(user_id)

    total_balance = account["current_balance"] if account else 0
    total_balance_reserved = account["reserved_balance"] if account else 0
    total_limit = sum(c["card_limit"] for c in cards) if cards else 0
    total_used = sum(c["used_limit"] for c in cards) if cards else 0
    total_card_reserved = sum(c["reserved_limit"] for c in cards) if cards else 0

    return render_template(
        "dashboard.html",
        total_balance=total_balance, total_balance_reserved=total_balance_reserved,
        total_card_reserved=total_card_reserved, total_limit=total_limit, total_used=total_used
    )

@app.route("/cards")
@login_required
def cards():
    user_id = session["user_id"]
    db_cards = get_user_cards(user_id)
    card_history = get_card_transactions(user_id)
    
    total_limit = sum(c["card_limit"] for c in db_cards) if db_cards else 0
    total_used = sum(c["used_limit"] for c in db_cards) if db_cards else 0
    total_reserved_cards = sum(c["reserved_limit"] for c in db_cards) if db_cards else 0

    card_snapshot = {"total_limit": total_limit, "total_used": total_used, "total_reserved": total_reserved_cards, "cards": []}

    for c in db_cards:
        available = c["card_limit"] - c["used_limit"] - c["reserved_limit"]
        utilization = round((c["used_limit"] / c["card_limit"]) * 100, 1) if c["card_limit"] > 0 else 0
        this_card_history = get_transactions_by_card(c["id"], user_id)

        card_snapshot["cards"].append({
            "id": c["id"], "name": c["card_name"], "card_limit": c["card_limit"],
            "used": c["used_limit"], "reserved": c["reserved_limit"], "available": available,
            "utilization": utilization, "statement_day": c["due_day"],
            "image_path": f"uploads/{c['image_filename']}" if c["image_filename"] else None,
            "history": this_card_history
        })

    return render_template("cards.html", card_snapshot=card_snapshot, categories=DEFAULT_CATEGORIES, card_history=card_history)

@app.route("/balance")
@login_required
def balance():
    user_id = session["user_id"]
    account = get_user_balance_account(user_id)
    balance_history = get_balance_transactions(user_id)

    balance_snapshot = {"total_balance": account["current_balance"] if account else 0, "total_reserved": account["reserved_balance"] if account else 0, "accounts": []}

    if account:
        balance_snapshot["accounts"].append({
            "id": account["id"], "name": account["account_name"], "current_balance": account["current_balance"],
            "reserved_balance": account["reserved_balance"],
            "added": sum(t["amount"] for t in balance_history if t["action_type"] == "add"),
            "spent": sum(t["amount"] for t in balance_history if t["action_type"] == "remove")
        })

    return render_template("balance.html", balance_snapshot=balance_snapshot, categories=DEFAULT_CATEGORIES, balance_history=balance_history)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

# ==========================================
# AÇÕES E UPLOADS COMPLETOS
# ==========================================
@app.route("/upload_profile_image", methods=["POST"])
@login_required
def upload_profile_image():
    user_id = session["user_id"]
    file = request.files.get("profile_pic")

    if file and file.filename:
        if allowed_file(file.filename):
            extension = file.filename.rsplit(".", 1)[1].lower()
            filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{extension}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            update_user_image(user_id, filename)
            flash("Foto de perfil atualizada!", "success")
        else:
            flash("Formato de imagem inválido.", "error")
    return redirect(request.referrer or url_for('dashboard'))

@app.route("/cards/<int:card_id>/delete", methods=["POST"])
@login_required
def delete_card_route(card_id):
    user_id = session["user_id"]
    delete_card(card_id, user_id)
    flash("Cartão removido com sucesso.", "success")
    return redirect(url_for("cards"))

@app.route("/balance/action", methods=["POST"])
@login_required
def balance_action():
    user_id = session["user_id"]
    account = get_user_balance_account(user_id)
    if not account:
        flash("Conta não encontrada.", "error")
        return redirect(url_for("balance"))

    action_type = request.form.get("action_type", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "Geral").strip() # Categoria Opcional
    new_account_name = request.form.get("account_name", "").strip() # Atualização de Nome

    try:
        amount = float(amount_raw.replace(",", ".")) # Resolve problema da vírgula
    except ValueError:
        flash("Valor inválido.", "error")
        return redirect(url_for("balance"))

    if amount <= 0:
        flash("O valor deve ser maior que zero.", "error")
        return redirect(url_for("balance"))

    current_balance = float(account["current_balance"])
    reserved_balance = float(account["reserved_balance"])

    if action_type == "add":
        current_balance += amount
    elif action_type == "remove":
        current_balance -= amount
    elif action_type == "reserve":
        if amount > (current_balance - reserved_balance):
            flash("Saldo livre insuficiente para guardar.", "error")
            return redirect(url_for("balance"))
        reserved_balance += amount
    elif action_type == "unreserve":
        if amount > reserved_balance:
            flash("Valor excede reserva.", "error")
            return redirect(url_for("balance"))
        reserved_balance -= amount

    conn = get_connection()
    cursor = conn.cursor()
    
    # Atualiza saldo e (se fornecido no 'add') atualiza o nome da conta
    cursor.execute("UPDATE balance_accounts SET current_balance = %s, reserved_balance = %s WHERE id = %s", (current_balance, reserved_balance, account["id"]))
    
    if action_type == "add" and new_account_name:
        cursor.execute("UPDATE balance_accounts SET account_name = %s WHERE id = %s", (new_account_name, account["id"]))

    cursor.execute("""
        INSERT INTO balance_transactions (account_id, user_id, action_type, amount, category, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (account["id"], user_id, action_type, amount, category, description))
    
    conn.commit()
    conn.close()

    flash("Movimentação registrada.", "success")
    return redirect(url_for("balance"))

@app.route("/cards/create", methods=["POST"])
@login_required
def create_card():
    user_id = session["user_id"]
    card_name = request.form.get("card_name", "").strip()
    card_limit_raw = request.form.get("card_limit", "").strip()
    due_day = request.form.get("due_day", "").strip()
    image_file = request.files.get("card_image")

    try:
        card_limit = float(card_limit_raw.replace(",", ".")) # Resolve problema da vírgula
        due_day = int(due_day)
    except ValueError:
        flash("Dados inválidos.", "error")
        return redirect(url_for("cards"))

    image_filename = None
    if image_file and image_file.filename and allowed_file(image_file.filename):
        extension = image_file.filename.rsplit(".", 1)[1].lower()
        image_filename = f"{uuid.uuid4().hex}.{extension}"
        image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(image_filename)))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO credit_cards (user_id, card_name, card_limit, used_limit, reserved_limit, due_day, image_filename)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, card_name, card_limit, 0, 0, due_day, image_filename))
    conn.commit()
    conn.close()

    flash("Cartão cadastrado.", "success")
    return redirect(url_for("cards"))

@app.route("/cards/<int:card_id>/action", methods=["POST"])
@login_required
def card_action(card_id):
    user_id = session["user_id"]
    action_type = request.form.get("action_type", "").strip()
    amount_raw = request.form.get("amount", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "Geral").strip()

    try:
        amount = float(amount_raw.replace(",", "."))
    except ValueError:
        flash("Valor inválido.", "error")
        return redirect(url_for("cards"))

    # AQUI ESTÁ A CORREÇÃO: Usar a função que já devolve como Dicionário Seguro
    db_cards = get_user_cards(user_id)
    card = next((c for c in db_cards if c["id"] == card_id), None)

    if not card:
        flash("Cartão não encontrado.", "error")
        return redirect(url_for("cards"))

    # Agora o Python consegue ler perfeitamente as chaves com nomes
    used_limit = float(card["used_limit"])
    reserved_limit = float(card["reserved_limit"])
    card_limit = float(card["card_limit"])
    available = card_limit - used_limit - reserved_limit

    if action_type == "use":
        if amount > available:
            flash("Limite insuficiente.", "error")
            return redirect(url_for("cards"))
        used_limit += amount
    elif action_type == "pay":
        used_limit = max(0, used_limit - amount)
    elif action_type == "reserve":
        if amount > available:
            flash("Limite insuficiente.", "error")
            return redirect(url_for("cards"))
        reserved_limit += amount
    elif action_type == "unreserve":
        reserved_limit = max(0, reserved_limit - amount)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE credit_cards SET used_limit = %s, reserved_limit = %s WHERE id = %s", (used_limit, reserved_limit, card_id))
    cursor.execute("""
        INSERT INTO card_transactions (card_id, user_id, action_type, amount, category, description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (card_id, user_id, action_type, amount, category, description))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Ação do cartão registrada.", "success")
    return redirect(url_for("cards"))

@app.route("/reserve/<int:tx_id>/release", methods=["POST"])
@login_required
def release_reserve(tx_id):
    user_id = session["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    
    # Busca a reserva específica pelo ID
    cursor.execute("SELECT card_id, amount FROM card_transactions WHERE id = %s AND user_id = %s", (tx_id, user_id))
    tx = cursor.fetchone()
    
    if tx:
        card_id, amount = tx[0], float(tx[1])
        # 1. Devolve o limite de volta para o cartão
        cursor.execute("UPDATE credit_cards SET reserved_limit = GREATEST(0, reserved_limit - %s) WHERE id = %s", (amount, card_id))
        # 2. Exclui definitivamente o registro da reserva para ela sumir da tela
        cursor.execute("DELETE FROM card_transactions WHERE id = %s", (tx_id,))
        conn.commit()
        flash("Reserva liberada e removida com sucesso!", "success")
        
    cursor.close()
    conn.close()
    return redirect(url_for("cards"))

@app.route("/reserve/<int:tx_id>/edit", methods=["POST"])
@login_required
def edit_reserve(tx_id):
    user_id = session["user_id"]
    new_amount_raw = request.form.get("amount", "").strip()
    new_desc = request.form.get("description", "").strip()
    new_cat = request.form.get("category", "Geral").strip()

    try:
        new_amount = float(new_amount_raw.replace(",", "."))
    except ValueError:
        flash("Valor inválido.", "error")
        return redirect(url_for("cards"))

    conn = get_connection()
    cursor = conn.cursor()
    
    # Busca a reserva original
    cursor.execute("SELECT card_id, amount FROM card_transactions WHERE id = %s AND user_id = %s", (tx_id, user_id))
    tx = cursor.fetchone()
    
    if tx:
        card_id, old_amount = tx[0], float(tx[1])
        diff = new_amount - old_amount # Calcula se o valor aumentou ou diminuiu

        # Checa se o cartão tem limite suficiente para cobrir o aumento (se houver)
        cursor.execute("SELECT card_limit, used_limit, reserved_limit FROM credit_cards WHERE id = %s", (card_id,))
        card = cursor.fetchone()
        if card:
            available = float(card[0]) - float(card[1]) - float(card[2])
            if diff > available:
                flash("Limite insuficiente para aumentar a reserva.", "error")
                cursor.close()
                conn.close()
                return redirect(url_for("cards"))

            # Atualiza o limite do cartão e modifica a transação
            cursor.execute("UPDATE credit_cards SET reserved_limit = reserved_limit + %s WHERE id = %s", (diff, card_id))
            cursor.execute("UPDATE card_transactions SET amount = %s, description = %s, category = %s WHERE id = %s", (new_amount, new_desc, new_cat, tx_id))
            conn.commit()
            flash("Reserva atualizada com sucesso!", "success")
            
    cursor.close()
    conn.close()
    return redirect(url_for("cards"))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)