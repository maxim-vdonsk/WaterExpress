import logging
import sqlite3
import calendar
import datetime
import requests
from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, Update, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from config import TELEGRAM_TOKEN, MANAGER_ID  

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы диалога
(ADDRESS, PHONE, DELIVERY_DATE, BOTTLES) = range(4)

def create_database():
    conn = sqlite3.connect('baza.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_delivery TEXT,
            client_name TEXT,
            client_address TEXT,
            number TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_database()

def get_address_from_location(latitude, longitude):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
    headers = {"User-Agent": "MyTelegramBot/1.0 (contact: example@email.com)"}  

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сбрасываем все данные пользователя
    context.user_data.clear()

    keyboard = [[KeyboardButton("🚰 Создать заявку на доставку воды")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Нажмите кнопку ниже, чтобы создать заявку.", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🚰 Создать заявку на доставку воды":
        # Сбрасываем все данные пользователя
        context.user_data.clear()

        keyboard = [[KeyboardButton("📍 Поделиться геолокацией", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Введите адрес доставки или поделитесь геолокацией.", reply_markup=reply_markup)
        return ADDRESS

async def address_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        context.user_data["client_address"] = get_address_from_location(latitude, longitude)
    else:
        context.user_data["client_address"] = update.message.text

    keyboard = [[KeyboardButton("📞 Отправить номер телефона", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(f"Ваш адрес: {context.user_data['client_address']}\nВведите номер телефона или нажмите кнопку ниже.", reply_markup=reply_markup)
    return PHONE

async def phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.contact.phone_number if update.message.contact else update.message.text

    # Проверяем, начинается ли номер с "+"
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    # Проверяем, что номер телефона содержит только цифры и знак "+"
    if not phone_number.lstrip('+').isdigit():
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона.")
        return PHONE

    context.user_data["number"] = phone_number
    await show_calendar(update, context)
    return DELIVERY_DATE

async def show_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    year, month = now.year, now.month

    # Получаем последний день текущего месяца
    _, last_day = calendar.monthrange(year, month)

    # Если сегодня последний день месяца, переключаемся на следующий месяц
    if now.day == last_day:
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Сохраняем год и месяц в контексте
    context.user_data["calendar_year"] = year
    context.user_data["calendar_month"] = month

    # Показываем календарь
    await update.message.reply_text("Выберите дату доставки:", reply_markup=generate_calendar(year, month))

def generate_calendar(year, month):
    now = datetime.datetime.now()
    keyboard, week = [], []

    # Получаем первый день месяца и количество дней в месяце
    first_day, last_day = calendar.monthrange(year, month)

    # Определяем, с какого дня начинать отображение
    start_day = 1
    if year == now.year and month == now.month:
        start_day = now.day + 1  # Начинаем с завтрашнего дня

    # Генерация календаря
    for day in range(1, last_day + 1):
        if day < start_day:
            week.append(InlineKeyboardButton(" ", callback_data="disabled"))
        else:
            week.append(InlineKeyboardButton(str(day), callback_data=f"date_{day}"))

        if len(week) == 7:
            keyboard.append(week)
            week = []

    if week:
        keyboard.append(week)

    # Кнопки навигации
    nav_buttons = []

    # Определяем минимально допустимый месяц
    min_year, min_month = now.year, now.month
    _, last_day_of_min_month = calendar.monthrange(min_year, min_month)
    if now.day == last_day_of_min_month:
        min_month += 1
        if min_month > 12:
            min_month = 1
            min_year += 1

    # Показываем кнопку "⬅ Предыдущий месяц" только если текущий месяц не минимально допустимый
    if year > min_year or (year == min_year and month > min_month):
        nav_buttons.append(InlineKeyboardButton("⬅ Предыдущий месяц", callback_data="prev_month"))

    # Всегда показываем кнопку "➡ Следующий месяц"
    nav_buttons.append(InlineKeyboardButton("➡ Следующий месяц", callback_data="next_month"))

    keyboard.append(nav_buttons)
    return InlineKeyboardMarkup(keyboard)

async def calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("date_"):
        day = int(query.data.split("_")[1])
        month, year = context.user_data["calendar_month"], context.user_data["calendar_year"]
        context.user_data["data_delivery"] = f"{day:02d}.{month:02d}.{year}"

        await query.message.edit_text(f"Вы выбрали дату доставки: {context.user_data['data_delivery']}")
        await query.message.reply_text("Введите количество бутылок воды.")
        return BOTTLES

    elif query.data == "next_month":
        month, year = context.user_data["calendar_month"] + 1, context.user_data["calendar_year"]
        if month > 12:
            month, year = 1, year + 1
        context.user_data["calendar_month"], context.user_data["calendar_year"] = month, year

    elif query.data == "prev_month":
        month, year = context.user_data["calendar_month"] - 1, context.user_data["calendar_year"]
        if month < 1:
            month, year = 12, year - 1
        context.user_data["calendar_month"], context.user_data["calendar_year"] = month, year

    await query.message.edit_text("Выберите дату доставки:", reply_markup=generate_calendar(year, month))
    return DELIVERY_DATE

async def bottles_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bottles = int(update.message.text)
        if bottles <= 0:
            await update.message.reply_text("Пожалуйста, введите положительное число бутылок.")
            return BOTTLES
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return BOTTLES

    context.user_data["bottles"] = bottles

    # Сохранение в базу данных
    conn = None
    try:
        conn = sqlite3.connect('baza.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clients (data_delivery, client_name, client_address, number)
            VALUES (?, ?, ?, ?)
        ''', (context.user_data["data_delivery"], update.message.from_user.first_name, 
              context.user_data["client_address"], context.user_data["number"]))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении заявки. Пожалуйста, попробуйте позже.")
        return ConversationHandler.END
    finally:
        if conn:
            conn.close()

    await update.message.reply_text("Заявка принята! Ожидайте доставки.")

    # Отправка заявки менеджеру
    manager_text = (
        f"Новая заявка!\n\n"
        f"📅 Дата доставки: {context.user_data['data_delivery']}\n"
        f"🏠 Адрес: {context.user_data['client_address']}\n"
        f"📞 <a href='tel:{context.user_data['number']}'>{context.user_data['number']}</a>\n"
        f"🧴 Бутылки: {context.user_data['bottles']}\n"
        f"👤 Клиент: {update.message.from_user.first_name}"
    )

    try:
        await context.bot.send_message(
            chat_id=MANAGER_ID, 
            text=manager_text, 
            parse_mode="HTML", 
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Ошибка отправки менеджеру: {e}")

    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT | filters.LOCATION, address_input)],
            PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, phone_input)],
            DELIVERY_DATE: [CallbackQueryHandler(calendar_callback)],
            BOTTLES: [MessageHandler(filters.TEXT, bottles_input)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()