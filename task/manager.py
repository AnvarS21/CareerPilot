import datetime
import sqlite3
from typing import Dict, List


class TaskManager:
    def __init__(self, db):
        self.db = db
        self.connection = db.connection
        self.connection.row_factory = sqlite3.Row

    def create(self, title: str, description: str, execution_time: datetime.datetime, status: str) -> dict:
        """
        Создать задачу в базе данных.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (title, description, date, status)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, execution_time, status),
        )
        self.connection.commit()
        return {
            "id": cursor.lastrowid,
            "title": title,
            "description": description,
            "date": execution_time,
            "status": status,
        }

    def get(self, **kwargs) -> dict or None:
        """
        Получить одну задачу по указанным фильтрам.
        """
        cursor = self.connection.cursor()
        where_clause = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())

        query = f"""
            SELECT *
            FROM tasks
            WHERE {where_clause}
            ORDER BY date
            LIMIT 1
        """

        cursor.execute(query, values)
        result = cursor.fetchone()
        return dict(result) if result else None

    def all(self) -> List[Dict]:
        """
        Получить все задачи.
        """
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY date")
        return [dict(row) for row in cursor.fetchall()]

    def filter(self, **kwargs) -> List[Dict]:
        """
        Получить задачи по указанным фильтрам.
        """
        cursor = self.connection.cursor()

        where_clause = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())

        query = f"""
            SELECT *
            FROM tasks
            WHERE {where_clause}
            ORDER BY date
        """

        cursor.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]

    def update(self, id: int, **kwargs) -> None:
        """
        Обновить задачу по ID.
        """
        cursor = self.connection.cursor()

        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values()) + (id,)

        query = f"""
            UPDATE tasks
            SET {set_clause}
            WHERE id = ?
        """

        cursor.execute(query, values)
        self.connection.commit()

    def delete(self, id: int) -> None:
        """
        Удалить задачу по ID.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id = ?
            """,
            (id,),
        )
        self.connection.commit()

    def get_tasks_for_range(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        Получить задачи в указанном диапазоне дат.
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            """,
            (start_date, end_date),
        )
        return [dict(row) for row in cursor.fetchall()]
