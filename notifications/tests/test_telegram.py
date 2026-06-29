from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from notifications.telegram import send_telegram_message


@override_settings(TELEGRAM_BOT_TOKEN="test-token", TELEGRAM_CHAT_ID="-100123")
class SendTelegramMessageTests(TestCase):
    @patch("notifications.telegram.requests.post")
    def test_sends_message_with_correct_payload(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        send_telegram_message("Hello chat")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("test-token", args[0])
        self.assertEqual(kwargs["data"]["chat_id"], "-100123")
        self.assertEqual(kwargs["data"]["text"], "Hello chat")

    @patch("notifications.telegram.requests.post")
    def test_does_not_raise_on_network_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.ConnectionError("boom")

        # Не повинно піднімати виняток назовні.
        send_telegram_message("Hello chat")

    @patch("notifications.telegram.requests.post")
    def test_does_not_raise_on_http_error_status(self, mock_post):
        response = MagicMock(status_code=401)
        response.raise_for_status.side_effect = __import__(
            "requests"
        ).exceptions.HTTPError("401")
        mock_post.return_value = response

        send_telegram_message("Hello chat")  # без винятку


@override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
class SendTelegramMessageNotConfiguredTests(TestCase):
    @patch("notifications.telegram.requests.post")
    def test_skips_request_when_not_configured(self, mock_post):
        send_telegram_message("Hello chat")
        mock_post.assert_not_called()
