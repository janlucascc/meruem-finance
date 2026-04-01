from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, get_user_by_email, get_user_by_id, update_user_password
from mailer import send_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import re

auth_bp = Blueprint('auth', __name__)

# --- GERADOR DE TOKENS SEGUROS ---
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route("/register", methods=["POST"])
def register():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not full_name or not email or not password or not confirm_password:
        flash("Preencha todos os campos do cadastro.", "error")
        return redirect(url_for("home"))

    if password != confirm_password:
        flash("As senhas não coincidem.", "error")
        return redirect(url_for("home"))

    # VALIDAÇÃO DE SENHA FORTE
    if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[a-zA-Z]", password):
        flash("A senha deve ter no mínimo 8 caracteres, contendo letras e números.", "error")
        return redirect(url_for("home"))

    existing_user = get_user_by_email(email)
    if existing_user:
        flash("Já existe uma conta com esse e-mail.", "error")
        return redirect(url_for("home"))

    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (full_name, email, password_hash)
        VALUES (%s, %s, %s) RETURNING id
    """, (full_name, email, password_hash))
    user_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO balance_accounts (user_id, account_name, current_balance, reserved_balance)
        VALUES (%s, %s, %s, %s)
    """, (user_id, "Conta principal", 0, 0))
    conn.commit()
    conn.close()

    flash("Conta criada com sucesso. Agora faça login.", "success")
    return redirect(url_for("home"))

@auth_bp.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Informe e-mail e senha.", "error")
        return redirect(url_for("home"))

    user = get_user_by_email(email)

    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboard"))

    flash("E-mail ou senha inválidos.", "error")
    return redirect(url_for("home"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "success")
    return redirect(url_for("home"))

@auth_bp.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("home"))
        
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    user = get_user_by_id(session["user_id"])
    
    if not check_password_hash(user["password_hash"], current_password):
        flash("Senha atual incorreta.", "error")
        return redirect(url_for("settings"))
        
    if new_password != confirm_password:
        flash("A nova senha e a confirmação não coincidem.", "error")
        return redirect(url_for("settings"))

    # VALIDAÇÃO DE SENHA FORTE
    if len(new_password) < 8 or not re.search(r"\d", new_password) or not re.search(r"[a-zA-Z]", new_password):
        flash("A nova senha deve ter no mínimo 8 caracteres, contendo letras e números.", "error")
        return redirect(url_for("settings"))
        
    new_hash = generate_password_hash(new_password)
    update_user_password(session["user_id"], new_hash)
    
    flash("Senha alterada com sucesso!", "success")
    return redirect(url_for("settings"))

# ==========================================
# FLUXO DE RECUPERAÇÃO DE SENHA
# ==========================================
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = get_user_by_email(email)
        
        if user:
            s = get_serializer()
            # Gera um token seguro atrelado ao email
            token = s.dumps(email, salt='recover-key')
            # Cria o link absoluto (com http://...)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            html = f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #17224f;">Recuperação de Senha - MERUEM</h2>
                <p>Olá, <strong>{user['full_name'].split()[0]}</strong>!</p>
                <p>Recebemos um pedido para redefinir a sua senha. Se foi você, clique no botão abaixo:</p>
                <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background-color: #86f2ff; color: #05101b; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0;">Redefinir Minha Senha</a>
                <p style="color: #777; font-size: 12px;">Este link expira em 1 hora. Se não pediu a redefinição, apenas ignore este e-mail.</p>
            </div>
            '''
            send_email(email, "Redefinição de Senha - MERUEM", html)
            
        flash("Se o e-mail estiver cadastrado, enviámos um link de recuperação.", "success")
        return redirect(url_for("auth.forgot_password"))
        
    return render_template("forgot_password.html")

@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        # Tenta ler o token. Se passou de 3600 segundos (1 hora), dá erro!
        email = s.loads(token, salt='recover-key', max_age=3600)
    except SignatureExpired:
        flash("O link de recuperação expirou. Por favor, solicite um novo.", "error")
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash("Link de recuperação inválido ou corrompido.", "error")
        return redirect(url_for('auth.forgot_password'))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('auth.reset_password', token=token))

        if len(new_password) < 8 or not re.search(r"\d", new_password) or not re.search(r"[a-zA-Z]", new_password):
            flash("A senha deve ter no mínimo 8 caracteres, contendo letras e números.", "error")
            return redirect(url_for('auth.reset_password', token=token))

        user = get_user_by_email(email)
        if user:
            new_hash = generate_password_hash(new_password)
            update_user_password(user["id"], new_hash)
            flash("Senha redefinida com sucesso! Pode fazer login.", "success")
            return redirect(url_for('home'))

    return render_template("reset_password.html", token=token)