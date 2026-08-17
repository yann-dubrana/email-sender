import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path

from modules.settings import settings


def connect() -> smtplib.SMTP:
    if settings.smtp.ssl:
        return smtplib.SMTP_SSL(
            settings.smtp.server, settings.smtp.port, timeout=settings.smtp.timeout
        )
    return smtplib.SMTP(
        settings.smtp.server, settings.smtp.port, timeout=settings.smtp.timeout
    )


def build_message(path: Path, to: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp.sender
    message["To"] = to
    message["Subject"] = f"New file: {path.name}"
    message.set_content(f"Attached: {path.name}")

    guessed, _ = mimetypes.guess_type(path.name)
    maintype, _, subtype = (guessed or "application/octet-stream").partition("/")
    message.add_attachment(
        path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=path.name,
    )
    return message


def send_file(path: Path, to: str) -> None:
    message = build_message(path, to)

    with connect() as smtp:
        smtp.ehlo()
        if not settings.smtp.ssl:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings.smtp.username, settings.smtp.password)
        smtp.send_message(message)
