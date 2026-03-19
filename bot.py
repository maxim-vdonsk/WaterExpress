"""
WaterExpress — Telegram-бот для доставки воды.

Этот бот позволяет клиентам создавать заявки на доставку воды через Telegram.
Поддерживает отправку геолокации, выбор даты доставки через календарь
и уведомляет менеджера о новых заказах.

Модульная структура:
    - bot.py: Точка входа, настройка приложения
    - config.py: Конфигурация (токен, ID менеджера)
    - database.py: Работа с базой данных SQLite
    - utils.py: Вспомогательные функции (геолокация, календарь)
    - handlers/: Обработчики диалогов
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from config import TELEGRAM_TOKEN
from database import create_database
from handlers import (
    start,
    handle_message,
    address_input,
    phone_input,
    calendar_callback,
    bottles_input,
)

# =============================================================================
# Настройка логирования
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# Этапы диалога (ConversationHandler states)
# =============================================================================

ADDRESS, PHONE, DELIVERY_DATE, BOTTLES = range(4)

# =============================================================================
# Запуск бота
# =============================================================================


def main():
    """
    Инициализирует и запускает Telegram-бота.

    Настраивает ConversationHandler для управления диалогом создания заявки.
    """
    # Создаём базу данных при запуске
    create_database()
    logger.info("База данных проверена/создана")

    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчик конверсации (диалога создания заявки)
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        ],
        states={
            ADDRESS: [
                MessageHandler(filters.TEXT | filters.LOCATION, address_input)
            ],
            PHONE: [
                MessageHandler(filters.TEXT | filters.CONTACT, phone_input)
            ],
            DELIVERY_DATE: [CallbackQueryHandler(calendar_callback)],
            BOTTLES: [
                MessageHandler(filters.TEXT, bottles_input)
            ],
        },
        fallbacks=[],
    )

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    # Запускаем бота
    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
