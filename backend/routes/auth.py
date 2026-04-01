from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, get_user_by_email, get_user_by_id, update_user_password

auth_bp = Blueprint('auth', __name__)

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

    existing_user = get_user_by_email(email)
    if existing_user:
        flash("Já existe uma conta com esse e-mail.", "error")
        return redirect(url_for("home"))

    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    # O POSTGRES USA %s e RETURNING id
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
    
    # Verifica se a senha atual digitada está correta
    if not check_password_hash(user["password_hash"], current_password):
        flash("Senha atual incorreta.", "error")
        return redirect(url_for("settings"))
        
    # Verifica se as senhas novas batem
    if new_password != confirm_password:
        flash("A nova senha e a confirmação não coincidem.", "error")
        return redirect(url_for("settings"))
        
    # Salva a nova senha
    new_hash = generate_password_hash(new_password)
    update_user_password(session["user_id"], new_hash)
    
    flash("Senha alterada com sucesso!", "success")
    return redirect(url_for("settings"))