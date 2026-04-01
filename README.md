# MERUEM

Aplicação web full stack em Flask com autenticação, painel financeiro moderno e persistência em SQLite.

## Recursos
- Login, registro e redefinição simples de senha
- Contas de saldo com adicionar, remover e reservar saldo
- Cartões de crédito com limite, vencimento, imagem e uso/reserva
- Categorias pré-definidas e categoria personalizada
- Estatísticas por categoria em estilo planilha
- Link direto para falar com desenvolvedor no WhatsApp

## Rodando localmente
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python backend/app.py
```

Acesse `http://127.0.0.1:5000`.

## Deploy no Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn backend.app:app`

## Observação
O fluxo de "esqueci minha senha" aqui é um MVP sem token de e-mail. Para produção, o ideal é usar reset por token e envio de e-mail.
