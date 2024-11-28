from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from job.keyboard import vacancies_keyboard, vacancies_list
from job.parser.dev import DevKG
from job.parser.hh import HhParser

SEARCH_VACANCY = 0


async def vacancy_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text='Напишите какую вакансию вы ищете'
    )
    return SEARCH_VACANCY


async def search_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.bot_data.get('job')
    vacancy = update.message.text

    await update.message.reply_text(
        text='Вакансии в поиске'
    )

    dev_kg = DevKG()
    hh = HhParser()
    dev_kg_vacancies: list = dev_kg.search_vacancies(vacancy.lower())
    hh_vacancies: list = hh.search_vacancies(vacancy.lower())

    keyboard = []

    for vacancy in dev_kg_vacancies + hh_vacancies:
        obj, is_create = job.get_or_create(
            title=vacancy.get('title'),
            company=vacancy.get('company'),
            link=vacancy.get('link'),
            salary=vacancy.get('salary'),
            job_type=vacancy.get('job_type'),
        )

        if is_create:
            keyboard.append([InlineKeyboardButton(
                f"{obj.get('title', '')[:35]} - {obj.get('company')}",
                callback_data=f"vacancy_{obj.get('id')}")])


    await update.message.reply_text(
        text="Вот новые вакансии по этой теме",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def vacancies_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job = context.bot_data.get('job')
    vacancies = job.all()
    if update.message:
        await update.message.reply_text(
                text="Список вакансий",
                reply_markup=vacancies_keyboard(vacancies)
            )
    else:
        await update.callback_query.message.reply_text(
            text="Список вакансий",
            reply_markup=vacancies_keyboard(vacancies)
        )

async def vacancy_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job = context.bot_data.get('job')
    id = update.callback_query.data.split('_')[-1]
    vacancy = job.get(id=id)
    if vacancy:
        await update.callback_query.message.reply_text(
            text=f"Название: {vacancy.get('title')}\n"
                 f"Компания:  {vacancy.get('company')}\n"
                 f"Зарплата:  {vacancy.get('salary')}\n",
            reply_markup=vacancies_list(vacancy.get('link'))
        )



