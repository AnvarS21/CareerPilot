import sqlite3
from typing import List, Dict, Tuple, Any
import logging

class JobManager:
    def __init__(self, db: sqlite3):
        """
        Менеджер для работы с таблицей jobs.
        :param db: База данных (Sqlite).
        """
        self.db = db
        self.connection = db.connection
        self.connection.row_factory = sqlite3.Row

    def create(self, company: str, title: str, link: str, salary: str, job_type: str, status: str) -> None:
        """Создает задачу"""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (company, title, link, salary, job_type, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (company, title, link, salary, job_type, status),
        )
        self.connection.commit()

    def bulk_create(self, jobs: List[Dict[str, str]]):
        """
        Добавляет вакансии в базу данных. Если вакансия уже существует, она пропускается.

        :param jobs: Список вакансий в виде словарей, где ключи — названия столбцов.
        """
        cursor = self.connection.cursor()
        try:
            sql = """
            INSERT INTO jobs (company, title, link, salary, job_type, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (company, title) DO NOTHING
            """
            job_values = [
                (job["company"], job["title"], job["link"], job["salary"], job["job_type"], job["status"])
                for job in jobs
            ]

            cursor.executemany(sql, job_values)
            self.connection.commit()
            logging.info(f"{cursor.rowcount} новых вакансий добавлено.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении вакансий: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def get_or_create(self, **kwargs) -> Tuple[Any, bool]:
        """
        Попытаться найти объект. Если не найдено, создать новый и вернуть его.
        :param kwargs: критерии поиска/создания
        :return: (объект, создан ли объект: True/False)
        """
        object_ = self.get(**kwargs)
        if object_:
            return object_, False

        cursor = self.connection.cursor()

        try:
            kwargs.update(status='Новая')
            columns = ", ".join(kwargs.keys())
            placeholders = ", ".join(["?"] * len(kwargs))
            values = tuple(kwargs.values())

            sql_insert = f"INSERT INTO jobs ({columns}) VALUES ({placeholders})"
            cursor.execute(sql_insert, values)
            self.connection.commit()

            row_id = cursor.lastrowid
            sql_select = "SELECT * FROM jobs WHERE id = ?"
            cursor.execute(sql_select, (row_id,))
            row = cursor.fetchone()

            obj = dict(zip([desc[0] for desc in cursor.description], row), id=row_id)
            return obj, True
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Ошибка в get_or_create: {e}")
            raise
        finally:
            cursor.close()

    def get(self, **kwargs) -> dict or None:
        """Получить одну задачу по указанным фильтрам."""
        cursor = self.connection.cursor()

        where_clause = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())

        query = f"""
            SELECT *
            FROM jobs
            WHERE {where_clause}
            LIMIT 1
        """

        cursor.execute(query, values)
        result = cursor.fetchone()
        if result:
            column_names = [desc[0] for desc in cursor.description]
            return dict(zip(column_names, result))
        return None

    def all(self) -> List[Dict]:
        """
        Получить все записи.
        :return: Список всех задач.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM jobs")
        return [dict(row) for row in cursor.fetchall()]

    def filter(self, **kwargs) -> List[Dict]:
        """
        Получить записи по фильтру.
        :param kwargs: Фильтры (например, func="my_function").
        :return: Список задач, соответствующих фильтрам.
        """
        cursor = self.connection.cursor()
        where_clause = " AND ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        query = f"SELECT * FROM jobs WHERE {where_clause}"
        cursor.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]

    def update(self, job_id: str, **kwargs):
        """
        Обновить запись по job_id.
        :param job_id: ID задачи.
        :param kwargs: Поля для обновления (например, next_run_time=datetime.now()).
        """
        cursor = self.connection.cursor()
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values()) + (job_id,)
        query = f"UPDATE jobs SET {set_clause} WHERE job_id = ?"
        cursor.execute(query, values)
        self.connection.commit()

    def delete(self, job_id: str) -> bool:
        """
        Удалить запись по job_id.
        :param job_id: ID задачи.
        :return: True, если запись была удалена, иначе False.
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def clear(self):
        """
        Удалить все записи.
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM jobs")
        self.connection.commit()
