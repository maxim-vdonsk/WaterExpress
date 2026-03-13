"""
Вспомогательные утилиты.

Содержит функции для работы с геолокацией и генерации календаря.
"""

import calendar
import datetime
import logging
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


def get_address_from_location(latitude: float, longitude: float) -> str:
    """
    Получает адрес по координатам через Nominatim API.

    Args:
        latitude: Широта координат.
        longitude: Долгота координат.

    Returns:
        Строка с адресом или сообщение об ошибке.
    """
    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?format=json&lat={latitude}&lon={longitude}"
    )
    # Заголовок User-Agent обязателен для Nominatim API
    headers = {"User-Agent": "WaterExpressBot/1.0"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()
        return data.get("display_name", "Адрес не найден")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к Nominatim: {e}")
        return "Ошибка получения адреса"

    except requests.exceptions.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        return "Ошибка обработки адреса"


def generate_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Генерирует inline-клавиатуру с календарём.

    Args:
        year: Год для отображения.
        month: Месяц для отображения.

    Returns:
        InlineKeyboardMarkup с календарём и кнопками навигации.
    """
    now = datetime.datetime.now()

    # Получаем первый день месяца и количество дней
    first_day_week, last_day = calendar.monthrange(year, month)

    # Определяем минимальный день для выбора (завтра или 1 если новый месяц)
    start_day = 1
    if year == now.year and month == now.month:
        start_day = now.day + 1  # Начинаем с завтрашнего дня

    keyboard = []
    week = []

    # Генерируем дни месяца
    for day in range(1, last_day + 1):
        if day < start_day:
            # Дни в прошлом - неактивные
            week.append(InlineKeyboardButton(" ", callback_data="disabled"))
        else:
            # Доступные для выбора дни
            week.append(
                InlineKeyboardButton(str(day), callback_data=f"date_{day}")
            )

        # Каждые 7 дней создаём новую строку
        if len(week) == 7:
            keyboard.append(week)
            week = []

    # Добавляем оставшиеся дни
    if week:
        keyboard.append(week)

    # Кнопки навигации по месяцам
    nav_buttons = []

    # Определяем минимально допустимый месяц (текущий или следующий)
    min_year, min_month = now.year, now.month
    _, last_day_of_min_month = calendar.monthrange(min_year, min_month)
    if now.day == last_day_of_min_month:
        min_month += 1
        if min_month > 12:
            min_month = 1
            min_year += 1

    # Кнопка "Назад" активна только если не достигли минимального месяца
    if year > min_year or (year == min_year and month > min_month):
        nav_buttons.append(
            InlineKeyboardButton("⬅ Предыдущий месяц", callback_data="prev_month")
        )

    # Кнопка "Вперёд" всегда активна
    nav_buttons.append(
        InlineKeyboardButton("➡ Следующий месяц", callback_data="next_month")
    )

    keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard)


def get_next_month(year: int, month: int) -> tuple:
    """
    Возвращает следующий месяц.

    Args:
        year: Текущий год.
        month: Текущий месяц.

    Returns:
        Кортеж (year, month) следующего месяца.
    """
    if month == 12:
        return year + 1, 1
    return year, month + 1


def get_prev_month(year: int, month: int) -> tuple:
    """
    Возвращает предыдущий месяц.

    Args:
        year: Текущий год.
        month: Текущий месяц.

    Returns:
        Кортеж (year, month) предыдущего месяца.
    """
    if month == 1:
        return year - 1, 12
    return year, month - 1


def is_valid_month(year: int, month: int) -> bool:
    """
    Проверяет, не является ли месяц прошлым.

    Args:
        year: Год для проверки.
        month: Месяц для проверки.

    Returns:
        True если месяц допустим, False если это прошлый месяц.
    """
    now = datetime.datetime.now()

    if year < now.year:
        return False
    if year == now.year and month < now.month:
        return False
    if year == now.year and month == now.month:
        # Проверяем, есть ли ещё доступные дни в этом месяце
        _, last_day = calendar.monthrange(year, month)
        return now.day < last_day

    return True


async def show_calendar(update, context):
    """
    Показывает календарь для выбора даты доставки.

    Календарь начинается со следующего дня и позволяет переключаться между месяцами.

    Args:
        update: Объект обновления Telegram.
        context: Контекст бота.
    """
    now = datetime.datetime.now()
    year, month = now.year, now.month

    # Получаем последний день текущего месяца
    _, last_day = calendar.monthrange(year, month)

    # Если сегодня последний день месяца, показываем следующий месяц
    if now.day == last_day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Сохраняем текущий год и месяц в контексте для навигации
    context.user_data["calendar_year"] = year
    context.user_data["calendar_month"] = month

    await update.message.reply_text(
        "Выберите дату доставки:", reply_markup=generate_calendar(year, month)
    )
