import datetime
import json
import re

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from core.settings import BOT_TOKEN
from task.keyboard import start_keyboard, tasks_list_datetime, tasks_keyboard, task_keyboard

scheduler = AsyncIOScheduler()


TASK_NAME, TASK_DESCRIPTION, EXECUTION_TIME, HOURS_AND_MINUTES = range(4)
TASK_DATE = 0


def notification(task, chat_id, token):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Готово!", "callback_data": f"done_{task.get('id')}"},
            ]
        ]
    }
    data = {
        "chat_id": chat_id,
        "text": f"Напоминание!\n Пора выполнить задачу:\n\n{task['title']}\nОписание: {task['description']}",
        "reply_markup": json.dumps(keyboard)

    }
    response = requests.post(url, data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = await start_keyboard()
    await update.message.reply_text("Выбирай, что ты будешь делать?", reply_markup=keyboard)
    return ConversationHandler.END


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text="Напиши короткое название задачки\n"
                                       "Если нажал случайно, нажми /cancel")

    return TASK_NAME


async def task_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text
    context.user_data['task_title'] = title
    await update.message.reply_text(text="Отлично! Теперь немножко поподробнее о задачке\n"
                                         "Если нет описания, то просто скипки /skip")
    return TASK_DESCRIPTION


async def choice_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    calendar, step = DetailedTelegramCalendar().build()

    await update.message.reply_text(
        text=f"Хорошо, тогда выбери срок выполнения задачи ({LSTEP[step]}):",
        reply_markup=calendar
    )
    return EXECUTION_TIME


async def task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    description = update.message.text
    context.user_data['description'] = description

    calendar, step = DetailedTelegramCalendar().build()

    await update.message.reply_text(
        text=f"Отлично! Теперь выбери срок выполнения задачи ({LSTEP[step]}):",
        reply_markup=calendar
    )

    return EXECUTION_TIME


async def execution_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    result, key, step = DetailedTelegramCalendar().process(query.data)

    if not result and key:
        await query.edit_message_text(
            text=f"Выбери {LSTEP[step]}:",
            reply_markup=key
        )
        return EXECUTION_TIME

    if result:
        context.user_data['execution_time'] = result
        await query.edit_message_text(
            text=f"А теперь напишите время в формате ---> <b>часы:минуты</b>\n"
                 f"Можете скипнуть ----->  /skip_time",
            parse_mode='HTML'
        )

        return HOURS_AND_MINUTES


async def hours_and_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text

    time_pattern = r"^([0-9]{1,2}):([0-9]{2})$"
    match = re.match(time_pattern, user_input)

    if not match:
        await update.message.reply_text(
            "Неверный формат. Пожалуйста, введите время в формате: часы:минуты."
        )
        return HOURS_AND_MINUTES

    hours = int(match.group(1))
    minutes = int(match.group(2))

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await update.message.reply_text(
            "Некорректное время. Часы должны быть от 0 до 23, а минуты от 0 до 59."
        )
        return HOURS_AND_MINUTES

    current_date = context.user_data.get('execution_time', None)
    execution_datetime = datetime.datetime.combine(current_date, datetime.time(hours, minutes))
    context.user_data['execution_time'] = execution_datetime

    task = context.bot_data.get('task')
    user_data = context.user_data

    task = task.create(
        user_data.get('task_title'),
        user_data.get('description', 'Описания - нет!'),
        execution_datetime,
        'В процессе',
    )

    if user_data.get('execution_time') > datetime.datetime.now():
        scheduler.add_job(
            func=notification,
            trigger=DateTrigger(user_data.get('execution_time')),
            args=[task, update.message.chat_id, context.bot_data.get('token')]
        )
        scheduler.id = task.get('id')
    await update.message.reply_text('Задачка успешно сохранена')
    user_data.clear()
    return ConversationHandler.END


async def skip_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    task = context.bot_data.get('task')

    task = task.create(
        user_data.get('task_title'),
        user_data.get('description', 'Описания - нет!'),
        user_data.get('execution_time'),
        'В процессе',
    )
    if user_data.get('execution_time') >= datetime.date.today():
        scheduler.add_job(
            func=notification,
            trigger=DateTrigger(user_data.get('execution_time')),
            args=[task, update.message.chat_id, context.bot_data.get('token')]
        )
        scheduler.id = task.get('id')
    await update.message.reply_text('Задачка успешно сохранена')
    user_data.clear()
    return ConversationHandler.END


