import sqlite3

from core.settings import DATABASE


class SqliteDB:
    """Обеспечивает подключение к базе данных Sqlite3"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = sqlite3.connect(DATABASE)
        return cls._instance

    def __init__(self):
        self._create_tables()

    def __repr__(self):
        return f"<SqliteDB(connection={self.connection})>"

    def _create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный идентификатор
                title TEXT NOT NULL,                  -- Название задачи (обязательно)
                description TEXT,                     -- Описание задачи (необязательно)
                date DATETIME,                        -- Дата выполнения задачи (в формате ISO)
                status TEXT DEFAULT 'Not Started'     -- Статус задачи (по умолчанию "Not Started")
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный идентификатор
                title TEXT NOT NULL,                  -- Название задачи (обязательно)
                company TEXT,                         -- Название компании
                link TEXT,                            -- Ссылка на вакансию
                salary TEXT,                          -- Зарплата
                job_type TEXT,                        -- Тип работы  
                status TEXT                           -- Статус  
            )
            """
        )
        self.connection.commit()

    def close(self):
        """Закрывает соединение с базой данных."""
        self.connection.close()

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()
