import resend

from config import settings

if settings.resend_api_key:
    resend.api_key = settings.resend_api_key


def send_alert_email(subject: str, body: str) -> None:
    if not (
        settings.resend_api_key
        and settings.alert_email_to
        and settings.alert_email_from
    ):
        print("[SVANSAI Alerts] Missing Resend email configuration.")
        return

    try:
        resend.Emails.send(
            {
                "from": settings.alert_email_from,
                "to": [settings.alert_email_to],
                "subject": subject,
                "html": f"<p>{body}</p>",
            }
        )
        print("[SVANSAI Alerts] Email sent successfully.")
    except Exception as error:
        print("[SVANSAI Alerts] Email alert failed:", error)
