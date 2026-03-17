"""
Обработчик выбора даты доставки через календарь.
"""

import logging
import datetime
import calendar
from telegram import Update
from telegram.ext import ContextTypes

from utils import generate_calendar, get_next_month, get_prev_month

logger = logging.getLogger(__name__)

# Этапы диалога
ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)


async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатий на календарь.

    Обрабатывает выбор даты и навигацию между месяцами.
    """
    query = update.callback_query
    await query.answer()

    # Выбор даты доставки
    if query.data.startswith("date_"):
        day = int(query.data.split("_")[1])
        month = context.user_data["calendar_month"]
        year = context.user_data["calendar_year"]

        # Форматируем дату как ДД.ММ.ГГГГ
        context.user_data["data_delivery"] = f"{day:02d}.{month:02d}.{year}"

        await query.message.edit_text(
            f"Вы выбрали дату доставки: {context.user_data['data_delivery']}"
        )
        await query.message.reply_text("Введите количество бутылок воды.")
        return BOTTLES

    # Навигация: следующий месяц
    elif query.data == "next_month":
        year, month = get_next_month(
            context.user_data["calendar_year"],
            context.user_data["calendar_month"]
        )
        context.user_data["calendar_year"] = year
        context.user_data["calendar_month"] = month

    # Навигация: предыдущий месяц
    elif query.data == "prev_month":
        year, month = get_prev_month(
            context.user_data["calendar_year"],
            context.user_data["calendar_month"]
        )
        context.user_data["calendar_year"] = year
        context.user_data["calendar_month"] = month

    # Обновляем календарь
    await query.message.edit_text(
        "Выберите дату доставки:",
        reply_markup=generate_calendar(year, month),
    )
    return DELIVERY_DATE
