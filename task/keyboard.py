from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup)


async def start_keyboard():
    reply_keyboard = [['Добавить задачу'], ['Посмотреть список задач'], ['Поиск вакансий'], ['Список вакансий']]
    return ReplyKeyboardMarkup(
        reply_keyboard, resize_keyboard=True,
        input_field_placeholder='Выберите что вам нужно сделать'
    )

def tasks_list_datetime():
    keyboard = [
        [InlineKeyboardButton('Сегодня', callback_data='today')],
        [InlineKeyboardButton('Эту неделю', callback_data='week')],
        [InlineKeyboardButton('Этот месяц', callback_data='month')],
        [InlineKeyboardButton('Все время', callback_data='all_time')],
        [InlineKeyboardButton('Написать дату', callback_data='specific_date')],
    ]
    return InlineKeyboardMarkup(keyboard)

def tasks_keyboard(tasks, back):
    keyboard = []
    for task in tasks:
        mark = ' ✅' if task.get('status') == 'Выполнен' else ' ❌'
        text = f"{task.get('title')} - {task.get('date')} {mark}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f'task_{task.get("id")}')])
    keyboard.append([InlineKeyboardButton('Назад 🔙', callback_data=back)])
    return InlineKeyboardMarkup(keyboard)


def task_keyboard(task, back):
    mark = task.get('status', None) == 'Выполнен'
    id = task.get('id', None)
    keyboard = [
        [InlineKeyboardButton(f"Выполнил {'✅' if mark else ''}", callback_data=f'done_{id}')],
        [InlineKeyboardButton(f"Не выполнил {'❌' if not mark else ''}", callback_data=f'not_completed_{id}')],
        [InlineKeyboardButton('Удалить', callback_data=f'delete_{id}')],
        [InlineKeyboardButton('Назад 🔙', callback_data=back)]
    ]

    return InlineKeyboardMarkup(keyboard)
