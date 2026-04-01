import os
import resend

def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """
    Envia um e-mail HTML via API do Resend.
    Retorna True se enviado com sucesso, ou False se falhar.
    """
    # Proteção: Se o e-mail estiver vazio, aborta a missão imediatamente
    if not to_email:
        print("Erro: E-mail de destino não fornecido.")
        return False

    # Puxa a chave do .env dinamicamente
    resend.api_key = os.environ.get("RESEND_API_KEY")

    # O Resend obriga a usar este e-mail remetente quando estamos testando no plano gratuito
    sender_email = "Equipe MERUEM <onboarding@resend.dev>"

    params = {
        "from": sender_email,
        "to": [to_email],
        "subject": subject,
        "html": body_html,
    }

    try:
        email_response = resend.Emails.send(params)
        print(f"E-mail enviado com sucesso! ID: {email_response.get('id')}")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail via Resend para {to_email}: {e}")
        return False