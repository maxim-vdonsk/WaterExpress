"""
Обработчик команды /start и начального сообщения.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Этапы диалога (импортируются из bot.py для консистентности)
ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.

    Сбрасывает данные пользователя и показывает приветственное сообщение
    с кнопкой для создания заявки.
    """
    # Очищаем данные пользователя перед новым диалогом
    context.user_data.clear()

    keyboard = [[KeyboardButton("🚰 Создать заявку на доставку воды")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Добро пожаловать! Нажмите кнопку ниже, чтобы создать заявку.",
        reply_markup=reply_markup,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений.

    Начинает диалог создания заявки, если пользователь нажал соответствующую кнопку.
    """
    if update.message.text == "🚰 Создать заявку на доставку воды":
        # Очищаем данные пользователя перед новым заказом
        context.user_data.clear()

        keyboard = [
            [KeyboardButton("📍 Поделиться геолокацией", request_location=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )

        await update.message.reply_text(
            "Введите адрес доставки или поделитесь геолокацией.",
            reply_markup=reply_markup,
        )
        return ADDRESS

    # Если текст не совпадает с ожидаемым, завершаем диалог
    return ConversationHandler.END
