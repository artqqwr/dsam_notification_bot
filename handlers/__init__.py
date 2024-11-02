from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

import config
from handlers import buttons, commands, scheduled, states_processing
from handlers.states_processing import ProcessingStates


def register(app: Application):
    app.add_handlers([
        CommandHandler('start', commands.start),
        CommandHandler('help', commands.help),
        CommandHandler('admin', commands.admin),
        CommandHandler('event_example', commands.event_example),
        CommandHandler('cancel', commands.cancel),
        CommandHandler('stat', commands.stat),
    ])

    app.add_handlers([
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
        MessageHandler(filters.PHOTO | filters.VIDEO |
                       filters.Document.ALL, states_processing.add_files),

        CallbackQueryHandler(buttons.handle_inline),
    ])

    if config.IS_DEBUG:
        app.job_queue.run_repeating(
            scheduled.delete_lost_notifications, interval=timedelta(minutes=2))
        app.job_queue.run_repeating(
            scheduled.delete_expired_keys, interval=timedelta(minutes=30))
    else:
        app.job_queue.run_daily(scheduled.delete_lost_notifications, time=datetime.strptime(
            config.DELETE_LOST_NOTIFICATIONS_TIME, '%H:%M'))
        app.job_queue.run_daily(scheduled.delete_expired_keys, time=datetime.strptime(
            config.DELETE_EXPIRED_KEYS_TIME, '%H:%M', '%H:%M'))
    
    app.job_queue.run_repeating(scheduled.add_notifications_to_job_queue, interval=timedelta(days=1))


async def handle_text(update: Update, context: CallbackContext):
    states = {
        ProcessingStates.SELECT_EVENT: states_processing.select_event,
        ProcessingStates.ADD_EVENT: states_processing.add_event,
        ProcessingStates.SET_NOTIFICATIONS_DATETIME: states_processing.set_notification_datetime,
    }

    if not 'state' in context.user_data:
        context.user_data['state'] = None

    handle_state = states.get(context.user_data['state'])
    if handle_state:
        await handle_state(update, context)
    else:
        await buttons.hanlde_reply(update, context)
