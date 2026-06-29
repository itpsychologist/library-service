mport logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_TIMEOUT = 5  # секунд; не блокувати HTTP-запит користувача надовго


def send_telegram_message(text: str) -> None:

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram notification skipped: TELEGRAM_BOT_TOKEN or "
            "TELEGRAM_CHAT_ID is not configured."
        )
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text},
            timeout=TELEGRAM_API_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to send Telegram notification.")