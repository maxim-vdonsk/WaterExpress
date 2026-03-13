"""
Обработчики диалогов Telegram-бота.

Этот пакет содержит все обработчики для ConversationHandler.
"""

from .start import start, handle_message
from .address import address_input
from .phone import phone_input
from .calendar import calendar_callback
from .order import bottles_input

__all__ = [
    "start",
    "handle_message",
    "address_input",
    "phone_input",
    "calendar_callback",
    "bottles_input",
]
