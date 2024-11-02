import os
from datetime import datetime

import peewee
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

import config
import models
from handlers import services
from handlers.services import EVENT_EXAMPLE
from template import render
from ui import buttons


class ProcessingStates:
    SELECT_EVENT = 1
    ADD_EVENT = 2
    ADD_FILES = 3
    SET_NOTIFICATIONS_DATETIME = 4


async def set_notification_datetime(update: Update, context: CallbackContext):
    text = update.message.text
    notification: models.Notification = context.user_data.get(
        'notification')
    if not notification:
        return await update.message.reply_text('Уведомление не найдено')

    format = '%H:%M'
    try:
        if context.user_data['notification'].type == models.NotificationTypes.CUSTOM:
            format = '%d.%m.%Y ' + format
        dt = datetime.strptime(text, format)
        
        if notification.date:
            notification.date = notification.date.replace(hour=dt.hour, minute=dt.minute)
        else:
            notification.date = dt

        notification.save()

        async def job(callback):
            await services.send_event_for_all(context.bot, notification.event, context)
            n = models.Notification.get_or_none(notification.id)
            if n:
                n.delete_instance()

        job_name = str(notification.id) + str(notification.event.id)
        context.job_queue.run_once(job, notification.date, name=job_name)

        await update.message.reply_text('Сохранено')
        context.user_data['notification'] = None
        context.user_data['state'] = None

    except ValueError:
        return await update.message.reply_text(f'Напиши время в формате "HH:MM", а не "{text}"')
    except peewee.IntegrityError:
        return await update.message.reply_text(f'Такое уведомление уже есть')


async def select_event(update: Update, context: CallbackContext):
    text = update.message.text
    data = text.split(' ')
    for id_str in data:
        try:
            id = int(id_str)
            event: models.Event = list(models.Event)[id-1]

            kb = [
                [buttons.inline_delete_event(event.id)],
                [buttons.inline_add_event_files(event.id)],
                [buttons.inline_get_event_notifications_menu(event.id)]
            ]

            event.date = event.date.strftime(config.DATE_FORMAT)

            message = await update.message.reply_text(render('event', event=event), reply_markup=InlineKeyboardMarkup(kb))
            
            services.set_last_message(context, message)

            context.user_data['state'] = None
        except IndexError:
            await update.message.reply_text(f'"{id_str}" нет в списке!')
            break
        except ValueError:
            await update.message.reply_text(f'Введите ID мероприятия, а не "{id_str}!"')
            break


async def add_event(update: Update, context: CallbackContext):
    text = escape_markdown(update.message.text)
    data = text.strip().split('\n')

    if len(data) <= 1:
        return await update.message.reply_text(render(
            'incorrect_event_data', event=EVENT_EXAMPLE, event_template=render('event_template')
        ))
    try:
        date = datetime.strptime(data[0], config.DATE_FORMAT)
    except ValueError:
        return await update.message.reply_text(render(
            'incorrect_event_data', event=EVENT_EXAMPLE, event_template=render('event_template')
        ))

    name = data[1]
    text = '\n'.join(data[2:])

    event: models.Event = models.Event.create(
        name=name,
        text=text,
        date=date,
    )

    kb = [
        [buttons.inline_delete_event(event.id)],
        [buttons.inline_add_event_files(event.id)],
        [buttons.inline_get_event_notifications_menu(event.id)]
    ]

    message = await update.message.reply_text('Мероприятие добавлено!', reply_markup=InlineKeyboardMarkup(kb))
    
    services.set_last_message(context, message)

    context.user_data['state'] = None


async def add_files(update: Update, context: CallbackContext):
    event_id = context.user_data['current_event']
    if not event_id:
        return

    telegram_files = {
        'photo': update.message.photo,
        'video': update.message.video,
        'document': update.message.document,
    }

    type = ''
    for file_type, tg_file in telegram_files.items():
        if tg_file:
            type = file_type
            telegram_file = tg_file

    telegram_file = telegram_file[-1] if type == 'photo' else telegram_file
    event: models.Event = models.Event.get_by_id(event_id)

    if not telegram_file:
        return await update.message.reply_text('')

    file_info = await update.get_bot().get_file(telegram_file.file_id)

    event_dir_path = os.path.join(
        config.UPLOADS_PATH, type, str(event.get_id()))
    os.makedirs(event_dir_path, exist_ok=True)

    src = os.path.join(
        event_dir_path, f'{telegram_file.file_id}.{file_info.file_path.split(".")[-1]}')

    await file_info.download_to_drive(src)
    models.File.create(event=event, src=src, type=type)
    files_count = event.files.select().count()

    await update.message.reply_text(f'{files_count} файл(-ов) сохраненено для меропиятия "{event.name}"')
