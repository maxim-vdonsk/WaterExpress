"""
Обработчик оформления заказа (количество бутылок, сохранение в БД, уведомление менеджера).
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import save_order
from config import MANAGER_ID

logger = logging.getLogger(__name__)

# Этапы диалога
ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)


async def bottles_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик ввода количества бутылок.

    Проверяет, что введено положительное целое число.
    Сохраняет заказ в базу данных и отправляет уведомление менеджеру.
    """
    # Проверяем корректность ввода
    try:
        bottles = int(update.message.text)
        if bottles <= 0:
            await update.message.reply_text(
                "Пожалуйста, введите положительное число бутылок."
            )
            return BOTTLES
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return BOTTLES

    context.user_data["bottles"] = bottles

    # Сохраняем заказ в базу данных
    success = save_order(
        data_delivery=context.user_data["data_delivery"],
        client_name=update.message.from_user.first_name,
        client_address=context.user_data["client_address"],
        number=context.user_data["number"],
    )

    if not success:
        await update.message.reply_text(
            "Произошла ошибка при сохранении заявки. Пожалуйста, попробуйте позже."
        )
        return ConversationHandler.END

    # Подтверждение для клиента
    await update.message.reply_text("Заявка принята! Ожидайте доставки.")

    # Формируем уведомление для менеджера
    manager_text = (
        f"🔔 Новая заявка!\n\n"
        f"📅 Дата доставки: {context.user_data['data_delivery']}\n"
        f"🏠 Адрес: {context.user_data['client_address']}\n"
        f"📞 <a href='tel:{context.user_data['number']}'>{context.user_data['number']}</a>\n"
        f"🧴 Бутылки: {context.user_data['bottles']}\n"
        f"👤 Клиент: {update.message.from_user.first_name}"
    )

    # Отправляем уведомление менеджеру
    try:
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=manager_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Ошибка отправки менеджеру: {e}")

    return ConversationHandler.END
