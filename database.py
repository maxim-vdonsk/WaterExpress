"""
Модуль для работы с базой данных SQLite.

Содержит функции для создания таблицы и сохранения заказов.
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DATABASE_NAME = "baza.db"


def create_database():
    """
    Создаёт таблицу клиентов в базе данных SQLite.

    Таблица содержит:
    - id: уникальный идентификатор записи
    - data_delivery: дата доставки
    - client_name: имя клиента
    - client_address: адрес доставки
    - number: номер телефона
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_delivery TEXT,
                client_name TEXT,
                client_address TEXT,
                number TEXT
            )
        """
        )

        conn.commit()
        logger.info("База данных успешно создана/проверена")

    except sqlite3.Error as e:
        logger.error(f"Ошибка при создании базы данных: {e}")

    finally:
        if conn:
            conn.close()


def save_order(
    data_delivery: str,
    client_name: str,
    client_address: str,
    number: str
) -> bool:
    """
    Сохраняет заказ в базу данных.

    Args:
        data_delivery: Дата доставки (формат ДД.ММ.ГГГГ).
        client_name: Имя клиента.
        client_address: Адрес доставки.
        number: Номер телефона.

    Returns:
        True если заказ успешно сохранён, False в случае ошибки.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO clients (data_delivery, client_name, client_address, number)
            VALUES (?, ?, ?, ?)
        """,
            (data_delivery, client_name, client_address, number),
        )

        conn.commit()
        logger.info(f"Заказ сохранён для клиента: {client_name}")
        return True

    except sqlite3.Error as e:
        logger.error(f"Ошибка при сохранении заказа: {e}")
        return False

    finally:
        if conn:
            conn.close()


def get_all_orders() -> list:
    """
    Получает все заказы из базы данных.

    Returns:
        Список кортежей с данными заказов.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clients ORDER BY id DESC")
        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return []

    finally:
        if conn:
            conn.close()
