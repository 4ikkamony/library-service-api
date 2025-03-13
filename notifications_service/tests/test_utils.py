from django.test import TestCase
from unittest.mock import Mock, patch
from notifications_service.utils import task_handler, send_notification
import logging


class TaskHandlerTestCase(TestCase):
    def setUp(self):
        self.mock_self = Mock()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.handler = logging.StreamHandler()
        self.logger.addHandler(self.handler)

    def test_task_handler_success(self):
        self.mock_self.retry = Mock()

        @task_handler(max_retries=3, countdown=60)
        def mock_task(self):
            return "Success"

        result = mock_task(self.mock_self)
        self.assertEqual(result, "Success")

    @patch("notifications_service.utils.logger")
    def test_task_handler_exception(self, mock_logger):
        self.mock_self.retry.side_effect = Exception("Retry failed")

        @task_handler(max_retries=3, countdown=60)
        def mock_task(self):
            raise Exception("Test error")

        with self.assertRaises(Exception) as context:
            mock_task(self.mock_self)
        self.assertEqual(str(context.exception), "Retry failed")
        mock_logger.error.assert_called_once_with(
            "Error in mock_task: Test error"
        )


class SendNotificationTestCase(TestCase):
    @patch(
        "notifications_service.utils.send_telegram_message",
        return_value=True
    )
    def test_send_notification_success(self, mock_send_telegram):
        message = "Test message"
        send_notification(message)
        mock_send_telegram.assert_called_once_with(message)

    @patch(
        "notifications_service.utils.send_telegram_message",
        return_value=False
    )
    def test_send_notification_failure(self, mock_send_telegram):
        with self.assertRaises(Exception) as context:
            send_notification("Test message")
        self.assertEqual(
            str(context.exception),
            "Failed to send Telegram notification"
        )
