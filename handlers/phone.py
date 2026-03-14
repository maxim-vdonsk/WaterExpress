"""
Обработчик ввода номера телефона.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from utils import show_calendar

logger = logging.getLogger(__name__)

# Этапы диалога
ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)


async def phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ввода номера телефона.

    Принимает номер через контакт Telegram или текстом.
    Проверяет корректность номера (должен начинаться с + и содержать цифры).
    """
    # Получаем номер из контакта или текста
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text

    # Добавляем "+" если номер начинается без него
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    # Проверяем, что номер содержит только цифры после "+"
    if not phone_number.lstrip("+").isdigit():
        await update.message.reply_text(
            "Пожалуйста, введите корректный номер телефона."
        )
        return PHONE

    context.user_data["number"] = phone_number

    # Показываем календарь для выбора даты
    await show_calendar(update, context)
    return DELIVERY_DATE
