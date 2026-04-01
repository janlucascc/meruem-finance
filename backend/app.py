import os
import uuid
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    send_from_directory
)

# 1. Importando o blueprint de autenticação
from routes.auth import auth_bp

# 2. Importando as funções do banco de dados (Incluídas as novas funções)
from db import (
    init_db, 
    get_connection, 
    get_user_by_email, 
    get_user_by_id,
    get_user_balance_account, 
    get_user_cards, 
    get_balance_transactions, 
    get_card_transactions,
    delete_card,
    get_transactions_by_card,
    update_user_image
)

app = Flask(__name__)

app.secret_key = "meruem_secret_key_123"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

DEFAULT_CATEGORIES = ["Moradia", "Alimentação", "Transporte", "Lazer", "Emergência"]

# Registrando o Blueprint
app.register_blueprint(auth_bp)

# ==========================================
# FILTROS JINJA2 E CONTEXTO GLOBAL
# ==========================================

@app.template_filter('brl')
def brl_format(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

@app.template_filter('format_datetime')
def format_datetime(value):
    if not value: return ""
    try:
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d/%m/%Y às %H:%M')
    except:
        return value

@app.template_filter('action_name')
def action_name(value):
    actions = {
        'use': 'Gasto adicionado',
        'pay': 'Fatura paga',
        'reserve': 'Reservado',
        'unreserve': 'Reserva liberada',
        'commit': 'Comprometido',
        'add': 'Saldo adicionado',
        'remove': 'Saldo removido'
    }
    return actions.get(value, value)

# Esta função faz com que user_name e user_profile_image estejam disponíveis em QUALQUER HTML
@app.context_processor
def inject_user_data():
    if "user_id" in session:
        try:
            user = get_user_by_id(session["user_id"])
            if user:
                # Tentamos pegar a imagem, se a coluna não existir, usamos None
                try:
                    profile_img = user["profile_image"]
                except (IndexError, KeyError):
                    profile_img = None
                
                return {
                    "user_name": user["full_name"],
                    "user_profile_image": profile_img
                }
        except Exception as e:
            print(f"Erro ao carregar dados do usuário: {e}")
            
    return {"user_name": "Usuário", "user_profile_image": None}


# =========================================
# UTILITÁRIOS E DECORADORES
# =========================================

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
        total_balance=total_balance,
        total_balance_reserved=total_balance_reserved,
        total_card_reserved=total_card_reserved,
        total_limit=total_limit,
        total_used=total_used
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

    card_snapshot = {
        "total_limit": total_limit,
        "total_used": total_used,
        "total_reserved": total_reserved_cards,
        "cards": []
    }

    for c in db_cards:
        available = c["card_limit"] - c["used_limit"] - c["reserved_limit"]
        utilization = round((c["used_limit"] / c["card_limit"]) * 100, 1) if c["card_limit"] > 0 else 0
        this_card_history = get_transactions_by_card(c["id"], user_id)

        card_snapshot["cards"].append({
            "id": c["id"],
            "name": c["card_name"],
            "card_limit": c["card_limit"],
            "used": c["used_limit"],
            "reserved": c["reserved_limit"],
            "available": available,
            "utilization": utilization,
            "statement_day": c["due_day"],
            "image_path": f"uploads/{c['image_filename']}" if c["image_filename"] else None,
            "history": this_card_history
        })

    return render_template(
        "cards.html",
        card_snapshot=card_snapshot,
        categories=DEFAULT_CATEGORIES,
        card_history=card_history
    )

@app.route("/balance")
@login_required
def balance():
    user_id = session["user_id"]
    account = get_user_balance_account(user_id)
    balance_history = get_balance_transactions(user_id)

    balance_snapshot = {
        "total_balance": account["current_balance"] if account else 0,
        "total_reserved": account["reserved_balance"] if account else 0,
        "accounts": []
    }

    if account:
        balance_snapshot["accounts"].append({
            "id": account["id"],
            "name": account["account_name"],
            "current_balance": account["current_balance"],
            "reserved_balance": account["reserved_balance"],
            "added": sum(t["amount"] for t in balance_history if t["action_type"] == "add"),
            "spent": sum(t["amount"] for t in balance_history if t["action_type"] == "remove")
        })

    return render_template(
        "balance.html",
        balance_snapshot=balance_snapshot,
        categories=DEFAULT_CATEGORIES,
        balance_history=balance_history
    )

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


# ==========================================
# AÇÕES E UPLOADS
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
    # ... (Sua lógica de balance_action aqui se mantém igual)
    # Certifique-se de copiar o corpo da função do seu arquivo anterior se necessário
    pass

@app.route("/cards/create", methods=["POST"])
@login_required
def create_card():
    # ... (Sua lógica de create_card aqui se mantém igual)
    pass

@app.route("/cards/<int:card_id>/action", methods=["POST"])
@login_required
def card_action(card_id):
    # ... (Sua lógica de card_action aqui se mantém igual)
    pass

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_user_by_email(email)
        if user:
            flash("Fluxo de recuperação registrado. Contate o suporte.", "success")
        else:
            flash("E-mail não encontrado.", "error")
        return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)