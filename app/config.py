from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    app_name: str = "SVANSAI"
    training_mode: bool = True

    learning_window_start_hour: int = 0
    learning_window_end_hour: int = 23

    daily_topic_goal: int = 10
    topics_per_run: int = 20
    run_interval_seconds: int = 10

    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    alert_email_to: str = os.getenv("ALERT_EMAIL_TO", "")
    alert_email_from: str = os.getenv("ALERT_EMAIL_FROM", "")
    domain_name: str = os.getenv("DOMAIN_NAME", "svansai.com")


settings = Settings()
