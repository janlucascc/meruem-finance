# 💠 M.E.R.U.E.M
> Gestão Financeira Descomplicada. Simples, fluida e direta ao ponto.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)

## ✨ Recursos

<details>
<summary><b>💼 Contas e Saldo</b></summary>
<br>
Adicione, gaste e reserve dinheiro com persistência robusta em banco de dados PostgreSQL. Controle total do seu capital livre e comprometido.
</details>

<details>
<summary><b>💳 Cartões Inteligentes e Reserva de Limite</b></summary>
<br>
Controle limites, dias de vencimento e faça upload de imagens customizadas para cada cartão. Sistema exclusivo de reserva: comprometa o limite antes mesmo de gastar na fatura.
</details>

<details>
<summary><b>📊 Relatórios e Categorias</b></summary>
<br>
Estatísticas organizadas por categorias pré-definidas (Moradia, Alimentação, Transporte, Lazer, Emergência) e personalizadas, exibidas em estilo planilha.
</details>

<details>
<summary><b>🔐 Autenticação e Suporte</b></summary>
<br>
Sistema completo de login, registro e redefinição simples de senha com isolamento de dados. Contém link direto para suporte com o desenvolvedor via WhatsApp.
</details>

---

## 🚀 Rodando Localmente

<details>
<summary><b>Ver passos de instalação</b></summary>
<br>

```bash
# 1. Crie e ative o ambiente virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as Variáveis de Ambiente
# Crie um arquivo .env na raiz do projeto (baseado no .env.example)
# e adicione a sua DATABASE_URL do PostgreSQL local.

# 4. Rode a aplicação
python backend/app.py