import os
import resend

def send_email(to_email, subject, body_html):
    # Puxa a chave do .env
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
        print(f"E-mail enviado com sucesso! ID: {email_response['id']}")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail via Resend: {e}")
        return False