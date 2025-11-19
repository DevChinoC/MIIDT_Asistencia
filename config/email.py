# config/emailer.py
import os, smtplib, mimetypes, socket
from email.message import EmailMessage
from dotenv import load_dotenv

# Carga el .env desde config/.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER

def _smtp_client():
    """Devuelve un cliente SMTP según el puerto (465=SSL, otros=STARTTLS)."""
    timeout = 20
    if SMTP_PORT == 465:
        return smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=timeout)
    return smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=timeout)

def send_mail(
    subject: str,
    body: str,
    to_list: list[str],
    attachments: list[str] | None = None,
    cc_list: list[str] | None = None
):
    """
    Envía un correo electrónico con soporte de adjuntos y CC.
    - subject: asunto
    - body: cuerpo del correo
    - to_list: lista de destinatarios principales
    - cc_list: lista de copias (CC)
    - attachments: rutas de archivos a adjuntar
    """
    # ----------------- VALIDACIONES -----------------
    missing = [
        k for k, v in {
            "SMTP_HOST": SMTP_HOST,
            "SMTP_PORT": SMTP_PORT,
            "SMTP_USER": SMTP_USER,
            "SMTP_PASS": "***" if SMTP_PASS else None,
            "SMTP_FROM": SMTP_FROM
        }.items() if not v
    ]
    if missing:
        raise RuntimeError(f"SMTP: faltan variables en .env -> {', '.join(missing)}")

    if not to_list:
        raise RuntimeError("SMTP: lista de destinatarios vacía")

    # ----------------- CONSTRUCCIÓN DEL MENSAJE -----------------
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join([t for t in to_list if t])

    if cc_list:
        msg["Cc"] = ", ".join([c for c in cc_list if c])

    msg.set_content(body or "")

    for path in attachments or []:
        try:
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(path, "rb") as f:
                data = f.read()
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(path))
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo adjuntar {path}: {e}")

    # Combina destinatarios principales y CC
    recipients = []
    recipients.extend([t for t in to_list or [] if t])
    recipients.extend([c for c in cc_list or [] if c])

    # ----------------- ENVÍO -----------------
    try:
        with _smtp_client() as s:
            # STARTTLS si NO es 465 (SSL)
            if SMTP_PORT != 465:
                s.ehlo()
                s.starttls()
                s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg, to_addrs=recipients)

    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            "SMTP: autenticación fallida.\n"
            "💡 Usa una 'App Password' de Gmail (no tu contraseña normal)."
        ) from e

    except smtplib.SMTPConnectError:
        raise RuntimeError("SMTP: no se pudo conectar al servidor. Verifica HOST/PUERTO.")
    except smtplib.SMTPRecipientsRefused:
        raise RuntimeError("SMTP: dirección de correo inválida o rechazada por el servidor.")
    except (smtplib.SMTPException, OSError, socket.error) as e:
        raise RuntimeError(f"SMTP: error de conexión o envío -> {e}") from e