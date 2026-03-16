"""
Обработчик ввода адреса и геолокации.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from utils import get_address_from_location

logger = logging.getLogger(__name__)

# Этапы диалога
ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)


async def address_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ввода адреса.

    Принимает текст адреса или геолокацию (преобразует в адрес через API).
    """
    if update.message.location:
        # Пользователь отправил геолокацию
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        context.user_data["client_address"] = get_address_from_location(
            latitude, longitude
        )
    else:
        # Пользователь ввёл адрес текстом
        context.user_data["client_address"] = update.message.text

    keyboard = [
        [KeyboardButton("📞 Отправить номер телефона", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(
        f"Ваш адрес: {context.user_data['client_address']}\n"
        f"Введите номер телефона или нажмите кнопку ниже.",
        reply_markup=reply_markup,
    )
    return PHONE
