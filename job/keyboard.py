from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def vacancies_keyboard(vacancies):
    keyboard = []

    for vacancy in vacancies:
        mark = vacancy.get('status', None) == 'Просмотрен'
        keyboard.append([InlineKeyboardButton(f"{vacancy.get('title', '')[:35]} - {vacancy.get('company')} {'✅' if mark else '❌'}",
                                              callback_data=f"vacancy_{vacancy.get('id')}")])

    return InlineKeyboardMarkup(keyboard)

def vacancies_list(url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Перейти к вакансии', url=url),],
        [InlineKeyboardButton('Назад в список вакансий', callback_data='vacancies_list')]
    ])