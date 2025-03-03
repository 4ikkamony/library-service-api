from django.test import TestCase
from unittest.mock import patch, Mock
from notifications_service.utils import send_telegram_message
from django.conf import settings
import requests


class TelegramNotificationTestCase(TestCase):
    def setUp(self):
        self.message = "Test message from TestCase"

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        result = send_telegram_message(self.message)

        mock_post.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": self.message,
                "parse_mode": "Markdown",
            },
        )
        self.assertTrue(result)

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_failure_403(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"ok":false,"error_code":403,"description":"Forbidden: bot can\'t initiate conversation with a user"}'
        mock_post.return_value = mock_response

        result = send_telegram_message(self.message)

        mock_post.assert_called_once()
        self.assertFalse(result)

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_failure_400(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = (
            '{"ok":false,"error_code":400,"description":"Bad Request: chat not found"}'
        )
        mock_post.return_value = mock_response

        result = send_telegram_message(self.message)

        mock_post.assert_called_once()
        self.assertFalse(result)

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_network_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Network is unreachable"
        )

        result = send_telegram_message(self.message)

        self.assertFalse(result)

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_long_message(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        # near message length Telegram limit 4096
        long_message = "A" * 4000
        result = send_telegram_message(long_message)

        mock_post.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": long_message,
                "parse_mode": "Markdown",
            },
        )
        self.assertTrue(result)

    @patch("notifications_service.utils.requests.post")
    def test_send_telegram_message_special_characters(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_post.return_value = mock_response

        special_message = "Test **bold** & <script> *italic* > text"
        result = send_telegram_message(special_message)

        mock_post.assert_called_once_with(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": special_message,
                "parse_mode": "Markdown",
            },
        )
        self.assertTrue(result)
