import logging

from telegram.ext import filters, CallbackQueryHandler
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler

from core.database import SqliteDB
from core.settings import BOT_TOKEN
from job.handlers import vacancies_list_handler, vacancy_detail, vacancy_name, search_vacancies, SEARCH_VACANCY
from job.manager import JobManager
from task.handlers import start, scheduler, specific_date_task, TASK_DATE, task_for_date, add_task, task_name, \
    TASK_NAME, TASK_DESCRIPTION, choice_time, task_description, EXECUTION_TIME, HOURS_AND_MINUTES, execution_time, \
    hours_and_minutes, skip_time, tasks_list, today_tasks, week_tasks, month_tasks, all_tasks, task_info, task_done, \
    delete_task, task_not_completed
from task.manager import TaskManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    database = SqliteDB()
    task_manager = TaskManager(database)
    job_manager = JobManager(database)

    application.bot_data.update(task=task_manager, job=job_manager)

    scheduler.start()

    task_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(specific_date_task, 'specific_date')],
        states={
            TASK_DATE: [MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), task_for_date)]
        },
        fallbacks=[MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), task_for_date)]
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Добавить задачу'), callback=add_task)],
        states={
            TASK_NAME: [MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), task_name)],
            TASK_DESCRIPTION: [
                MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), task_description),
                CommandHandler('skip', choice_time),
            ],
            EXECUTION_TIME: [CallbackQueryHandler(execution_time), ],
            HOURS_AND_MINUTES: [MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), hours_and_minutes)],
        },
        fallbacks=[
            CommandHandler('cancel', start),
            CommandHandler('skip_time', skip_time),
        ],
    )

    job_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Поиск вакансий'), callback=vacancy_name)],
        states={
            SEARCH_VACANCY: [MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), search_vacancies)]
        },
        fallbacks=[MessageHandler(filters.TEXT & (~filters.Regex(r'^/')), search_vacancies)]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Regex('Посмотреть список задач'), callback=tasks_list))
    application.add_handler(CallbackQueryHandler(tasks_list, 'tasks_list'))
    application.add_handler(CallbackQueryHandler(today_tasks, 'today'))
    application.add_handler(CallbackQueryHandler(week_tasks, 'week'))
    application.add_handler(CallbackQueryHandler(month_tasks, 'month'))
    application.add_handler(CallbackQueryHandler(all_tasks, 'all_time'))
    application.add_handler(CallbackQueryHandler(task_info, 'task_'))
    application.add_handler(CallbackQueryHandler(task_done, 'done_'))
    application.add_handler(CallbackQueryHandler(delete_task, 'delete_'))
    application.add_handler(CallbackQueryHandler(task_not_completed, 'not_completed_'))

    application.add_handler(CallbackQueryHandler(vacancies_list_handler, 'vacancies_list'))
    application.add_handler(CallbackQueryHandler(vacancy_detail, 'vacancy_'))

    application.add_handler(conv_handler)
    application.add_handler(task_conv_handler)
    application.add_handler(job_conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