async def tasks_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    tasks = task.all()

    if update.message is None:
        if not tasks:
            await update.callback_query.edit_message_text('У вас пока нет задач.')
            return
        await update.callback_query.edit_message_text(
        'За какой срок вам предоставить список задач?',
        reply_markup=tasks_list_datetime()
    )
    else:
        if not tasks:
            await update.message.reply_text('У вас пока нет задач.')
            return
        await update.message.reply_text(
            'За какой срок вам предоставить список задач?',
            reply_markup=tasks_list_datetime()
        )


async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.today().date()
    tomorrow = today + datetime.timedelta(days=1)

    task = context.bot_data.get('task')
    tasks = task.get_tasks_for_range(today, tomorrow)
    await update.callback_query.edit_message_text(
        "Задачки на сегодня",
        reply_markup=tasks_keyboard(tasks, 'tasks_list'),
    )


async def task_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    id = update.callback_query.data.split('_')[-1]
    task_instance = task.get(id=id)
    mark = ' ✅' if task_instance.get('status') == 'Выполнен' else ' ❌'
    text = (
        f"*Название:* {task_instance.get('title')}\n\n"
        f"*Описание:* {task_instance.get('description')}\n\n"
        f"*Дата выполнения:* {task_instance.get('date')} {mark}\n\n"
        f"*Статус:* {task_instance.get('status')}\n\n"
    )

    await update.callback_query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=task_keyboard(task_instance, 'tasks_list')
    )


async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    id = update.callback_query.data.split('_')[-1]
    task.update(id=id, status="Выполнен")
    task_instance = task.get(id=id)
    mark = ' ✅' if task_instance.get('status') == 'Выполнен' else ' ❌'
    text = (
        f"*Название:* {task_instance.get('title')}\n\n"
        f"*Описание:* {task_instance.get('description')}\n\n"
        f"*Дата выполнения:* {task_instance.get('date')} {mark}\n\n"
        f"*Статус:* {task_instance.get('status')}\n\n"
    )
    try:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=task_keyboard(task_instance, 'tasks_list')
        )
    except BadRequest:
        await update.callback_query.answer('')


async def task_not_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    id = update.callback_query.data.split('_')[-1]
    task.update(id=id, status="Не Выполнен")
    task_instance = task.get(id=id)
    mark = ' ✅' if task_instance.get('status') == 'Выполнен' else ' ❌'
    text = (
        f"*Название:* {task_instance.get('title')}\n\n"
        f"*Описание:* {task_instance.get('description')}\n\n"
        f"*Дата выполнения:* {task_instance.get('date')} {mark}\n\n"
        f"*Статус:* {task_instance.get('status')}\n\n"
    )
    try:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=task_keyboard(task_instance, 'tasks_list')
        )
    except BadRequest:
        await update.callback_query.answer('')


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    id = update.callback_query.data.split('_')[-1]
    task.delete(id=id)
    await update.callback_query.message.reply_text("Задача удалена")
    await tasks_list(update, context)


async def week_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = datetime.datetime.now().date()

    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)

    task = context.bot_data.get('task')
    tasks = task.get_tasks_for_range(start_of_week, end_of_week)
    await update.callback_query.edit_message_text(
        "Задачки за эту неделю",
        reply_markup=tasks_keyboard(tasks, 'tasks_list'),
    )


async def all_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    tasks = task.all()
    await update.callback_query.edit_message_text(
        "Задачки за эту неделю",
        reply_markup=tasks_keyboard(tasks, 'tasks_list'),
    )


async def month_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.bot_data.get('task')
    today = datetime.datetime.now().date()

    start_of_month = today.replace(day=1)

    next_month = start_of_month.replace(month=start_of_month.month % 12 + 1, day=1)
    end_of_month = next_month - datetime.timedelta(days=1)

    tasks = task.get_tasks_for_range(start_of_month, end_of_month)

    await update.callback_query.edit_message_text(
        "Задачки за этот месяц",
        reply_markup=tasks_keyboard(tasks, 'tasks_list'),
    )


async def specific_date_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.message.reply_text(
        "Напишите дату в формате день:месяц:год"
    )
    return TASK_DATE


async def task_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()

    try:
        specific_date = datetime.datetime.strptime(user_input, "%d:%m:%Y").date()

        task = context.bot_data.get('task')
        tasks = task.get(date=specific_date)
        if tasks:
            await update.message.reply_text(
                f"Задачки за {specific_date}:",
                reply_markup=tasks_keyboard(tasks, 'tasks_list'),
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                f"Задачек на эту дату не наблюдается",
            )

    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты! Пожалуйста, введите дату в формате день:месяц:год (например, 19:11:2024)."
        )
        return TASK_DATE